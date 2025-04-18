from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# URL базы данных из переменной окружения или SQLite по умолчанию
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tron_info.db")

# Создаём асинхронный движок для взаимодействия с базой данных
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Настраиваем фабрику асинхронных сессий для ORM
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Генератор асинхронной сессии для FastAPI зависимостей
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

# Асинхронное создание таблиц в базе данных при запуске приложения
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)