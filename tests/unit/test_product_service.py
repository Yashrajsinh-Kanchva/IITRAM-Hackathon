import pytest

from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.product_repository import ProductRepository
from app.services.activity_log_service import ActivityLogService
from app.services.exceptions import ServiceError
from app.services.product_service import ProductService


def build_service(db):
    activity = ActivityLogService(ActivityLogRepository(db))
    return ProductService(ProductRepository(db), activity)


def test_product_review_approve_updates_fields(db):
    service = build_service(db)
    product = db.products.find_one({"name": "Wheat"})

    updated = service.review_product(
        str(product["_id"]),
        status="approved",
        review_note="Quality verified",
        admin_id="admin-1",
    )

    assert updated["status"] == "approved"
    assert updated["review_note"] == "Quality verified"
    assert updated["reviewed_at"] is not None


def test_product_review_rejects_invalid_status(db):
    service = build_service(db)
    product = db.products.find_one({"name": "Wheat"})

    with pytest.raises(ServiceError) as exc:
        service.review_product(
            str(product["_id"]),
            status="invalid",
            review_note="",
            admin_id="admin-1",
        )

    assert "Invalid review status" in exc.value.message
