from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.exceptions import AddressNotFound
from typing import Dict, Any
import logging
import asyncio
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import HTTPError, ConnectionError

# Настройка логирования с кастомным форматом
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")

# Инициализация клиента Tron с API-ключом для авторизации запросов
client = Tron(provider=HTTPProvider("https://api.trongrid.io", api_key=TRONGRID_API_KEY))

@retry(
    stop=stop_after_attempt(3),  # Максимум 3 попытки
    wait=wait_exponential(multiplier=1, min=1, max=10),  # Экспоненциальная задержка
    retry=retry_if_exception_type((ConnectionError, HTTPError)),  # Повторять для сетевых ошибок
    before_sleep=lambda retry_state: logger.info(f"Retrying validate_tron_address: attempt {retry_state.attempt_number}")
)
async def validate_tron_address(address: str) -> bool:
    """
    Проверяет, является ли адрес Tron валидным.
    Args:
        address: Адрес Tron для проверки.
    Returns:
        bool: True, если адрес валиден, False в противном случае.
    """
    try:
        await asyncio.to_thread(client.get_account, address)
        return True
    except AddressNotFound:
        logger.warning(f"Invalid Tron address attempted: {address}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, HTTPError)),
    before_sleep=lambda retry_state: logger.info(f"Retrying get_address_info: attempt {retry_state.attempt_number}")
)
async def get_address_info(address: str) -> Dict[str, Any]:
    """
    Получает информацию об адресе Tron асинхронно.
    Args:
        address: Адрес Tron для получения информации.
    Returns:
        Dict[str, Any]: Словарь с bandwidth, energy и balance.
    Raises:
        ValueError: Если адрес невалиден.
        Exception: Если запрос к TronGrid не удался.
    """
    if not await validate_tron_address(address):
        raise ValueError("Invalid Tron address")
    try:
        resource = await asyncio.to_thread(client.get_account_resource, address)
        balance = await asyncio.to_thread(client.get_account_balance, address)
        bandwidth = resource.get('NetLimit', 0)
        energy = resource.get('EnergyLimit', 0)
        logger.info(f"Successfully retrieved info for address: {address}")
        return {
            "bandwidth": bandwidth,
            "energy": energy,
            "balance": balance
        }
    except Exception as e:
        logger.error(f"Failed to retrieve info for address {address}: {str(e)}")
        raise