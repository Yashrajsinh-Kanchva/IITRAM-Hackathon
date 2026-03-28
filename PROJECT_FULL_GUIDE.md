# Krishi Connect (Farm-to-Market) - Full Project Guide

This document covers the complete project in one place: what is built, what technologies are used, key features, architecture, API surface, database collections, and how to run/test.

## 1) Project Summary

Krishi Connect is a multi-role agricultural marketplace built on a single Flask + MongoDB backend.

It includes:
- Admin module (`/admin/*`) for moderation, monitoring, analytics, and audits
- Buyer module (`/buyer/*` + `/api/*`) for shopping, negotiations, wishlist, cart, and orders
- Farmer module (`/farmer/*`) for profile setup, product listing, and negotiation response
- Offer + Market Intelligence services for pricing/offer workflows and AI-like trends/forecasting

All modules are connected to the same MongoDB database:
- `DATABASE_NAME=farm_to_market`

## 2) What Is Used (Tech Stack)

### Backend
- Python 3
- Flask 3.1.1
- Flask-WTF 1.2.1 (forms + CSRF)
- PyMongo 4.10.1 (MongoDB access)
- python-dotenv 1.0.1 (env loading)

### Data / AI / External
- MongoDB (Atlas/local)
- scikit-learn 1.6.1 (RandomForest-based forecasting flow)
- Open-Meteo API (weather signal input for insights)

### Frontend
- Admin: Jinja templates + Tailwind CSS + Vanilla JS
- Buyer: static HTML/CSS/JS served via Flask at `/buyer/*`
- Farmer: Jinja templates + dedicated farmer static assets

### Build & Tooling
- Tailwind CLI (`tailwindcss`) via `package.json`
- Pytest + Mongomock for tests

## 3) High-Level Architecture

### App Factory
- `app/__init__.py`
  - Loads config and env
  - Connects MongoDB
  - Ensures collection validators + indexes
  - Registers blueprints
  - Centralized error handling for HTML/JSON paths

### Layering Pattern
- Routes: HTTP handling + request/response
- Services: business rules + validations
- Repositories: Mongo queries and persistence
- Utils: auth, time, serialization, pagination, validators

## 4) Directory Overview

```text
app/
  admin/            # Admin routes/forms/decorators/dependency wiring
  buyer/            # Buyer APIs + buyer static-file serving blueprint
  farmer/           # Farmer APIs/pages (portal + notifications)
  offers/           # Offer API endpoints
  repositories/     # DB schema/index/repository access classes
  services/         # Business logic (auth, analytics, orders, offers, AI insights, etc.)
  static/           # Admin static + farmer static
  templates/        # Admin/farmer/login selector templates
  utils/            # Shared helper functions
frontend/
  buyer/            # Buyer HTML/CSS/JS + local image placeholders
tests/
  unit/
  integration/
```

## 5) Feature Coverage

### 5.1 Unified Entry
- `/login` role selection page
- Role-based navigation for Admin, Buyer, Farmer

### 5.2 Admin Features
- Admin login/logout (session based)
- Dashboard KPIs + anomaly alerts + recent activity
- User management (filters, status update, bulk action)
- Product moderation (approve/reject/hide + quality insights)
- Order lifecycle control with transition checks
- Transaction monitoring (payment/review states)
- Analytics:
  - sales/orders/overview charts
  - 3D data endpoint
  - forecast endpoints (1d/3d/7d)
  - crop trend endpoints (1d/3d/7d)
- Audit logs with filters

### 5.3 Buyer Features
- Buyer signup/login APIs
- Marketplace listing with:
  - search
  - crop/location/price/quantity/sort filters
  - negotiation modal
  - wishlist toggle
- Cart add/remove/update
- Checkout and order placement
- Buyer orders page
- Buyer negotiations page (counter/reject flows)
- Buyer wishlist page
- Product detail page + map page
- Local image fallback support for robust product image rendering

