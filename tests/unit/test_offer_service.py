from datetime import timedelta

import pytest

from app.repositories.offer_repository import OfferRepository
from app.services.exceptions import ServiceError
from app.services.offer_service import OfferService
from app.utils.serialization import to_object_id
from app.utils.time_utils import utcnow


def build_service(db):
    return OfferService(OfferRepository(db), page_size=20, expiry_hours=24)


def _seed_owned_product(db, farmer_id):
    doc = {
        "name": "Onion",
        "category": "vegetable",
        "price": 1100,
        "status": "approved",
        "farmer_id": farmer_id,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    inserted = db.products.insert_one(doc)
    return str(inserted.inserted_id)


def _seed_offer(db, product_id, buyer_id, farmer_id, status="pending", expires_at=None):
    now = utcnow()
    expires_at = expires_at or (now + timedelta(hours=12))
    doc = {
        "product_id": product_id,
        "buyer_id": buyer_id,
        "farmer_id": farmer_id,
        "price": 1000.0,
        "quantity": 10,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "expires_at": expires_at,
        "history": [
            {
                "event": "created",
                "actor_id": buyer_id,
                "actor_role": "buyer",
                "price": 1000.0,
                "quantity": 10,
                "at": now,
            }
        ],
    }
    inserted = db.offers.insert_one(doc)
    return str(inserted.inserted_id)


def test_valid_offer_creation(db):
    service = build_service(db)
    buyer = db.users.find_one({"role": "buyer"})
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))

    created = service.create_offer(
        {"product_id": product_id, "price": 1400, "quantity": 15, "note": "Fresh lot"},
        {"user_id": str(buyer["_id"]), "role": "buyer"},
    )

    assert created["status"] == "pending"
    assert created["price"] == 1400.0
    assert created["quantity"] == 15
    assert created["buyer_id"] == str(buyer["_id"])
    assert created["farmer_id"] == str(farmer["_id"])
    assert len(created["history"]) == 1


def test_invalid_price_rejected(db):
    service = build_service(db)
    buyer = db.users.find_one({"role": "buyer"})
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))

    with pytest.raises(ServiceError) as exc:
        service.create_offer(
            {"product_id": product_id, "price": 0, "quantity": 5},
            {"user_id": str(buyer["_id"]), "role": "buyer"},
        )

    assert exc.value.status_code == 400
    assert "price must be > 0" in exc.value.message


def test_unauthorized_user_role_rejected(db):
    service = build_service(db)
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))

    with pytest.raises(ServiceError) as exc:
        service.create_offer(
            {"product_id": product_id, "price": 1000, "quantity": 5},
            {"user_id": str(farmer["_id"]), "role": "farmer"},
        )

    assert exc.value.status_code == 403


def test_expired_offer_cannot_be_responded(db):
    service = build_service(db)
    buyer = db.users.find_one({"role": "buyer"})
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))
    offer_id = _seed_offer(
        db,
        product_id=product_id,
        buyer_id=str(buyer["_id"]),
        farmer_id=str(farmer["_id"]),
        status="pending",
        expires_at=utcnow() - timedelta(minutes=1),
    )

    with pytest.raises(ServiceError) as exc:
        service.respond_offer(
            offer_id,
            {"response": "accepted"},
            {"user_id": str(farmer["_id"]), "role": "farmer"},
        )

    assert exc.value.status_code == 409
    assert "expired" in exc.value.message.lower()
    stored = db.offers.find_one({"_id": to_object_id(offer_id)})
    assert stored["status"] == "expired"


def test_double_acceptance_prevention(db):
    service = build_service(db)
    buyer = db.users.find_one({"role": "buyer"})
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))
    offer_id = _seed_offer(
        db,
        product_id=product_id,
        buyer_id=str(buyer["_id"]),
        farmer_id=str(farmer["_id"]),
    )

    first = service.respond_offer(
        offer_id,
        {"response": "accepted"},
        {"user_id": str(farmer["_id"]), "role": "farmer"},
    )
    assert first["status"] == "accepted"

    with pytest.raises(ServiceError) as exc:
        service.respond_offer(
            offer_id,
            {"response": "accepted"},
            {"user_id": str(farmer["_id"]), "role": "farmer"},
        )
    assert exc.value.status_code == 409
    assert "already accepted" in exc.value.message.lower()


def test_race_condition_simulation_returns_conflict(db, monkeypatch):
    service = build_service(db)
    buyer = db.users.find_one({"role": "buyer"})
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_owned_product(db, str(farmer["_id"]))
    offer_id = _seed_offer(
        db,
        product_id=product_id,
        buyer_id=str(buyer["_id"]),
        farmer_id=str(farmer["_id"]),
    )

    repo = service.offer_repo
    original = repo.respond_offer

    def racey_respond_offer(*args, **kwargs):
        db.offers.update_one(
            {"_id": to_object_id(offer_id)},
            {"$set": {"status": "accepted", "updated_at": utcnow()}},
        )
        return None

    monkeypatch.setattr(repo, "respond_offer", racey_respond_offer)

    with pytest.raises(ServiceError) as exc:
        service.respond_offer(
            offer_id,
            {"response": "accepted"},
            {"user_id": str(farmer["_id"]), "role": "farmer"},
        )
    assert exc.value.status_code == 409
    assert "accepted" in exc.value.message.lower()

    monkeypatch.setattr(repo, "respond_offer", original)
