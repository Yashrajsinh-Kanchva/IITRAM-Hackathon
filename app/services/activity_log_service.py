from datetime import datetime, timedelta, timezone

from app.services.exceptions import ServiceError


class ActivityLogService:
    def __init__(self, repository, admin_repo=None):
        self.repository = repository
        self.admin_repo = admin_repo

    def log(
        self,
        admin_id,
        action,
        entity_type,
        entity_id=None,
        details=None,
        ip_address=None,
    ):
        self.repository.create(
            admin_id,
            action,
            entity_type,
            entity_id,
            details,
            ip_address=ip_address,
        )

    def recent(self, limit=10):
        return self.repository.recent(limit)

    def _parse_iso_date(self, value, field_name, end_of_day=False):
        if not value:
            return None
        try:
            value = value.strip()
            if len(value) == 10:
                parsed = datetime.strptime(value, "%Y-%m-%d")
                if end_of_day:
                    parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)
                return parsed
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if end_of_day and "T" not in value:
                parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError as exc:
            raise ServiceError(f"invalid {field_name} ISO date", status_code=400) from exc

    def _extract_changes(self, details):
        if not isinstance(details, dict):
            return {"before": {}, "after": {}}

        if isinstance(details.get("changes"), dict):
            changes = details["changes"]
            before = changes.get("before") or {}
            after = changes.get("after") or {}
            return {"before": before if isinstance(before, dict) else {}, "after": after if isinstance(after, dict) else {}}

        before = details.get("before") if isinstance(details.get("before"), dict) else {}
        after = details.get("after") if isinstance(details.get("after"), dict) else {}
        return {"before": before, "after": after}

    def list_logs(self, query_args):
        try:
            page = max(int(query_args.get("page", 1) or 1), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = max(int(query_args.get("per_page", 50) or 50), 1)
        except (TypeError, ValueError):
            per_page = 50
        per_page = min(per_page, 200)
        skip = (page - 1) * per_page

        filters = {
            "admin_email": (query_args.get("admin_email") or "").strip(),
            "action_type": (query_args.get("action_type") or "").strip(),
            "date_from": (query_args.get("date_from") or "").strip(),
            "date_to": (query_args.get("date_to") or "").strip(),
        }

        query = {}
        if filters["action_type"]:
            query["action"] = filters["action_type"]

        date_from = self._parse_iso_date(filters["date_from"], "date_from", end_of_day=False)
        date_to = self._parse_iso_date(filters["date_to"], "date_to", end_of_day=True)
        if date_from or date_to:
            range_query = {}
            if date_from:
                range_query["$gte"] = date_from
            if date_to:
                range_query["$lte"] = date_to
            query["created_at"] = range_query

        if filters["admin_email"]:
            if not self.admin_repo:
                return {"logs": [], "total": 0, "page": page, "pages": 0}
            admin_ids = self.admin_repo.find_ids_by_email_query(filters["admin_email"])
            if not admin_ids:
                return {"logs": [], "total": 0, "page": page, "pages": 0}
            query["admin_id"] = {"$in": admin_ids}

        rows, total = self.repository.list_filtered(query, skip=skip, limit=per_page)
        pages = (total + per_page - 1) // per_page if per_page else 0

        admin_ids = {row.get("admin_id") for row in rows if row.get("admin_id")}
        email_map = self.admin_repo.map_emails_by_ids(admin_ids) if self.admin_repo else {}

        logs = []
        for row in rows:
            logs.append(
                {
                    "id": row.get("id"),
                    "admin_email": email_map.get(row.get("admin_id")) or "-",
                    "action_type": row.get("action"),
                    "target_collection": row.get("entity_type"),
                    "target_id": row.get("entity_id"),
                    "changes": self._extract_changes(row.get("details") or {}),
                    "ip_address": row.get("ip_address"),
                    "created_at": row.get("created_at"),
                    "details": row.get("details") or {},
                }
            )

        return {"logs": logs, "total": total, "page": page, "pages": pages}
