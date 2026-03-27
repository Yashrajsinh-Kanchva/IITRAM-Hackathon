from app.utils.serialization import serialize_document
from app.utils.time_utils import utcnow


class ActivityLogRepository:
    def __init__(self, db):
        self.collection = db.admin_activity_logs

    def create(
        self,
        admin_id,
        action,
        entity_type,
        entity_id=None,
        details=None,
        ip_address=None,
    ):
        payload = {
            "admin_id": str(admin_id) if admin_id else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": utcnow(),
        }
        self.collection.insert_one(payload)

    def recent(self, limit=10):
        cursor = self.collection.find({}).sort("created_at", -1).limit(limit)
        return [serialize_document(doc) for doc in cursor]

    def list_filtered(self, query, skip=0, limit=50):
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        items = [serialize_document(doc) for doc in cursor]
        total = self.collection.count_documents(query)
        return items, total
