from app.services.exceptions import ServiceError
from app.utils.pagination import parse_pagination
from app.utils.validators import ALLOWED_ORDER_STATUSES, is_valid_order_transition


class OrderService:
    def __init__(self, order_repo, activity_log_service, page_size=20):
        self.order_repo = order_repo
        self.activity_log_service = activity_log_service
        self.page_size = page_size

    def list_orders(self, query_args):
        pagination = parse_pagination(query_args, default_page_size=self.page_size)
        filters = {
            "search": query_args.get("search", "").strip(),
            "status": query_args.get("status", "").strip(),
        }
        items, meta = self.order_repo.list(filters, pagination)
        return {"items": items, "pagination": meta}

    def update_status(self, order_id, status, admin_id):
        if status not in ALLOWED_ORDER_STATUSES:
            raise ServiceError(f"Invalid order status '{status}'", status_code=400)

        existing = self.order_repo.find_by_id(order_id)
        if not existing:
            raise ServiceError("Order not found", status_code=404)

        current_status = existing.get("status", "pending")
        if not is_valid_order_transition(current_status, status):
            raise ServiceError(
                f"Cannot move order from '{current_status}' to '{status}'",
                status_code=400,
            )

        updated = self.order_repo.update_status(order_id, status)
        self.activity_log_service.log(
            admin_id,
            action="order_status_updated",
            entity_type="order",
            entity_id=order_id,
            details={"previous_status": current_status, "new_status": status},
        )
        return updated
