from pymongo import ASCENDING


def ensure_indexes(db):
    db.admin_users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING), ("status", ASCENDING)])
    db.products.create_index(
        [("status", ASCENDING), ("category", ASCENDING), ("created_at", ASCENDING)]
    )
    db.orders.create_index([("status", ASCENDING), ("created_at", ASCENDING)])
    db.transactions.create_index(
        [("payment_status", ASCENDING), ("created_at", ASCENDING)]
    )
    db.offers.create_index([("product_id", ASCENDING), ("created_at", ASCENDING)])
    db.offers.create_index([("farmer_id", ASCENDING), ("status", ASCENDING)])
    db.offers.create_index([("buyer_id", ASCENDING), ("status", ASCENDING)])
    db.offers.create_index([("status", ASCENDING), ("expires_at", ASCENDING)])
    db.offers.create_index(
        [("product_id", ASCENDING), ("buyer_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"status": {"$in": ["pending", "countered"]}},
        name="uniq_active_offer_per_buyer_product",
    )
    db.admin_activity_logs.create_index([("created_at", ASCENDING)])
    db.admin_alerts.create_index([("is_resolved", ASCENDING), ("triggered_at", ASCENDING)])
    db.admin_alerts.create_index([("type", ASCENDING), ("is_resolved", ASCENDING)])
