from datetime import timedelta

from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService
from app.utils.time_utils import utcnow


def build_service(db):
    return AnalyticsService(
        OrderRepository(db),
        TransactionRepository(db),
        UserRepository(db),
        ProductRepository(db),
    )


def test_sales_analytics_returns_expected_series(db):
    service = build_service(db)
    result = service.sales_trend("7d")

    assert result["range"] == "7d"
    assert len(result["series"]) == 7
    total = sum(point["value"] for point in result["series"])
    assert total >= 7000


def test_overview_contains_category_and_growth(db):
    now = utcnow()
    db.users.insert_one(
        {
            "name": "New Buyer",
            "email": "newbuyer@example.com",
            "role": "buyer",
            "status": "active",
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1),
        }
    )

    service = build_service(db)
    overview = service.overview("30d")

    assert overview["range"] == "30d"
    assert any(item["category"] == "grain" for item in overview["category_activity"])
    assert len(overview["user_growth"]) == 30
