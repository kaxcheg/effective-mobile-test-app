# effective-mobile-test-app

Мини-сервис на FastAPI + PostgreSQL с архитектурой DDD / Clean Architecture / Ports & Adapters / Dependency Inversion, реализующий аутентификацию через JWT и ролевую авторизацию.

---

## Установка и запуск (Docker Compose + Make)

Команды:

1. Клонирование репозитория:
   ```bash
   git clone https://github.com/kaxcheg/effective-mobile-test-app.git
   cd effective-mobile-test-app
   ```

2. (Опционально) подготовка переменных окружения:
   используйте `dev/.env` (создайте при необходимости на основе `dev/.env.example`)

3. Запуск приложения (БД + API):
   ```bash
   make build
   make up
   ```

4. Полезные команды:
   ```bash
   make logs     # просмотр логов приложения
   make restart  # перезапуск контейнеров
   make down     # остановка и удаление окружения
   make clean    # полная очистка от артефактов
   ```

Миграции создавать/применять вручную не нужно — они уже включены и выполняются автоматически при старте контейнера.

**Swagger UI:** http://localhost:8000/docs  
**Health check:** `GET /health`

---

## Аутентификация (middleware)

Механизм реализован через HTTP middleware, который проверяет JWT и помещает пользователя в `request.state.user`.

Поток запроса:

```
Client (JWT в Authorization: Bearer <token>)
  ↓
Auth Middleware
  ↓
JwtTokenService.verify(token)
  ↓
Извлекаем sub=user_id и sid=session_id
  ↓
Запрос в БД (UserSession по sid)
  ↓
Проверка sub == user_id из сессии
  ↓
Загрузка доменной сущности User → request.state.user
  ↓
Передача управления конечной точке
```

Особенности:
- При logout запись в `UserSessionORM` удаляется, токен становится невалидным.
- В `request.state.user` хранится доменная сущность `User`, не ORM.
- При ошибке — **401 Unauthorized**.

---

## Авторизация (ROLE_POLICIES)

Т.к. в ТЗ указано *"Таблицы в БД создавать не требуется."*, ролевая модель определена 
в `app/interface/http/auth/base.py` в словаре `ROLE_POLICIES`.

Механизм:
- Право задаётся в формате `<use_case(ресурс)>: <список_разрешённых_ролей>`.
- При несоответствии роли текущего пользователя политике возвращается **403 Forbidden**.

---

## Архитектура проекта

```
app/
  domain/              — Сущности, Value Objects, доменные правила и инварианты
  application/         — Use cases, DTO, оркестрация бизнес-логики
  infrastructure/      — Адаптеры: SQLAlchemy/Alembic, JWT, репозитории и сервисы
  interface/
    http/              — FastAPI: роуты, схемы, зависимости, middleware
deploy/
  bootstrap/           — Скрипты инициализации и загрузки данных
dev/
  docker-compose.yml   — Окружение для разработки
```

Принципы:
- **DIP** — зависимости направлены внутрь.  
- **Ports & Adapters** — use cases взаимодействуют только с абстрактными портами.  
- **Clean Architecture** — домен не зависит от фреймворков.  
- **DDD** — бизнес-логика сосредоточена в `domain/`.

---

## Ресурсы API

**Users:**
- `POST /users` — создать пользователя (админ)
- `GET /users/{id}` — получить профиль (сам/админ)
- `PATCH /users/{id}` — обновить (сам/админ)
- `DELETE /users/{id}` — деактивировать (админ)
- `POST /auth/login` / `POST /auth/logout` — управление сессиями (JWT + таблица сессий)

**Orders:**
- `GET /orders/{id}` — мок заказов для демонстрации схем авторизации

**Payments:**
- `GET /payments/{id}` — мок платежей для демонстрации схем авторизации

---

## Тестирование

Запуск тестов через Makefile:

```bash
make test-unit
```

Подход:
- Unit-тесты изолируют домен и use cases (с фейковыми портами).
