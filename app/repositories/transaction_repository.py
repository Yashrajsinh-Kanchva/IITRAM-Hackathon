import re

from pymongo import ReturnDocument

from app.utils.pagination import build_pagination_meta
from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow


class TransactionRepository:
    def __init__(self, db):
        self.collection = db.transactions

    def _build_query(self, filters):
        query = {}
        if filters.get("payment_status"):
            query["payment_status"] = filters["payment_status"]
        if filters.get("review_state"):
            query["review_state"] = filters["review_state"]
        if filters.get("search"):
            pattern = re.escape(filters["search"])
            query["$or"] = [
                {"transaction_ref": {"$regex": pattern, "$options": "i"}},
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

    def update_state(self, transaction_id, updates):
        oid = to_object_id(transaction_id)
        if not oid:
            return None
        updates["updated_at"] = utcnow()
        updated = self.collection.find_one_and_update(
            {"_id": oid}, {"$set": updates}, return_document=ReturnDocument.AFTER
        )
        return serialize_document(updated)

    def count_all(self):
        return self.collection.count_documents({})

    def count_failed(self):
        return self.collection.count_documents({"payment_status": "failed"})

    def paid_gmv_since(self, since):
        pipeline = [
            {"$match": {"payment_status": "paid", "created_at": {"$gte": since}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        rows = list(self.collection.aggregate(pipeline))
        return float(rows[0]["total"]) if rows else 0.0

    def daily_sales(self, start_dt, end_dt):
        docs = self.collection.find(
            {
                "payment_status": "paid",
                "created_at": {"$gte": start_dt, "$lte": end_dt},
            }
        )
        buckets = {}
        for doc in docs:
            created = doc.get("created_at")
            if not created:
                continue
            key = created.date().isoformat()
            buckets[key] = buckets.get(key, 0.0) + float(doc.get("amount", 0) or 0)
        return buckets
