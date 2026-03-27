import re

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
