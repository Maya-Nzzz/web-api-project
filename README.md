# Асинхронный Backend на Fast API

## Описание функций
- **REST API (CRUD)** для элементов (*items*) — в проекте это погодные записи по городу
- **WebSocket** `/ws/items` для **real-time** уведомлений (создание/обновление/удаление + события фоновой задачи + события NATS)
- **Фоновая задача** (scheduler): раз в N секунд ходит во внешний сервис через `httpx`, парсит ответ, сохраняет в БД
- **Ручной запуск** фоновой задачи: `POST /tasks/run`
- **NATS**: публикация событий и подписка на `items.updates`
- **Async DB**: SQLite через async SQLAlchemy (`aiosqlite`)


## Структура проекта

```
web-api-project/
├─ app/
│  ├─ api/
│  │  ├─ items.py          # CRUD для записей погоды
│  │  └─ tasks.py          # POST фоновый процесс
│  ├─ db/
│  │  └─ database.py       # engine, sessionmaker, Depends(get_session)
│  ├─ models/
│  │  └─ item.py           # описание таблицы для хранения данных о погоде
│  ├─ nats/
│  │  └─ client.py         # connect/publish/subscribe (items.updates)
│  ├─ services/
│  │  └─ weather.py        # получение данных с внешнего API
│  ├─ tasks/
│  │  └─ runner.py         # периодическая задача и ручной запуск
│  ├─ ws/
│  │  ├─ manager.py        # ConnectionManager (broadcast)
│  │  └─ router.py         # /ws/items
│  ├─ config.py            # настройки проекта
│  └─ main.py              
├─ scripts/
│  ├─ nats_subscriber.py   # пример: подписчик NATS
│  └─ nats_publisher.py    # пример: publisher в NATS
├─ docker-compose.yml      # поднятие NATS (docker)
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

## Значения по умолчанию

- `DATABASE_URL` — `sqlite+aiosqlite:///./app.db`
- `NATS_URL` — `nats://127.0.0.1:4222`
- `NATS_SUBJECT` — `items.updates`
- `BACKGROUND_PERIOD_SECONDS` — `300`

---

## Эндпоинты

- `GET /items` — список записей
- `GET /items/{id}` — запись по id
- `POST /items` — создать
- `PATCH /items/{id}` — частично обновить
- `DELETE /items/{id}` — удалит

---

## Запуск (Git Bash / Terminal)

### 1) Виртуальное окружение + зависимости
Терминал 1
```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### 2) Поднять NATS (Docker)
Терминал 2
```bash
docker compose up -d
docker compose ps
```

### 3) Запустить приложение (uvicorn)
Терминал 1
```bash
python -m uvicorn app.main:app --reload
```

### 4) Subscriber NATS
Терминал 3
```powershell
source venv/Scripts/activate
python scripts/nats_subscriber.py
```

### 5) Остановить NATS
Терминал 2
```bash
docker compose down
```

### 6) Остановить проект
Закрыть терминал 1, 3 либи Ctrl + C

---

- Swagger UI: `http://127.0.0.1:8000/docs`

---
