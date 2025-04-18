from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Dict, Any
from database import get_db, create_tables
from models import TronAddressInfo
from tron_service import get_address_info, validate_tron_address
from cachetools import TTLCache
import logging
from requests.exceptions import HTTPError, ConnectionError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Tron Address Info API",
    description="API для получения информации об адресах Tron с кэшированием, логированием и повторными попытками.",
    version="1.0.0"
)

# Кэш для хранения результатов запросов (100 элементов, TTL 5 минут)
cache = TTLCache(maxsize=100, ttl=300)

# Pydantic модель для валидации входных данных
class AddressRequest(BaseModel):
    address: str

@app.on_event("startup")
async def on_startup():
    """Создаёт таблицы в базе данных при запуске приложения."""
    await create_tables()

@app.post(
    "/address_info",
    response_model=Dict[str, Any],
    summary="Получить информацию об адресе Tron",
    responses={
        200: {"description": "Информация об адресе успешно получена"},
        400: {"description": "Некорректный адрес Tron"},
        500: {"description": "Внутренняя ошибка сервера (например, проблемы с сетью или API TronGrid)"}
    }
)
async def get_address_info_endpoint(request: AddressRequest, db: AsyncSession = Depends(get_db)):
    """
    Получает информацию о bandwidth, energy и balance для указанного адреса Tron.
    Сохраняет данные в базу и использует кэш для оптимизации.
    Args:
        request: Pydantic модель с адресом Tron.
        db: Асинхронная сессия базы данных.
    Returns:
        Dict[str, Any]: Информация об адресе (address, bandwidth, energy, balance).
    Raises:
        HTTPException: При невалидном адресе или ошибке сервера.
    """
    address = request.address
    if not await validate_tron_address(address):
        raise HTTPException(status_code=400, detail="Invalid Tron address")
    try:
        # Проверяем кэш
        if address in cache:
            logger.info(f"Cache hit for address: {address}")
            info = cache[address]
        else:
            info = await get_address_info(address)
            cache[address] = info
            logger.info(f"Cache updated for address: {address}")

        # Сохраняем в базу
        db_entry = TronAddressInfo(
            address=address,
            bandwidth=info["bandwidth"],
            energy=info["energy"],
            balance=info["balance"]
        )
        db.add(db_entry)
        await db.commit()
        await db.refresh(db_entry)
        return {
            "address": address,
            "bandwidth": info["bandwidth"],
            "energy": info["energy"],
            "balance": info["balance"]
        }
    except (ConnectionError, HTTPError) as e:
        logger.error(f"Network error for address {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing address {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get(
    "/recent_requests",
    summary="Получить список последних запросов",
    responses={
        200: {"description": "Список последних запросов успешно получен"},
        500: {"description": "Внутренняя ошибка сервера при обращении к базе данных"}
    }
)
async def get_recent_requests(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Возвращает список последних запросов с пагинацией.
    Запросы сортируются по времени создания (от новых к старым).
    Args:
        page: Номер страницы (начинается с 1).
        page_size: Количество записей на странице (1-100).
        db: Асинхронная сессия базы данных.
    Returns:
        Dict[str, Any]: Словарь с total, page, page_size и списком записей.
    Raises:
        HTTPException: При ошибке сервера.
    """
    try:
        # Подсчёт общего количества записей
        total_query = await db.execute(select(func.count()).select_from(select(TronAddressInfo).subquery()))
        total = total_query.scalar()

        # Получение записей с пагинацией
        results = (
            await db.execute(
                select(TronAddressInfo)
                .order_by(TronAddressInfo.timestamp.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        logger.info(f"Retrieved recent requests: page={page}, page_size={page_size}")
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": [
                {
                    "id": item.id,
                    "address": item.address,
                    "bandwidth": item.bandwidth,
                    "energy": item.energy,
                    "balance": item.balance,
                    "timestamp": item.timestamp.isoformat()
                } for item in results
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving recent requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")