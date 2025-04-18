import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base
from models import TronAddressInfo
from sqlalchemy.future import select
from unittest.mock import patch
import asyncio

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Переопределение зависимости для тестовой базы данных
async def override_get_db():
    async with TestingSessionLocal() as db:
        yield db

app.dependency_overrides[get_db] = override_get_db

# Фикстура для создания и удаления таблиц
@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Инициализация тестового клиента
client = TestClient(app)

# Тест POST с валидным адресом
@patch('tron_service.get_address_info')
@pytest.mark.asyncio
async def test_post_address_info(mock_get_address_info):
    mock_get_address_info.return_value = {"bandwidth": 0, "energy": 0, "balance": "0.088946"}
    response = client.post("/address_info", json={"address": "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g"})
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g"
    assert data["bandwidth"] == 0
    assert data["energy"] == 0
    assert data["balance"] == "0.088946"

    # Проверка базы данных
    async with TestingSessionLocal() as db:
        entry = (await db.execute(
            select(TronAddressInfo).filter_by(address="TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g")
        )).scalars().first()
        assert entry is not None
        assert entry.bandwidth == 0

# Тест POST с невалидным адресом
@patch('tron_service.validate_tron_address', return_value=False)
@pytest.mark.asyncio
async def test_post_invalid_address(mock_validate):
    response = client.post("/address_info", json={"address": "invalid_address"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Tron address"

# Тест GET с пагинацией
@pytest.mark.asyncio
async def test_get_recent_requests():
    async with TestingSessionLocal() as db:
        for i in range(15):
            db.add(TronAddressInfo(
                address=f"test_{i}",
                bandwidth=1000 + i,
                energy=5000 + i,
                balance=100.0 + i
            ))
        await db.commit()

    response = client.get("/recent_requests?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 16
    assert len(data["data"]) == 10

    response = client.get("/recent_requests?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 6

# Тест обработки сетевой ошибки
@patch('tron_service.get_address_info')
@pytest.mark.asyncio
async def test_post_network_error(mock_get_address_info):
    from requests.exceptions import ConnectionError
    mock_get_address_info.side_effect = ConnectionError("Network error")
    response = client.post("/address_info", json={"address": "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g"})
    assert response.status_code == 500
    assert "Network error" in response.json()["detail"]