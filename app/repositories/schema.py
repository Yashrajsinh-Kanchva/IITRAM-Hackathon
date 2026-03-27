from pymongo.errors import CollectionInvalid

from app.repositories.indexes import ensure_indexes


COLLECTION_SCHEMAS = {
    "admin_users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "password_hash", "status", "updated_at"],
            "properties": {
                "email": {"bsonType": "string"},
                "password_hash": {"bsonType": "string"},
                "status": {"enum": ["active", "inactive", "suspended"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
                "last_login_at": {"bsonType": ["date", "null"]},
            },
        }
    },
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "email", "role", "status", "created_at", "updated_at"],
            "properties": {
                "name": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "role": {"enum": ["farmer", "buyer"]},
                "status": {"enum": ["active", "inactive", "suspended"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "products": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "category", "price", "status", "created_at", "updated_at"],
            "properties": {
                "name": {"bsonType": "string"},
                "description": {"bsonType": ["string", "null"]},
                "category": {"bsonType": "string"},
                "price": {"bsonType": ["double", "int", "long", "decimal"]},
                "quality_score": {"bsonType": ["int", "long", "null"]},
                "status": {"bsonType": "string"},
                "review_note": {"bsonType": ["string", "null"]},
                "reviewed_by": {"bsonType": ["string", "null"]},
                "reviewed_at": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "orders": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["order_number", "status", "total_amount", "created_at", "updated_at"],
            "properties": {
                "order_number": {"bsonType": "string"},
                "buyer_name": {"bsonType": ["string", "null"]},
                "status": {
                    "enum": [
                        "pending",
                        "confirmed",
                        "packed",
                        "shipped",
                        "delivered",
                        "cancelled",
                    ]
                },
                "total_amount": {"bsonType": ["double", "int", "long", "decimal"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "transactions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "transaction_ref",
                "order_number",
                "amount",
                "payment_status",
                "review_state",
                "created_at",
                "updated_at",
            ],
            "properties": {
                "transaction_ref": {"bsonType": "string"},
                "order_number": {"bsonType": "string"},
                "amount": {"bsonType": ["double", "int", "long", "decimal"]},
                "payment_status": {"enum": ["pending", "paid", "failed", "refunded"]},
                "review_state": {"enum": ["pending_review", "reviewed", "flagged"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "offers": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "product_id",
                "buyer_id",
                "farmer_id",
                "price",
                "quantity",
                "status",
                "history",
                "created_at",
                "updated_at",
                "expires_at",
            ],
            "properties": {
                "product_id": {"bsonType": "string"},
                "buyer_id": {"bsonType": "string"},
                "farmer_id": {"bsonType": "string"},
                "price": {"bsonType": ["double", "int", "long", "decimal"]},
                "quantity": {"bsonType": ["int", "long"]},
                "status": {
                    "enum": ["pending", "countered", "accepted", "rejected", "expired"]
                },
                "history": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["event", "actor_role", "at"],
                        "properties": {
                            "event": {"bsonType": "string"},
                            "actor_id": {"bsonType": ["string", "null"]},
                            "actor_role": {"bsonType": "string"},
                            "price": {"bsonType": ["double", "int", "long", "decimal", "null"]},
                            "quantity": {"bsonType": ["int", "long", "null"]},
                            "note": {"bsonType": ["string", "null"]},
                            "at": {"bsonType": "date"},
                        },
                    },
                },
                "expires_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "admin_activity_logs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["action", "entity_type", "created_at"],
            "properties": {
                "admin_id": {"bsonType": ["string", "null"]},
                "action": {"bsonType": "string"},
                "entity_type": {"bsonType": "string"},
                "entity_id": {"bsonType": ["string", "null"]},
                "details": {"bsonType": "object"},
                "ip_address": {"bsonType": ["string", "null"]},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "admin_alerts": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "type",
                "severity",
                "message",
                "triggered_at",
                "is_resolved",
                "updated_at",
            ],
            "properties": {
                "type": {"bsonType": "string"},
                "severity": {"enum": ["warning", "critical"]},
                "message": {"bsonType": "string"},
                "triggered_at": {"bsonType": "date"},
                "resolved_at": {"bsonType": ["date", "null"]},
                "resolved_by": {"bsonType": ["string", "null"]},
                "is_resolved": {"bsonType": "bool"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
}


def _ensure_collection(db, name, validator=None, apply_validators=True):
    existing = set(db.list_collection_names())

    if name not in existing:
        try:
            if apply_validators and validator is not None:
                db.create_collection(
                    name,
                    validator=validator,
                    validationLevel="moderate",
                    validationAction="warn",
                )
            else:
                db.create_collection(name)
            return "created"
        except (TypeError, NotImplementedError, CollectionInvalid):
            if name not in set(db.list_collection_names()):
                db.create_collection(name)
            return "created"

    if apply_validators and validator is not None:
        try:
            db.command(
                {
                    "collMod": name,
                    "validator": validator,
                    "validationLevel": "moderate",
                    "validationAction": "warn",
                }
            )
            return "validated"
        except Exception:
            return "exists"

    return "exists"


def ensure_database_structure(db, apply_validators=True):
    results = {}
    for collection_name, validator in COLLECTION_SCHEMAS.items():
        results[collection_name] = _ensure_collection(
            db,
            collection_name,
            validator=validator,
            apply_validators=apply_validators,
        )

    ensure_indexes(db)
    return results
