import re

from pymongo import ReturnDocument

from app.utils.pagination import build_pagination_meta
from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow


class ProductRepository:
    def __init__(self, db):
        self.collection = db.products

    def _build_query(self, filters):
        clauses = []
        if filters.get("status"):
            clauses.append({"status": filters["status"]})
        if filters.get("category"):
            clauses.append({"category": filters["category"]})
        if filters.get("search"):
            pattern = re.escape(filters["search"])
            clauses.append(
                {
                    "$or": [
                        {"name": {"$regex": pattern, "$options": "i"}},
                        {"description": {"$regex": pattern, "$options": "i"}},
                    ]
                }
            )
        quality_band = (filters.get("quality_band") or "").strip().lower()
        if quality_band == "excellent":
            clauses.append({"quality_score": {"$gt": 75}})
        elif quality_band == "good":
            clauses.append({"quality_score": {"$gte": 40, "$lte": 75}})
        elif quality_band == "poor":
            clauses.append(
                {
                    "$or": [
                        {"quality_score": {"$lt": 40}},
                        {"quality_score": {"$exists": False}},
                        {"quality_score": None},
                    ]
                }
            )

        if not clauses:
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

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

    def update_review(self, product_id, status, review_note, reviewed_by, quality_score=None):
        oid = to_object_id(product_id)
        if not oid:
            return None

        update = {
            "status": status,
            "review_note": review_note,
            "reviewed_by": str(reviewed_by) if reviewed_by else None,
            "reviewed_at": utcnow(),
            "updated_at": utcnow(),
        }
        if quality_score is not None:
            update["quality_score"] = int(quality_score)

        doc = self.collection.find_one_and_update(
            {"_id": oid}, {"$set": update}, return_document=ReturnDocument.AFTER
        )
        return serialize_document(doc)

    def count_all(self):
        return self.collection.count_documents({})

    def category_activity_since(self, since):
        docs = self.collection.find({"created_at": {"$gte": since}})
        summary = {}
        for doc in docs:
            category = doc.get("category", "uncategorized")
            summary[category] = summary.get(category, 0) + 1
        return summary

    def update_quality_score(self, product_id, quality_score):
        oid = to_object_id(product_id)
        if not oid:
            return None
        doc = self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"quality_score": int(quality_score), "updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(doc)