### 5.4 Farmer Features
- Farmer role/entry flow
- Farmer profile setup (location, crop types, banking/payment details)
- Farmer dashboard + new dashboard view
- Add product (with optional image upload to `app/static/farmer/uploads`)
- Product live toggle + delete
- Negotiation action API (accept/reject/counter)
- Farmer logout
- Farmer public info endpoint
- Farmer notification APIs (`/farmer/api/notifications*`)

### 5.5 Offer Engine
- Create offer
- Respond to offer
- List offers with pagination/status handling

### 5.6 Market Intelligence (AI/ML)
- Order forecast generation for 1d/3d/7d horizons
- Crop trend scoring and confidence calculations
- Weather-aware refresh pipeline
- Model persistence at `artifacts/order_forecast_model.pkl`
- Optional notification generation from trend signals

## 6) API Surface (Grouped)

### Admin
- UI pages under `/admin/*`
- JSON APIs under `/admin/api/*` (dashboard/users/products/orders/transactions/analytics/audit/alerts)

### Buyer
- Auth: `/api/signup`, `/api/login`
- Products: `/api/products`, `/api/products/<id>`
- Cart: `/api/cart/*`
- Orders: `/api/orders/*`
- Negotiation: `/api/negotiate/*`
- Wishlist: `/api/wishlist/*`

### Farmer
- Portal pages: `/farmer/*`
- Negotiation action: `/farmer/api/negotiate`
- Public farmer API: `/api/farmer/<farmer_id>`
- Notifications: `/farmer/api/notifications`, `/farmer/api/notifications/<id>/read`

### Offers
- `/offers` POST/GET
- `/offers/<offer_id>/respond` PATCH

## 7) Database Collections (Purpose)

- `admin_users`: admin credentials/state
- `users`: normalized platform users (farmer/buyer)
- `products`: marketplace product catalog
- `orders`: admin-visible order ledger
- `transactions`: payment/review transaction records
- `offers`: offer lifecycle data
- `admin_activity_logs`: admin action audit trail
- `admin_alerts`: anomaly/alert records
- `ml_order_forecasts`: forecast snapshots
- `ml_crop_trends`: crop trend snapshots
- `farmer_notifications`: notifications for farmers
- `farmers`: farmer profile master data
- `buyer_Cart`: buyer cart documents
- `buyer_Orders`: buyer order documents
- `buyer_Negotiations`: buyer negotiation records
- `buyer_Wishlist`: buyer wishlist data
- `buyer_Users`: legacy compatibility user store
- `buyer_Products`: legacy compatibility product store

Collection validators and indexes are managed by:
- `app/repositories/schema.py`
- `app/repositories/indexes.py`

## 8) CLI Commands

Defined in `app/cli.py`:

- `flask --app run.py init-db`
- `flask --app run.py seed-admin --email <email>`
- `flask --app run.py seed-demo-data [--reset]`
- `flask --app run.py seed-trend-offers [--reset]`
- `flask --app run.py seed-3d-data`
- `flask --app run.py refresh-ai-insights`

## 9) Setup & Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `.env` values (minimum):
- `MONGODB_URI=...`
- `DATABASE_NAME=farm_to_market`

Initialize and run:

```bash
flask --app run.py init-db
flask --app run.py seed-admin --email admin@example.com
flask --app run.py run
```

Useful URLs:
- `http://127.0.0.1:5000/login`
- `http://127.0.0.1:5000/admin/login`
- `http://127.0.0.1:5000/buyer/index.html`
- `http://127.0.0.1:5000/farmer`

## 10) Testing

Run all tests:

```bash
pytest -q
```

Test coverage includes:
- Unit tests for services (auth/order/product/offer/analytics/market intelligence)
- Integration tests for admin, buyer, farmer portal, offers, analytics endpoints
- `mongomock`-based DB simulation for reliable local runs

## 11) Notes for Team Integration

- Keep all modules on shared DB (`farm_to_market`) for integrated behavior.
- If Mongo Atlas connectivity is unstable, APIs/pages may fail at app startup because DB schema/index checks run during app creation.
- For consistent buyer visuals, buyer pages now include local image placeholders in `frontend/buyer/images/placeholders/`.
