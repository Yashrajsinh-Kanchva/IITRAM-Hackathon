import random
from datetime import timedelta

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from app.repositories.schema import ensure_database_structure
from app.services.analytics_service import compute_quality_score
from app.utils.time_utils import utcnow

FARM_PRODUCTS = {
    "grain": ["Wheat", "Rice", "Maize", "Bajra", "Barley"],
    "vegetable": ["Tomato", "Potato", "Onion", "Brinjal", "Cauliflower", "Peas"],
    "fruit": ["Mango", "Banana", "Guava", "Papaya", "Pomegranate"],
    "pulse": ["Chickpea", "Lentil", "Green Gram", "Black Gram", "Toor Dal"],
    "spice": ["Cumin", "Turmeric", "Coriander", "Chili", "Fenugreek"],
}

ORDER_STATUSES = ["pending", "confirmed", "packed", "shipped", "delivered", "cancelled"]
PAYMENT_STATUSES = ["pending", "paid", "failed", "refunded"]
REVIEW_STATES = ["pending_review", "reviewed", "flagged"]
USER_STATUSES = ["active", "active", "active", "inactive", "suspended"]


def _random_ts(days_back=120):
    now = utcnow()
    back_days = random.randint(0, max(days_back - 1, 0))
    back_minutes = random.randint(0, 24 * 60 - 1)
    return now - timedelta(days=back_days, minutes=back_minutes)


def _weighted_order_status():
    roll = random.random()
    if roll < 0.1:
        return "pending"
    if roll < 0.2:
        return "confirmed"
    if roll < 0.3:
        return "packed"
    if roll < 0.45:
        return "shipped"
    if roll < 0.9:
        return "delivered"
    return "cancelled"


def _payment_for_order_status(order_status):
    if order_status == "cancelled":
        return random.choice(["failed", "refunded", "pending"])
    if order_status in {"shipped", "delivered"}:
        return random.choice(["paid", "paid", "paid", "pending"])
    return random.choice(["pending", "paid", "failed"])


def _review_state_for_payment(payment_status):
    if payment_status in {"failed", "refunded"}:
        return random.choice(["flagged", "pending_review", "reviewed"])
    return random.choice(["reviewed", "pending_review"])


