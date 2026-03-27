from datetime import timedelta

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.utils.pagination import build_pagination_meta
from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow
from app.utils.validators import ACTIVE_OFFER_STATUSES


class OfferRepository:
    def __init__(self, db):
        self.collection = db.offers
        self.products = db.products
        self.users = db.users

    def find_product_by_id(self, product_id):
        oid = to_object_id(product_id)
        if not oid:
            return None
        return self.products.find_one({"_id": oid})

    def create_offer(
        self,
        product_id,
        buyer_id,
        farmer_id,
        price,
        quantity,
        expires_at,
        note=None,
    ):
        now = utcnow()
        doc = {
            "product_id": product_id,
            "buyer_id": buyer_id,
            "farmer_id": farmer_id,
            "price": float(price),
            "quantity": int(quantity),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at,
            "history": [
                {
                    "event": "created",
                    "actor_id": buyer_id,
                    "actor_role": "buyer",
                    "price": float(price),
                    "quantity": int(quantity),
                    "note": note,
                    "at": now,
                }
            ],
        }
        try:
            result = self.collection.insert_one(doc)
        except DuplicateKeyError:
            return None, "duplicate_active_offer"

        created = self.collection.find_one({"_id": result.inserted_id})
        return serialize_document(created), None

    def list_by_product(self, product_id, page, page_size, buyer_id=None):
        query = {"product_id": product_id}
        if buyer_id:
            query["buyer_id"] = buyer_id
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = [serialize_document(doc) for doc in cursor]
        total = self.collection.count_documents(query)
        meta = build_pagination_meta(page, page_size, total)
        return items, meta

    def expire_active_offer_for_pair(self, product_id, buyer_id):
        now = utcnow()
        self.collection.update_many(
            {
                "product_id": product_id,
                "buyer_id": buyer_id,
                "status": {"$in": list(ACTIVE_OFFER_STATUSES)},
                "expires_at": {"$lte": now},
            },
            {
                "$set": {"status": "expired", "updated_at": now},
                "$push": {
                    "history": {
                        "event": "expired",
                        "actor_role": "system",
                        "at": now,
                    }
                },
            },
        )

    def find_by_id(self, offer_id):
        oid = to_object_id(offer_id)
        if not oid:
            return None
        return self.collection.find_one({"_id": oid})

    def find_user_by_id(self, user_id):
        oid = to_object_id(user_id)
        if not oid:
            return None
        return self.users.find_one({"_id": oid})

    def find_user_by_email(self, email):
        if not email:
            return None
        return self.users.find_one({"email": str(email).strip().lower()})

    def expire_offer_if_needed(self, offer_id):
        oid = to_object_id(offer_id)
        if not oid:
            return None
        now = utcnow()
        updated = self.collection.find_one_and_update(
            {
                "_id": oid,
                "status": {"$in": list(ACTIVE_OFFER_STATUSES)},
                "expires_at": {"$lte": now},
            },
            {
                "$set": {"status": "expired", "updated_at": now},
                "$push": {
                    "history": {
                        "event": "expired",
                        "actor_role": "system",
                        "at": now,
                    }
                },
            },
            return_document=ReturnDocument.AFTER,
        )
        return updated

    def expire_offers_for_product(self, product_id):
        now = utcnow()
        self.collection.update_many(
            {
                "product_id": product_id,
                "status": {"$in": list(ACTIVE_OFFER_STATUSES)},
                "expires_at": {"$lte": now},
            },
            {
                "$set": {"status": "expired", "updated_at": now},
                "$push": {
                    "history": {
                        "event": "expired",
                        "actor_role": "system",
                        "at": now,
                    }
                },
            },
        )

    def respond_offer(
        self,
        offer_id,
        expected_statuses,
        response_status,
        actor_id,
        actor_role,
        counter_price=None,
        counter_quantity=None,
        note=None,
        counter_expiry_hours=24,
    ):
        oid = to_object_id(offer_id)
        if not oid:
            return None

        now = utcnow()
        updates = {
            "status": response_status,
            "updated_at": now,
        }
        history_item = {
            "event": response_status,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "at": now,
            "note": note,
        }

        if response_status == "countered":
            updates["price"] = float(counter_price)
            updates["quantity"] = int(counter_quantity)
            updates["expires_at"] = now + timedelta(hours=counter_expiry_hours)
            history_item["price"] = float(counter_price)
            history_item["quantity"] = int(counter_quantity)

        updated = self.collection.find_one_and_update(
            {
                "_id": oid,
                "status": {"$in": list(expected_statuses)},
                "expires_at": {"$gt": now},
            },
            {
                "$set": updates,
                "$push": {"history": history_item},
            },
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(updated)
