# Farm-to-Market Admin: Project Structure and Features

This file describes the current project structure and implemented features for the Admin-side MVP.

## 1) Root Structure

- `run.py`: Flask entry point (`create_app()` bootstrap)
- `app/`: Main Flask application package
- `tests/`: Unit and integration tests
- `requirements.txt`: Python dependencies
- `package.json`, `tailwind.config.js`: Tailwind tooling
- `.env`, `.env.example`: Environment config
- `README.md`: Setup and usage notes

Note:
- Root-level `index.html`, `style.css`, `script.js` are standalone frontend files.
- Actual admin app UI is served from `app/templates` + `app/static`.

## 2) Application Layers (`app/`)

### 2.1 Core App
- `app/__init__.py`
  - App factory pattern
  - Loads env and config
  - Connects MongoDB
  - Ensures DB collections + indexes
  - Registers admin blueprint and CLI commands

- `app/config.py`
  - Development/testing/production configs
  - Mongo URI, DB name, session and CSRF settings

- `app/extensions.py`
  - Shared Flask extensions (`CSRFProtect`)

- `app/cli.py`
  - CLI commands:
    - `init-db`
    - `seed-admin`
    - `seed-demo-data`

### 2.2 Admin HTTP Layer
- `app/admin/routes.py`
  - Admin pages and JSON APIs
- `app/admin/decorators.py`
  - Admin auth guard (`admin_required`)
- `app/admin/forms.py`
  - Login form (Flask-WTF)
- `app/admin/dependencies.py`
  - Service/repository wiring per request

### 2.3 Repository Layer (Mongo data access)
- `app/repositories/admin_user_repository.py`
- `app/repositories/user_repository.py`
- `app/repositories/product_repository.py`
- `app/repositories/order_repository.py`
- `app/repositories/transaction_repository.py`
- `app/repositories/activity_log_repository.py`
- `app/repositories/admin_alert_repository.py`
- `app/repositories/schema.py` (collection validators)
- `app/repositories/indexes.py` (indexes)

### 2.4 Service Layer (business logic)
- `app/services/auth_service.py`
- `app/services/dashboard_service.py`
- `app/services/user_service.py`
- `app/services/product_service.py`
- `app/services/order_service.py`
- `app/services/transaction_service.py`
- `app/services/activity_log_service.py`
- `app/services/analytics_service.py`
  - includes anomaly detection
  - includes `compute_quality_score(product)`

### 2.5 Utilities
- `app/utils/auth.py`: session login/logout helpers
- `app/utils/pagination.py`: page parsing + metadata
- `app/utils/serialization.py`: ObjectId/document serialization
- `app/utils/time_utils.py`: UTC time helper
- `app/utils/validators.py`: allowed statuses/ranges/transitions

### 2.6 Frontend Templates and Assets
- `app/templates/base.html`: shared admin layout + sidebar nav
- `app/templates/admin/*.html`: page-specific templates
  - `login.html`
  - `dashboard.html`
  - `users.html`
  - `products.html`
  - `orders.html`
  - `transactions.html`
  - `analytics.html`
  - `audit_logs.html`
  - `error.html`
- `app/static/js/admin.js`: shared frontend helpers (`apiFetch`, toast, pagination, etc.)
- `app/static/css/styles.css`: compiled/admin CSS

## 3) Implemented Admin Features

### 3.1 Authentication
- Super-admin login/logout
- Session-based protection for admin routes
- CSRF protection on mutating requests

### 3.2 Dashboard
- KPI cards (users, products, orders, revenue proxy, failed txns)
- Recent admin activity table
- Smart anomaly strip
  - order spike
  - payment failure rate spike
  - user registration drop
  - product rejection spike
- Alert count badge in sidebar dashboard link

### 3.3 Users Module
- List/search/filter users by role/status
- Single-user status update
- Bulk actions:
  - activate
  - suspend
  - delete
- Select-all + floating action bar UI

### 3.4 Products Module
- List/search/filter products by status/category
- Product quality scoring (0-100)
- Quality summary cards (Excellent/Good/Poor)
- Quality filter (All/Excellent/Good/Poor)
- Single review update (approve/reject/hide + note)
- Bulk moderation actions:
  - approve
  - reject
  - hide
- Select-all + floating action bar UI

### 3.5 Orders Module
- List/search/filter orders
- Status updates with transition validation
- Table layout tuned to avoid control overlap

### 3.6 Transactions Module
- List/search/filter transactions
- Update payment/review states

### 3.7 Analytics Module
- Sales trend API and chart
- Orders trend API and chart
- Overview analytics (category activity + user growth)

### 3.8 Audit Trail Module
- Dedicated page: `/admin/audit-logs`
- Filter by admin email, action type, date range
- Expand row to view before/after details
- Highlight changed fields
- CSV export (client-side from current dataset)

## 4) API Surface (Admin)

### Auth/UI pages
- `GET /admin/login`
- `GET /admin/dashboard`
- `GET /admin/users`
- `GET /admin/products`
- `GET /admin/orders`
- `GET /admin/transactions`
- `GET /admin/analytics`
- `GET /admin/audit-logs`

### Core APIs
- `GET /admin/api/dashboard/kpis`
- `GET /admin/api/users`
- `PATCH /admin/api/users/<id>/status`
- `POST /admin/api/users/bulk-action`
- `GET /admin/api/products`
- `GET /admin/api/products/quality-summary`
- `PATCH /admin/api/products/<id>/review`
- `POST /admin/api/products/bulk-action`
- `GET /admin/api/orders`
- `PATCH /admin/api/orders/<id>/status`
- `GET /admin/api/transactions`
- `PATCH /admin/api/transactions/<id>/state`
- `GET /admin/api/analytics/sales?range=7d|30d|90d`
- `GET /admin/api/analytics/orders?range=7d|30d|90d`
- `GET /admin/api/analytics/overview?range=7d|30d|90d`
- `GET /admin/api/alerts`
- `PATCH /admin/api/alerts/<id>/resolve`
- `GET /admin/api/audit-logs`

## 5) Mongo Collections

- `admin_users`
- `users`
- `products`
- `orders`
- `transactions`
- `admin_activity_logs`
- `admin_alerts`

## 6) How Data/Flow Works

1. Route receives request in `app/admin/routes.py`
2. Route calls service from `get_services()`
3. Service applies business rules
4. Repository performs Mongo operations
5. Response returns JSON or rendered template
6. Frontend pages call API via `AdminApp.apiFetch()`

## 7) Testing

- Unit tests: service logic and validators
- Integration tests: auth protection + API update paths
- Current suite location:
  - `tests/unit/`
  - `tests/integration/`

## 8) Run Commands

- Initialize DB:
  - `flask --app run.py init-db`
- Seed admin user:
  - `flask --app run.py seed-admin --email admin@example.com`
- Seed demo data:
  - `flask --app run.py seed-demo-data --reset`
- Run server:
  - `flask --app run.py run --port 5001`

