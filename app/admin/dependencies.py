from flask import current_app, g

from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.admin_alert_repository import AdminAlertRepository
from app.repositories.admin_user_repository import AdminUserRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_log_service import ActivityLogService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


SERVICE_KEY = "_admin_services"


def get_services():
    cached = getattr(g, SERVICE_KEY, None)
    if cached:
        return cached

    db = current_app.db
    page_size = current_app.config.get("ADMIN_PAGE_SIZE", 20)

    admin_repo = AdminUserRepository(db)
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)
    order_repo = OrderRepository(db)
    transaction_repo = TransactionRepository(db)
    activity_repo = ActivityLogRepository(db)
    alert_repo = AdminAlertRepository(db)

    activity_service = ActivityLogService(activity_repo, admin_repo=admin_repo)

    services = {
        "auth": AuthService(admin_repo, activity_service),
        "users": UserService(user_repo, activity_service, page_size=page_size),
        "products": ProductService(product_repo, activity_service, page_size=page_size),
        "orders": OrderService(order_repo, activity_service, page_size=page_size),
        "transactions": TransactionService(
            transaction_repo,
            activity_service,
            page_size=page_size,
        ),
        "dashboard": DashboardService(
            user_repo,
            product_repo,
            order_repo,
            transaction_repo,
            activity_service,
        ),
        "analytics": AnalyticsService(
            order_repo,
            transaction_repo,
            user_repo,
            product_repo,
            alert_repo,
        ),
        "activity": activity_service,
    }

    setattr(g, SERVICE_KEY, services)
    return services
