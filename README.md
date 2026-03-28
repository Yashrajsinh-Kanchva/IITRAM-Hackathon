# Farm-to-Market Marketplace (Admin + Buyer + Farmer)

Integrated Farm-to-Market platform using:
- `Flask` backend (app factory + blueprints)
- `MongoDB` database
- `HTML + Tailwind CSS + Vanilla JS` frontend

This build now contains all modules on the same database (`farm_to_market`):
- Admin panel (moderation, monitoring, analytics, AI insights)
- Buyer module (signup/login, marketplace, cart, negotiations, wishlist, orders)
- Farmer portal (profile setup, product listing, negotiation handling, dashboard)

## Features (Admin)
- Admin authentication (single super admin)
- Dashboard KPIs + recent activity logs
- User management (filter + activate/inactive/suspend)
- Product moderation (approve/reject/hide + review notes)
- Order lifecycle monitoring with transition validation
- Transaction monitoring (payment state + review state)
- Analytics graphs (sales trend, order trend, user growth, category activity)
- Audit trail for sensitive admin actions

## Features (Buyer)
- Buyer signup/login APIs
- Buyer storefront pages (marketplace, cart, orders, wishlist, profile, map)
- Negotiation flow (submit/update/reject)
- Cart management and checkout/order placement
- Buyer order placement mirrors into core `orders` and `transactions` for admin visibility

## Features (Farmer)
- Farmer role selection + entry flow
- Farmer profile setup (location, crop types, payment details)
- Farmer product listing and live/pause/delete controls
- Farmer negotiation actions (accept/reject/counter) over buyer offers
- Farmer dashboard and advanced dashboard views

## Tech Stack
- Backend: `Flask`, `Flask-WTF`, `PyMongo`
- Database: `MongoDB`
- Frontend: Admin templates + Buyer static pages + Farmer templates/assets
- Tests: `pytest`, `mongomock`

## Project Structure
```text
app/
  admin/
  buyer/
    auth_routes.py
    products_routes.py
    cart_routes.py
    orders_routes.py
    negotiation_routes.py
    wishlist_routes.py
    web_routes.py
  farmer/
    portal_routes.py
  repositories/
  services/
  static/
    farmer/
  templates/
    admin/
    farmer/
    login_selector.html
  utils/
  __init__.py
frontend/
  buyer/
run.py
requirements.txt
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
Set:
```bash
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority
DATABASE_NAME=farm_to_market
```

### 3) Initialize DB and seed admin
```bash
flask --app run.py init-db
flask --app run.py seed-admin --email admin@example.com
```

### 4) Optional demo data
```bash
flask --app run.py seed-demo-data --reset
```

### 5) Run app
```bash
flask --app run.py run
```
Open:
- Role selector: `http://127.0.0.1:5000/login`
- Admin login: `http://127.0.0.1:5000/admin/login`
- Buyer login: `http://127.0.0.1:5000/buyer/login.html`
- Farmer portal: `http://127.0.0.1:5000/farmer`

## API Surface
### Admin APIs
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
- `GET /admin/api/analytics/forecast?horizon=1d|3d|7d`
- `GET /admin/api/analytics/crop-trends?horizon=1d|3d|7d`
- `POST /admin/api/analytics/refresh`
- `GET /admin/api/alerts`
- `PATCH /admin/api/alerts/<id>/resolve`
- `GET /admin/api/audit-logs`

### Buyer APIs
- `POST /api/signup`
- `POST /api/login`
- `GET /api/products`
- `GET /api/products/<id>`
- `GET /api/cart/<user_id>`
- `POST /api/cart/add`
- `POST /api/cart/remove`
- `POST /api/cart/update`
- `POST /api/orders/`
- `GET /api/orders/<user_id>`
- `POST /api/negotiate/submit`
- `GET /api/negotiate/<user_id>`
- `POST /api/negotiate/update/<neg_id>`
- `POST /api/negotiate/reject/<neg_id>`
- `GET /api/wishlist/<user_id>`
- `POST /api/wishlist/toggle`

### Farmer APIs + Pages
- `GET /farmer`
- `GET /farmer/entry`
- `POST /farmer/entry`
- `GET /farmer/profile-setup`
- `POST /farmer/profile-setup`
- `GET /farmer/dashboard`
- `GET /farmer/new-dashboard`
- `GET /farmer/add-product`
- `POST /farmer/add-product`
- `POST /farmer/product/<product_id>/toggle`
- `POST /farmer/product/<product_id>/delete`
- `POST /farmer/api/negotiate`
- `GET /api/farmer/<farmer_id>`
- `GET /farmer/logout`

## Collections
- `admin_users`, `users`, `products`, `orders`, `transactions`
- `offers`, `admin_activity_logs`, `admin_alerts`
- `ml_order_forecasts`, `ml_crop_trends`, `farmer_notifications`
- `farmers`
- `buyer_Cart`, `buyer_Orders`, `buyer_Negotiations`, `buyer_Wishlist`

## Testing
```bash
pytest -q
```
