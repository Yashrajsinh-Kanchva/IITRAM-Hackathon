import re
from datetime import datetime, timezone

from pymongo import ReturnDocument

from app.utils.pagination import build_pagination_meta
from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow


class OrderRepository:
    def __init__(self, db):
        self.collection = db.orders

    def _build_query(self, filters):
        query = {}
        if filters.get("status"):
            query["status"] = filters["status"]
        if filters.get("search"):
            pattern = re.escape(filters["search"])
            query["$or"] = [
                {"buyer_name": {"$regex": pattern, "$options": "i"}},
                {"order_number": {"$regex": pattern, "$options": "i"}},
            ]
        return query

    def list(self, filters, pagination):
        query = self._build_query(filters)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(pagination["skip"])
            .limit(pagination["page_size"])
        )
        items = [serialize_document(doc) for doc in cursor]
        total = self.collection.count_documents(query)
        meta = build_pagination_meta(pagination["page"], pagination["page_size"], total)
        return items, meta

    def find_by_id(self, order_id):
        oid = to_object_id(order_id)
        if not oid:
            return None
        return self.collection.find_one({"_id": oid})

    def update_status(self, order_id, status):
        oid = to_object_id(order_id)
        if not oid:
            return None

        updated = self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"status": status, "updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(updated)

    def count_all(self):
        return self.collection.count_documents({})

    def count_since(self, since):
        return self.collection.count_documents({"created_at": {"$gte": since}})

    def daily_order_counts(self, start_dt, end_dt):
        docs = self.collection.find({"created_at": {"$gte": start_dt, "$lte": end_dt}})
        buckets = {}
        for doc in docs:
            created = doc.get("created_at")
            if not created:
                continue
            key = created.date().isoformat()
            buckets[key] = buckets.get(key, 0) + 1
        return buckets

    def fetch_recent_for_3d(self, start_dt, end_dt, limit=100):
        """Fetch recent order records for 3D analytics with lightweight projection."""
        query = {"created_at": {"$gte": start_dt, "$lte": end_dt}}
        projection = {
            "_id": 0,
            "created_at": 1,
            "total_price": 1,
            "total_amount": 1,
            "price": 1,
            "quantity": 1,
            "total_quantity": 1,
        }
        cursor = (
            self.collection.find(query, projection)
            .sort("created_at", -1)
            .limit(limit)
        )
        items = []
        for doc in cursor:
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime) and created_at.tzinfo is not None:
                created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
                doc["created_at"] = created_at
            items.append(doc)
        return items
