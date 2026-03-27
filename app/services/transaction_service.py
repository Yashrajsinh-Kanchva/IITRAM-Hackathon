from app.services.exceptions import ServiceError
from app.utils.pagination import parse_pagination
from app.utils.validators import ALLOWED_PAYMENT_STATUSES, ALLOWED_REVIEW_STATES


class TransactionService:
    def __init__(self, transaction_repo, activity_log_service, page_size=20):
        self.transaction_repo = transaction_repo
        self.activity_log_service = activity_log_service
        self.page_size = page_size

    def list_transactions(self, query_args):
        pagination = parse_pagination(query_args, default_page_size=self.page_size)
        filters = {
            "search": query_args.get("search", "").strip(),
            "payment_status": query_args.get("payment_status", "").strip(),
            "review_state": query_args.get("review_state", "").strip(),
        }
        items, meta = self.transaction_repo.list(filters, pagination)
        return {"items": items, "pagination": meta}

    def update_state(self, transaction_id, payment_status, review_state, admin_id):
        if not payment_status and not review_state:
            raise ServiceError("Provide payment_status or review_state", status_code=400)

        updates = {}
        if payment_status:
            if payment_status not in ALLOWED_PAYMENT_STATUSES:
                raise ServiceError(f"Invalid payment_status '{payment_status}'", status_code=400)
            updates["payment_status"] = payment_status

        if review_state:
            if review_state not in ALLOWED_REVIEW_STATES:
                raise ServiceError(f"Invalid review_state '{review_state}'", status_code=400)
            updates["review_state"] = review_state

        updated = self.transaction_repo.update_state(transaction_id, updates)
        if not updated:
            raise ServiceError("Transaction not found", status_code=404)

        self.activity_log_service.log(
            admin_id,
            action="transaction_state_updated",
            entity_type="transaction",
            entity_id=transaction_id,
            details=updates,
        )
        return updated
