# Farm-to-Market Marketplace (Admin MVP)

Admin-only MVP for a Farm-to-Market web platform using:
- `Flask` backend (app factory + admin blueprint)
- `MongoDB` database
- `HTML + Tailwind CSS + Vanilla JS` frontend

This build focuses only on the Admin view and provides secure login, data monitoring, moderation workflows, transaction supervision, and analytics.

## Features (Admin)
- Admin authentication (single super admin)
- Dashboard KPIs + recent activity logs
- User management (filter + activate/inactive/suspend)
- Product moderation (approve/reject/hide + review notes)
- Order lifecycle monitoring with transition validation
- Transaction monitoring (payment state + review state)
- Analytics graphs (sales trend, order trend, user growth, category activity)
- Audit trail for sensitive admin actions

## Tech Stack
- Backend: `Flask`, `Flask-WTF`, `PyMongo`
- Database: `MongoDB`
- Frontend: `Jinja templates`, `Vanilla JS`, `Tailwind`
- Tests: `pytest`, `mongomock`

## Project Structure
```text
app/
  admin/
    decorators.py
    dependencies.py
    forms.py
    routes.py
  repositories/
  services/
  static/
    css/
    js/
  templates/
    admin/
  utils/
  __init__.py
run.py
requirements.txt
tailwind.config.js
package.json
tests/
  integration/
  unit/
```

## Quick Start
### 1) Create environment and install Python deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
```bash
cp .env.example .env
```
Edit `.env` if needed.
Use your Atlas connection string as:
```bash
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority
DATABASE_NAME=farm_to_market
```

### 3) Create admin user
```bash
flask --app run.py init-db
flask --app run.py seed-admin --email admin@example.com
```
You will be prompted for password.

### 4) (Optional) Seed realistic demo data for dashboards/charts
```bash
flask --app run.py seed-demo-data --reset
```
You can customize volume:
```bash
flask --app run.py seed-demo-data --reset --users 120 --products 200 --orders 400 --activity-logs 200
```

### 5) Run app
```bash
flask --app run.py run
```
Open `http://127.0.0.1:5000/admin/login`.

## Tailwind Setup
This project includes Tailwind CLI config.

Install frontend dependencies:
```bash
npm install
```

Build CSS:
```bash
npm run build:css
```

Watch mode:
```bash
npm run watch:css
```

## Admin Routes
### Pages
- `/admin/login`
- `/admin/dashboard`
- `/admin/users`
- `/admin/products`
- `/admin/orders`
- `/admin/transactions`
- `/admin/analytics`

### APIs
- `GET /admin/api/dashboard/kpis`
- `GET /admin/api/users`
- `PATCH /admin/api/users/<id>/status`
- `GET /admin/api/products`
- `PATCH /admin/api/products/<id>/review`
- `GET /admin/api/orders`
- `PATCH /admin/api/orders/<id>/status`
- `GET /admin/api/transactions`
- `PATCH /admin/api/transactions/<id>/state`
- `GET /admin/api/analytics/sales?range=7d|30d|90d`
- `GET /admin/api/analytics/orders?range=7d|30d|90d`
- `GET /admin/api/analytics/overview?range=7d|30d|90d`

## Database Collections and Indexes
Collections:
- `admin_users`
- `users`
- `products`
- `orders`
- `transactions`
- `admin_activity_logs`

Configured indexes:
- `admin_users.email` (unique)
- `users.role + users.status`
- `products.status + products.category + products.created_at`
- `orders.status + orders.created_at`
- `transactions.payment_status + transactions.created_at`

Schema setup command:
- `flask --app run.py init-db`
- Optional (if validator permissions are restricted): `flask --app run.py init-db --skip-validators`

## Testing
Run full suite:
```bash
pytest -q
```

Current status: `15 passed`.
