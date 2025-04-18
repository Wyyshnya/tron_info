from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

# Модель для хранения информации об адресах Tron
class TronAddressInfo(Base):
    __tablename__ = 'tron_address_info'
    # Уникальный идентификатор записи
    id = Column(Integer, primary_key=True)
    # Адрес кошелька Tron
    address = Column(String, nullable=False)
    # Доступная пропускная способность (bandwidth)
    bandwidth = Column(Integer)
    # Доступная энергия (energy)
    energy = Column(Integer)
    # Баланс в TRX
    balance = Column(Float)
    # Время создания записи
    timestamp = Column(DateTime, default=datetime.utcnow)