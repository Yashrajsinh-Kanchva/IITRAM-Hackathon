from datetime import timedelta

from app.utils.time_utils import utcnow


class DashboardService:
    def __init__(
        self,
        user_repo,
        product_repo,
        order_repo,
        transaction_repo,
        activity_log_service,
    ):
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.order_repo = order_repo
        self.transaction_repo = transaction_repo
        self.activity_log_service = activity_log_service

    def get_kpis(self):
        now = utcnow()
        trailing_window = now - timedelta(days=30)
        return {
            "total_users": self.user_repo.count_all(),
            "total_products": self.product_repo.count_all(),
            "total_orders": self.order_repo.count_all(),
            "revenue_proxy": round(self.transaction_repo.paid_gmv_since(trailing_window), 2),
            "failed_transactions": self.transaction_repo.count_failed(),
        }

    def recent_activity(self, limit=8):
        return self.activity_log_service.recent(limit)