def _build_demo_users(count):
    first_names = [
        "Aarav",
        "Vihaan",
        "Saanvi",
        "Ananya",
        "Riya",
        "Arjun",
        "Karan",
        "Meera",
        "Ishaan",
        "Neha",
    ]
    last_names = [
        "Patel",
        "Sharma",
        "Singh",
        "Yadav",
        "Prajapati",
        "Desai",
        "Kumar",
        "Rathod",
        "Chauhan",
        "Joshi",
    ]

    users = []
    for i in range(count):
        created_at = _random_ts(days_back=120)
        role = "farmer" if i < int(count * 0.55) else "buyer"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}.{i}@demo.local"
        users.append(
            {
                "name": name,
                "email": email,
                "role": role,
                "status": random.choice(USER_STATUSES),
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
    return users


def _build_demo_products(count, farmers):
    quality_tags = ["Premium", "Organic", "Fresh", "Export Grade", "Sorted"]
    products = []
    catalog = [(category, item) for category, items in FARM_PRODUCTS.items() for item in items]

    for i in range(count):
        created_at = _random_ts(days_back=120)
        category, item_name = random.choice(catalog)
        farmer = random.choice(farmers) if farmers else None
        status = random.choices(
            ["approved", "pending", "hidden", "rejected"],
            weights=[70, 15, 10, 5],
            k=1,
        )[0]
        review_note = ""
        if status == "approved":
            review_note = "Verified quality and quantity."
        elif status == "rejected":
            review_note = "Image and quantity mismatch."
        elif status == "hidden":
            review_note = "Temporarily hidden due to stock issue."

        products.append(
            {
                "name": f"{random.choice(quality_tags)} {item_name}",
                "description": f"{item_name} sourced from local farms.",
                "category": category,
                "price": random.randint(500, 7000),
                "stock_qty": random.randint(20, 600),
                "unit": random.choice(["kg", "quintal", "crate"]),
                "image_url": f"https://example.com/images/{item_name.lower().replace(' ', '-')}-{i}.jpg",
                "seller_verified": random.choice([True, True, False]),
                "status": status,
                "seller_name": farmer.get("name") if farmer else None,
                "seller_email": farmer.get("email") if farmer else None,
                "review_note": review_note,
                "reviewed_by": None,
                "reviewed_at": created_at if status in {"approved", "rejected", "hidden"} else None,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

        products[-1]["quality_score"] = compute_quality_score(products[-1])

    return products


def _build_demo_orders_and_transactions(count, buyers):
    orders = []
    transactions = []
    now = utcnow()

    for i in range(count):
        created_at = _random_ts(days_back=90)
        buyer = random.choice(buyers) if buyers else {"name": f"Buyer {i+1}", "email": f"buyer{i+1}@demo.local"}
        status = _weighted_order_status()
        total_amount = random.randint(1200, 25000)
        order_number = f"ORD-{created_at.strftime('%Y%m%d')}-{1000 + i}"

        orders.append(
            {
                "order_number": order_number,
                "buyer_name": buyer.get("name"),
                "buyer_email": buyer.get("email"),
                "status": status,
                "total_amount": total_amount,
                "delivery_address": random.choice(
                    [
                        "Ahmedabad Central Market",
                        "Surat Fresh Hub",
                        "Vadodara Retail Zone",
                        "Rajkot Supply Point",
                    ]
                ),
                "created_at": created_at,
                "updated_at": min(now, created_at + timedelta(days=random.randint(0, 5))),
            }
        )

        payment_status = _payment_for_order_status(status)
        transactions.append(
            {
                "transaction_ref": f"TXN-{created_at.strftime('%y%m%d')}-{20000 + i}",
                "order_number": order_number,
                "amount": total_amount,
                "payment_status": payment_status,
                "review_state": _review_state_for_payment(payment_status),
                "gateway": random.choice(["razorpay", "stripe", "upi"]),
                "created_at": created_at + timedelta(minutes=random.randint(5, 180)),
                "updated_at": created_at + timedelta(days=random.randint(0, 3)),
            }
        )

    return orders, transactions


def _build_demo_activity_logs(admin_id, users, products, orders, transactions, count=120):
    actions = [
        ("user_status_updated", "user"),
        ("product_reviewed", "product"),
        ("order_status_updated", "order"),
        ("transaction_state_updated", "transaction"),
        ("admin_login", "admin_user"),
    ]

    logs = []
    entity_lookup = {
        "user": users,
        "product": products,
        "order": orders,
        "transaction": transactions,
    }

    for _ in range(count):
        action, entity_type = random.choice(actions)
        created_at = _random_ts(days_back=40)
        entity_id = None
        details = {}

        if entity_type in entity_lookup and entity_lookup[entity_type]:
            entity = random.choice(entity_lookup[entity_type])
            entity_id = str(entity.get("_id")) if entity.get("_id") else None
            if entity_type == "order":
                details = {"new_status": entity.get("status")}
            elif entity_type == "transaction":
                details = {"payment_status": entity.get("payment_status")}
            elif entity_type == "product":
                details = {"status": entity.get("status")}
            elif entity_type == "user":
                details = {"new_status": entity.get("status")}

        logs.append(
            {
                "admin_id": str(admin_id) if admin_id else None,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "details": details,
                "created_at": created_at,
            }
        )

    logs.sort(key=lambda item: item["created_at"])
    return logs


def register_commands(app):
    @app.cli.command("init-db")
    @click.option(
        "--skip-validators",
        is_flag=True,
        default=False,
        help="Create collections and indexes without applying Mongo validators.",
    )
    def init_db(skip_validators):
        summary = ensure_database_structure(
            current_app.db,
            apply_validators=not skip_validators,
        )

        click.echo("Database initialization complete:")
        for collection_name, status in summary.items():
            click.echo(f"- {collection_name}: {status}")

    @app.cli.command("seed-admin")
    @click.option("--email", required=True, help="Admin email")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def seed_admin(email, password):
        admin_users = current_app.db.admin_users
        now = utcnow()
        existing = admin_users.find_one({"email": email.lower()})

        payload = {
            "email": email.lower(),
            "password_hash": generate_password_hash(password),
            "status": "active",
            "updated_at": now,
        }

        if existing:
            admin_users.update_one({"_id": existing["_id"]}, {"$set": payload})
            click.echo("Updated existing admin user")
            return

        payload["created_at"] = now
        payload["last_login_at"] = None
        admin_users.insert_one(payload)
        click.echo("Created admin user")

    @app.cli.command("seed-demo-data")
    @click.option("--users", "users_count", default=80, show_default=True, type=int)
    @click.option("--products", "products_count", default=120, show_default=True, type=int)
    @click.option("--orders", "orders_count", default=220, show_default=True, type=int)
    @click.option(
        "--activity-logs",
        "activity_count",
        default=120,
        show_default=True,
        type=int,
    )
    @click.option(
        "--reset",
        is_flag=True,
        default=False,
        help="Delete existing users/products/orders/transactions/activity logs before seeding.",
    )
    def seed_demo_data(users_count, products_count, orders_count, activity_count, reset):
        db = current_app.db
        ensure_database_structure(db, apply_validators=True)

        if reset:
            db.users.delete_many({})
            db.products.delete_many({})
            db.orders.delete_many({})
            db.transactions.delete_many({})
            db.admin_activity_logs.delete_many({})
            click.echo("Cleared existing marketplace demo collections.")

        users = _build_demo_users(users_count)
        if users:
            db.users.insert_many(users)

        farmers = users[: int(len(users) * 0.55)]
        buyers = users[int(len(users) * 0.55) :]

        products = _build_demo_products(products_count, farmers)
        if products:
            db.products.insert_many(products)

        orders, transactions = _build_demo_orders_and_transactions(orders_count, buyers)
        if orders:
            db.orders.insert_many(orders)
        if transactions:
            db.transactions.insert_many(transactions)

        admin = db.admin_users.find_one({}, sort=[("created_at", 1)])
        logs = _build_demo_activity_logs(
            admin_id=admin.get("_id") if admin else None,
            users=users,
            products=products,
            orders=orders,
            transactions=transactions,
            count=activity_count,
        )
        if logs:
            db.admin_activity_logs.insert_many(logs)

        click.echo("Demo data seeded successfully:")
        click.echo(f"- users: {len(users)}")
        click.echo(f"- products: {len(products)}")
        click.echo(f"- orders: {len(orders)}")
        click.echo(f"- transactions: {len(transactions)}")
        click.echo(f"- activity logs: {len(logs)}")
