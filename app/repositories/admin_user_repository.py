from app.utils.serialization import serialize_document, to_object_id
from app.utils.time_utils import utcnow


class AdminUserRepository:
    def __init__(self, db):
        self.collection = db.admin_users

    def find_by_email(self, email):
        return self.collection.find_one({"email": email.lower()})

    def find_by_id(self, admin_id):
        oid = to_object_id(admin_id)
        if not oid:
            return None
        return self.collection.find_one({"_id": oid})

    def update_last_login(self, admin_id):
        oid = to_object_id(admin_id)
        if not oid:
            return
        self.collection.update_one(
            {"_id": oid},
            {"$set": {"last_login_at": utcnow(), "updated_at": utcnow()}},
        )

    def to_public(self, admin):
        if not admin:
            return None
        serialized = serialize_document(admin)
        serialized.pop("password_hash", None)
        return serialized

    def find_ids_by_email_query(self, email_query):
        if not email_query:
            return []
        cursor = self.collection.find(
            {"email": {"$regex": email_query, "$options": "i"}},
            {"_id": 1},
        )
        return [str(doc["_id"]) for doc in cursor]

    def map_emails_by_ids(self, admin_ids):
        object_ids = []
        for admin_id in admin_ids:
            oid = to_object_id(admin_id)
            if oid:
                object_ids.append(oid)
        if not object_ids:
            return {}

        cursor = self.collection.find(
            {"_id": {"$in": object_ids}},
            {"_id": 1, "email": 1},
        )
        return {str(doc["_id"]): doc.get("email") for doc in cursor}
