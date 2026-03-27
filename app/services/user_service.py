from app.services.exceptions import ServiceError
from app.utils.pagination import parse_pagination
from app.utils.serialization import to_object_id
from app.utils.validators import ALLOWED_USER_STATUSES


class UserService:
    def __init__(self, user_repo, activity_log_service, page_size=20):
        self.user_repo = user_repo
        self.activity_log_service = activity_log_service
        self.page_size = page_size

    def list_users(self, query_args):
        pagination = parse_pagination(query_args, default_page_size=self.page_size)
        filters = {
            "search": query_args.get("search", "").strip(),
            "role": query_args.get("role", "").strip(),
            "status": query_args.get("status", "").strip(),
        }
        items, meta = self.user_repo.list(filters, pagination)
        return {"items": items, "pagination": meta}

    def update_status(self, user_id, status, admin_id):
        if status not in ALLOWED_USER_STATUSES:
            raise ServiceError(f"Invalid status '{status}'", status_code=400)

        updated = self.user_repo.update_status(user_id, status)
        if not updated:
            raise ServiceError("User not found", status_code=404)

        self.activity_log_service.log(
            admin_id,
            action="user_status_updated",
            entity_type="user",
            entity_id=user_id,
            details={"new_status": status},
        )
        return updated

    def bulk_action(self, ids, action, admin_id):
        allowed_actions = {"activate", "suspend", "delete"}
        if action not in allowed_actions:
            raise ServiceError(
                "action must be one of activate, suspend, delete",
                status_code=400,
            )
        if not isinstance(ids, list) or not ids:
            raise ServiceError("ids must be a non-empty list", status_code=400)

        normalized = []
        invalid_ids = []
        for value in ids:
            oid = to_object_id(value)
            if not oid:
                invalid_ids.append(str(value))
            else:
                normalized.append((str(value), oid))

        if invalid_ids:
            return {
                "success_count": 0,
                "failed_ids": invalid_ids,
                "errors": [f"invalid ids: {', '.join(invalid_ids)}"],
            }

        object_ids = [oid for _, oid in normalized]
        existing_docs = list(
            self.user_repo.collection.find({"_id": {"$in": object_ids}}, {"_id": 1})
        )
        existing_ids = {str(doc["_id"]) for doc in existing_docs}
        missing = [raw_id for raw_id, oid in normalized if str(oid) not in existing_ids]
        if missing:
            return {
                "success_count": 0,
                "failed_ids": missing,
                "errors": [f"ids not found: {', '.join(missing)}"],
            }

        success_count = 0
        failed_ids = []
        errors = []

        try:
            for raw_id, oid in normalized:
                try:
                    if action == "delete":
                        result = self.user_repo.collection.delete_one({"_id": oid})
                        if result.deleted_count != 1:
                            raise ValueError("delete failed")
                        log_details = {"bulk_action": "delete"}
                    else:
                        status = "active" if action == "activate" else "suspended"
                        updated = self.user_repo.update_status(raw_id, status)
                        if not updated:
                            raise ValueError("status update failed")
                        log_details = {"bulk_action": action, "new_status": status}

                    self.activity_log_service.log(
                        admin_id,
                        action="user_bulk_action",
                        entity_type="user",
                        entity_id=raw_id,
                        details=log_details,
                    )
                    success_count += 1
                except Exception as exc:
                    failed_ids.append(raw_id)
                    errors.append(f"{raw_id}: {str(exc)}")
        except Exception as exc:
            errors.append(f"bulk operation error: {str(exc)}")

        return {
            "success_count": success_count,
            "failed_ids": failed_ids,
            "errors": errors,
        }
