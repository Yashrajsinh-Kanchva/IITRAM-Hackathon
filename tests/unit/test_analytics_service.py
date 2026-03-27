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


def test_get_3d_data_valid_dataset(db):
    service = build_service(db)
    now = utcnow()
    db.orders.insert_many(
        [
            {
                "order_number": "ORD-3D-1",
                "status": "confirmed",
                "total_amount": 2200,
                "quantity": 7,
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
            {
                "order_number": "ORD-3D-2",
                "status": "packed",
                "total_price": 1800,
                "quantity": 3,
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=2),
            },
        ]
    )

    data = service.get_3d_data("30d")
    assert isinstance(data, list)
    assert any(point["price"] > 0 for point in data)
    assert any(point["quantity"] > 0 for point in data)
    assert all({"time", "price", "quantity"} <= set(point.keys()) for point in data)


def test_get_3d_data_empty_dataset(db):
    db.orders.delete_many({})
    service = build_service(db)
    data = service.get_3d_data("7d")
    assert data == []


def test_get_3d_data_filters_invalid_values_and_missing_fields(db):
    service = build_service(db)
    now = utcnow()
    db.orders.insert_many(
        [
            {
                "order_number": "ORD-INV-1",
                "status": "confirmed",
                "total_amount": -100,
                "quantity": 10,
                "created_at": now - timedelta(hours=3),
                "updated_at": now - timedelta(hours=3),
            },
            {
                "order_number": "ORD-INV-2",
                "status": "confirmed",
                "total_amount": 1200,
                "quantity": 0,
                "created_at": now - timedelta(hours=2),
                "updated_at": now - timedelta(hours=2),
            },
            {
                "order_number": "ORD-INV-3",
                "status": "confirmed",
                "created_at": now - timedelta(hours=1),
                "updated_at": now - timedelta(hours=1),
            },
            {
                "order_number": "ORD-VALID-1",
                "status": "confirmed",
                "total_amount": 900,
                "quantity": 4,
                "created_at": now - timedelta(minutes=30),
                "updated_at": now - timedelta(minutes=30),
            },
            {
                "order_number": "ORD-BAD-DATE",
                "status": "confirmed",
                "total_amount": 1000,
                "quantity": 5,
                "created_at": "not-a-date",
                "updated_at": now,
            },
        ]
    )

    data = service.get_3d_data("7d")
    assert len(data) >= 1
    assert all(point["price"] > 0 for point in data)
    assert all(point["quantity"] > 0 for point in data)


def test_get_3d_data_large_dataset_capped_to_100_and_sorted_latest(db):
    service = build_service(db)
    now = utcnow()
    rows = []
    for index in range(160):
        dt = now - timedelta(minutes=index)
        rows.append(
            {
                "order_number": f"ORD-LARGE-{index}",
                "status": "confirmed",
                "total_amount": 1000 + index,
                "quantity": 1 + (index % 10),
                "created_at": dt,
                "updated_at": dt,
            }
        )
    db.orders.insert_many(rows)

    data = service.get_3d_data("30d")
    assert len(data) == 100
    timestamps = [point["time"] for point in data]
    assert timestamps == sorted(timestamps, reverse=True)
