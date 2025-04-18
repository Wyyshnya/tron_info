# Микросервис для получения информации об адресах Tron

## Описание

Микросервис предоставляет REST API для получения информации об адресах в сети Tron, включая пропускную способность (bandwidth), энергию (energy) и баланс в TRX. Данные сохраняются в базу данных, а запросы оптимизированы с помощью кэширования. Сервис включает два эндпоинта:
- **POST /address_info**: Получение информации об адресе Tron и сохранение в базу.
- **GET /recent_requests**: Получение списка последних запросов с пагинацией.

Микросервис построен с использованием современных технологий:
- **FastAPI** для асинхронного REST API.
- **SQLAlchemy** с асинхронным драйвером `aiosqlite` для базы данных.
- **Tronpy** для взаимодействия с TronGrid API.
- **Tenacity** для повторных попыток при сетевых ошибках.
- **TTLCache** для кэширования запросов.
- Полное логирование, валидация адресов, документация Swagger и тесты с `pytest`.

## Функциональность

### Эндпоинты
1. **POST /address_info**:
   - **Входные данные**: JSON с полем `address` (адрес Tron).
   - **Функция**: Запрашивает данные (bandwidth, energy, balance) через TronGrid, сохраняет их в базу и возвращает результат.
   - **Особенности**:
     - Проверка валидности адреса.
     - Кэширование для повторных запросов (TTL 5 минут).
     - Повторные попытки при сетевых ошибках.
   - **Пример ответа**:
     ```json
     {
         "address": "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g",
         "bandwidth": 1000,
         "energy": 5000,
         "balance": 100.0
     }
     ```

2. **GET /recent_requests**:
   - **Параметры**: `page` (номер страницы, от 1), `page_size` (размер страницы, 1-100).
   - **Функция**: Возвращает список последних запросов, отсортированных по времени (от новых к старым).
   - **Пример ответа**:
     ```json
     {
         "total": 15,
         "page": 1,
         "page_size": 10,
         "data": [
             {
                 "id": 1,
                 "address": "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g",
                 "bandwidth": 1000,
                 "energy": 5000,
                 "balance": 100.0,
                 "timestamp": "2025-04-18T11:35:11.705Z"
             },
             ...
         ]
     }
     ```

### Особенности
- **Асинхронность**: Полная асинхронная обработка (эндпоинты, база данных, вызовы Tronpy через `asyncio.to_thread`).
- **Логирование**: Логируются запросы, ошибки, кэш-хиты и ретрай-попытки.
- **Кэширование**: Ускоряет повторные запросы к одним и тем же адресам.
- **Обработка ошибок**: Валидация адресов, повторные попытки для сетевых ошибок, информативные HTTP-ошибки.
- **Тестирование**: Интеграционные и юнит-тесты с `pytest`, включая проверку сетевых ошибок.
- **Документация**: Swagger UI (`/docs`) с описанием эндпоинтов и ошибок.

## Требования

- **Python**: 3.8 или выше.
- **Docker**: Для запуска через Docker Compose.
- **API-ключ TronGrid**: Получите на [TronGrid](https://www.trongrid.io/).
- **Зависимости** (см. `requirements.txt`):
  - fastapi
  - uvicorn
  - sqlalchemy
  - aiosqlite
  - tronpy
  - pytest
  - pytest-asyncio
  - python-dotenv
  - tenacity
  - cachetools

## Установка и запуск (локально)

1. **Клонируйте репозиторий**:
   ```bash
   git clone <repository_url>
   cd tron_info_service

2. **Создайте виртуальное окружение и установите зависимости**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Для Windows: .venv\Scripts\activate
    pip install -r requirements.txt

3. **Создайте файл .env в корне проекта** (не обязательно):
    ```plaintext
    DATABASE_URL=sqlite+aiosqlite:///./tron_info.db
    TRONGRID_API_KEY=your_trongrid_api_key_here

Замените your_trongrid_api_key_here на ваш API-ключ TronGrid.

4. **Запустите приложение**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Откройте документацию API:
Swagger: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

## Установка и запуск (через Docker Compose)
1. **Убедитесь, что Docker и Docker Compose установлены**:
    ```bash
    docker --version
    docker-compose --version

2. **Создайте файл .env (см. выше).**

3. **Запустите приложение:**
   ```bash
    docker-compose up --build -d

4. **Проверьте документацию API:**
   Swagger: http://127.0.0.1:8000/docs

5. **Остановите приложение:**
   ```bash
    docker-compose down

## Примеры запросов
1. **POST /address_info:**
    ```bash
    curl -X POST "http://127.0.0.1:8000/address_info" \
         -H "Content-Type: application/json" \
         -d '{"address": "TFjnjGvy8GLP63CDkX2eWQBYHRUzvN619g"}'

2. **GET /recent_requests:**
    ```bash
    curl "http://127.0.0.1:8000/recent_requests?page=1&page_size=10"

## Тестирование
1. **Установите зависимости для тестов (если ещё не установлены):**
    ```bash
    pip install pytest pytest-asyncio

2. **Запустите тесты:**
    ```bash
    pytest tests/ --asyncio-mode=auto

### Покрытие тестами:
POST-запросы с валидными и невалидными адресами.

GET-запросы с пагинацией.

Обработка сетевых ошибок.

Проверка записи и чтения данных из базы.

### Замечания
API-ключ TronGrid: Без действительного ключа запросы могут возвращать ошибку 401 Unauthorized. Получите ключ на TronGrid и добавьте в .env.

Сетевые ошибки: Если возникают ошибки типа Max retries exceeded, проверьте интернет-соединение или настройки прокси. Механизм tenacity делает до 3 попыток при сбоях.

SQLite: Используется для простоты. Для продакшена рекомендуется PostgreSQL с драйвером asyncpg. (SQLite не имеет асинхронности на уровне драйвера)

Tronpy: Библиотека синхронная, но вызовы обёрнуты в asyncio.to_thread для совместимости с асинхронным кодом.

