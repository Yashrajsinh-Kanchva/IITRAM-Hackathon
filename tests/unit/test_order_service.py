import pytest

from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.order_repository import OrderRepository
from app.services.activity_log_service import ActivityLogService
from app.services.exceptions import ServiceError
from app.services.order_service import OrderService


def build_service(db):
    activity = ActivityLogService(ActivityLogRepository(db))
    return OrderService(OrderRepository(db), activity)


def test_order_status_valid_transition(db):
    service = build_service(db)
    order = db.orders.find_one({"order_number": "ORD-1001"})

    updated = service.update_status(str(order["_id"]), "confirmed", admin_id="admin-1")

    assert updated["status"] == "confirmed"


def test_order_status_invalid_transition(db):
    service = build_service(db)
    order = db.orders.find_one({"order_number": "ORD-1001"})

    with pytest.raises(ServiceError) as exc:
        service.update_status(str(order["_id"]), "delivered", admin_id="admin-1")

    assert "Cannot move order" in exc.value.message
