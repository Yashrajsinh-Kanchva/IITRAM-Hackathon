from app.services.exceptions import ServiceError
from app.services.analytics_service import compute_quality_score
from app.utils.pagination import parse_pagination
from app.utils.serialization import to_object_id
from app.utils.validators import ALLOWED_PRODUCT_REVIEW_STATUSES


class ProductService:
    def __init__(self, product_repo, activity_log_service, page_size=20):
        self.product_repo = product_repo
        self.activity_log_service = activity_log_service
        self.page_size = page_size

    def list_products(self, query_args):
        self._ensure_identity_fields_for_missing()
        self._ensure_quality_scores_for_missing()
        pagination = parse_pagination(query_args, default_page_size=self.page_size)
        filters = {
            "search": query_args.get("search", "").strip(),
            "status": query_args.get("status", "").strip(),
            "category": query_args.get("category", "").strip(),
            "quality_band": query_args.get("quality", "").strip(),
        }
        items, meta = self.product_repo.list(filters, pagination)
        for item in items:
            if item.get("quality_score") is None:
                item["quality_score"] = compute_quality_score(item)
        return {"items": items, "pagination": meta}

    def review_product(self, product_id, status, review_note, admin_id):
        if status not in ALLOWED_PRODUCT_REVIEW_STATUSES:
            raise ServiceError(f"Invalid review status '{status}'", status_code=400)

        existing = self.product_repo.collection.find_one({"_id": to_object_id(product_id)})
        if not existing:
            raise ServiceError("Product not found", status_code=404)

        candidate = {**existing, "status": status, "review_note": review_note}
        quality_score = compute_quality_score(candidate)

        updated = self.product_repo.update_review(
            product_id,
            status,
            review_note,
            admin_id,
            quality_score=quality_score,
        )
        if not updated:
            raise ServiceError("Product not found", status_code=404)

        self.activity_log_service.log(
            admin_id,
            action="product_reviewed",
            entity_type="product",
            entity_id=product_id,
            details={"status": status, "review_note": review_note},
        )
        return updated

    def quality_summary(self):
        self._ensure_identity_fields_for_missing()
        self._ensure_quality_scores_for_missing()
        excellent = 0
        good = 0
        poor = 0

        cursor = self.product_repo.collection.find({})
        for doc in cursor:
            score = doc.get("quality_score")
            if score is None:
                score = compute_quality_score(doc)
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = 0

            if score > 75:
                excellent += 1
            elif score >= 40:
                good += 1
            else:
                poor += 1

        return {"excellent": excellent, "good": good, "poor": poor}

    def _ensure_quality_scores_for_missing(self):
        cursor = self.product_repo.collection.find(
            {"$or": [{"quality_score": {"$exists": False}}, {"quality_score": None}]}
        )
        for doc in cursor:
            score = compute_quality_score(doc)
            self.product_repo.update_quality_score(str(doc["_id"]), score)

    @staticmethod
    def _infer_category_from_text(value):
        text = str(value or "").strip().lower()
        if not text:
            return "crop"
        if any(token in text for token in ("honey", "madhu")):
            return "honey"
        if any(
            token in text
            for token in ("milk", "dairy", "paneer", "curd", "ghee", "butter", "cheese", "yogurt")
        ):
            return "dairy"
        if any(
            token in text
            for token in (
                "mango",
                "banana",
                "apple",
                "orange",
                "grape",
                "papaya",
                "guava",
                "pomegranate",
                "fruit",
            )
        ):
            return "fruit"
        if any(
            token in text
            for token in ("wheat", "rice", "maize", "grain", "millet", "barley", "bajra", "jowar")
        ):
            return "grain"
        if any(
            token in text
            for token in (
                "tomato",
                "onion",
                "potato",
                "brinjal",
                "eggplant",
                "cabbage",
                "carrot",
                "cauliflower",
                "peas",
                "spinach",
                "okra",
                "vegetable",
            )
        ):
            return "vegetable"
        if any(token in text for token in ("chickpea", "lentil", "gram", "pulse", "toor", "dal")):
            return "pulse"
        if any(token in text for token in ("cumin", "turmeric", "coriander", "chili", "fenugreek", "spice")):
            return "spice"
        if "cotton" in text:
            return "fiber"
        return "crop"

    def _ensure_identity_fields_for_missing(self):
        missing_query = {
            "$or": [
                {"name": {"$exists": False}},
                {"name": None},
                {"name": ""},
                {"category": {"$exists": False}},
                {"category": None},
                {"category": ""},
            ]
        }
        cursor = self.product_repo.collection.find(missing_query)
        for doc in cursor:
            current_name = str(doc.get("name") or "").strip()
            crop_name = str(doc.get("crop_name") or "").strip()
            current_category = str(doc.get("category") or "").strip().lower()

            patch = {}
            if not current_name:
                patch["name"] = crop_name or "Farm Produce"

            if not current_category:
                source = " ".join(
                    [
                        crop_name,
                        str(doc.get("description") or "").strip(),
                        str(doc.get("name") or "").strip(),
                    ]
                )
                patch["category"] = self._infer_category_from_text(source)

            if patch:
                patch["updated_at"] = doc.get("updated_at") or doc.get("created_at")
                self.product_repo.collection.update_one({"_id": doc["_id"]}, {"$set": patch})

    def bulk_action(self, ids, action, admin_id):
        action_to_status = {
            "approve": "approved",
            "reject": "rejected",
            "hide": "hidden",
        }
        if action not in action_to_status:
            raise ServiceError("action must be one of approve, reject, hide", status_code=400)
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
            self.product_repo.collection.find({"_id": {"$in": object_ids}}, {"_id": 1})
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
        next_status = action_to_status[action]

        try:
            for raw_id, _ in normalized:
                try:
                    existing = self.product_repo.collection.find_one({"_id": to_object_id(raw_id)})
                    if not existing:
                        raise ValueError("product not found")
                    candidate = {
                        **existing,
                        "status": next_status,
                        "review_note": f"Bulk action: {action}",
                    }
                    quality_score = compute_quality_score(candidate)
                    updated = self.product_repo.update_review(
                        raw_id,
                        next_status,
                        f"Bulk action: {action}",
                        admin_id,
                        quality_score=quality_score,
                    )
                    if not updated:
                        raise ValueError("review update failed")

                    self.activity_log_service.log(
                        admin_id,
                        action="product_bulk_action",
                        entity_type="product",
                        entity_id=raw_id,
                        details={"bulk_action": action, "status": next_status},
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
