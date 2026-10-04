# Чеклист для следующей модели (с токенами)

## Приоритет 1 — MVP

1. **OrderServiceImpl** (`backend/services/order_service_impl.py`)
   - upsert user по telegram_id
   - create_order с Payment(pending)
   - list_user_orders, get_order с join lab/language
   - change_status + order_status_history + can_transition
   - submit_receipt → awaiting_review + enqueue admin notify

2. **API routes**
   - `GET /users/{telegram_id}/orders`
   - `POST /orders/{id}/attachments` (multipart)
   - `POST /orders/{id}/receipt`
   - `POST /orders/{id}/submit`

3. **User bot FSM**
   - choose_lab → choose_language (skip if one)
   - attach_materials: document/photo handlers
   - GitHub URL validation (`config/file_rules.GITHUB_URL_PREFIXES`)
   - confirm → create_order → payment instructions
   - awaiting_receipt state

4. **Admin bot**
   - `/orders [status]` list
   - callback pay_ok / pay_no → API
   - status keyboard
   - send receipt photo to admin

5. **Worker**
   - реальный `Bot(token=...).send_message` в tasks
   - enqueue из NotificationService через arq pool

## Приоритет 2

- Alembic: `alembic init`, autogenerate from models
- Rate limit middleware (Redis INCR)
- Webhook setup для prod
- Integration tests (pytest + testcontainers)

## Приоритет 3

- S3 storage backend
- Multiple admins
- Auto Kaspi (если API появится)

## Тестовый сценарий (E2E)

1. User: /start → Новый заказ → ADS → Lab 1 → C++ → attach .cpp → GitHub URL → создать
2. User: отправить PNG чек
3. Admin: получить уведомление → ✅ Подтвердить
4. User: «✅ Оплата подтверждена»
5. Admin: 🔵 В работе → ✅ Готово
6. User: «✅ Заказ завершён»
