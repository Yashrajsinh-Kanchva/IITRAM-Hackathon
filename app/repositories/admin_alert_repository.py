from pymongo import ReturnDocument

from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow


class AdminAlertRepository:
    def __init__(self, db):
        self.collection = db.admin_alerts

    def list_unresolved(self, limit=25):
        cursor = self.collection.find({"is_resolved": False}).sort("triggered_at", -1).limit(limit)
        return [serialize_document(doc) for doc in cursor]

    def upsert_unresolved(self, alert_type, severity, message):
        now = utcnow()
        doc = self.collection.find_one_and_update(
            {"type": alert_type, "is_resolved": False},
            {
                "$set": {
                    "severity": severity,
                    "message": message,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "type": alert_type,
                    "triggered_at": now,
                    "resolved_at": None,
                    "resolved_by": None,
                    "is_resolved": False,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(doc)

    def resolve(self, alert_id, resolved_by):
        oid = to_object_id(alert_id)
        if not oid:
            return None
        now = utcnow()
        doc = self.collection.find_one_and_update(
            {"_id": oid, "is_resolved": False},
            {
                "$set": {
                    "is_resolved": True,
                    "resolved_at": now,
                    "resolved_by": str(resolved_by) if resolved_by else None,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(doc)
