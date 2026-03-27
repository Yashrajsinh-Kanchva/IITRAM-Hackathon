from datetime import timedelta

from app.utils.serialization import to_object_id
from app.utils.time_utils import utcnow


def _headers(user_id, role):
    return {
        "X-User-Id": str(user_id),
        "X-User-Role": role,
        "X-CSRFToken": "test-token",
    }


def _seed_product(db, farmer_id):
    result = db.products.insert_one(
        {
            "name": "Potato",
            "category": "vegetable",
            "price": 1500,
            "status": "approved",
            "farmer_id": str(farmer_id),
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    )
    return str(result.inserted_id)


def test_offer_api_valid_creation(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    buyer = db.users.find_one({"role": "buyer"})
    product_id = _seed_product(db, farmer["_id"])

    resp = client.post(
        "/offers",
        json={"product_id": product_id, "price": 1200, "quantity": 9},
        headers=_headers(buyer["_id"], "buyer"),
    )

    assert resp.status_code == 201
    payload = resp.get_json()
    assert payload["item"]["status"] == "pending"
    assert payload["item"]["product_id"] == product_id


def test_offer_api_invalid_price(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    buyer = db.users.find_one({"role": "buyer"})
    product_id = _seed_product(db, farmer["_id"])

    resp = client.post(
        "/offers",
        json={"product_id": product_id, "price": -1, "quantity": 9},
        headers=_headers(buyer["_id"], "buyer"),
    )
    assert resp.status_code == 400
    assert "price" in resp.get_json()["error"]


def test_offer_api_unauthorized_user(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    product_id = _seed_product(db, farmer["_id"])

    resp = client.post(
        "/offers",
        json={"product_id": product_id, "price": 1200, "quantity": 9},
        headers=_headers(farmer["_id"], "farmer"),
    )
    assert resp.status_code == 403


def test_offer_api_expired_offer_response(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    buyer = db.users.find_one({"role": "buyer"})
    product_id = _seed_product(db, farmer["_id"])
    offer_id = db.offers.insert_one(
        {
            "product_id": product_id,
            "buyer_id": str(buyer["_id"]),
            "farmer_id": str(farmer["_id"]),
            "price": 1000.0,
            "quantity": 10,
            "status": "pending",
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "expires_at": utcnow() - timedelta(minutes=1),
            "history": [
                {
                    "event": "created",
                    "actor_id": str(buyer["_id"]),
                    "actor_role": "buyer",
                    "price": 1000.0,
                    "quantity": 10,
                    "at": utcnow(),
                }
            ],
        }
    ).inserted_id

    resp = client.patch(
        f"/offers/{offer_id}/respond",
        json={"response": "accepted"},
        headers=_headers(farmer["_id"], "farmer"),
    )
    assert resp.status_code == 409
    assert "expired" in resp.get_json()["error"].lower()


def test_offer_api_double_acceptance_prevention(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    buyer = db.users.find_one({"role": "buyer"})
    product_id = _seed_product(db, farmer["_id"])

    create_resp = client.post(
        "/offers",
        json={"product_id": product_id, "price": 1800, "quantity": 20},
        headers=_headers(buyer["_id"], "buyer"),
    )
    offer_id = create_resp.get_json()["item"]["id"]

    first = client.patch(
        f"/offers/{offer_id}/respond",
        json={"response": "accepted"},
        headers=_headers(farmer["_id"], "farmer"),
    )
    assert first.status_code == 200

    second = client.patch(
        f"/offers/{offer_id}/respond",
        json={"response": "accepted"},
        headers=_headers(farmer["_id"], "farmer"),
    )
    assert second.status_code == 409
    assert "accepted" in second.get_json()["error"].lower()


def test_offer_api_race_condition_simulation(client, db):
    farmer = db.users.find_one({"role": "farmer"})
    buyer = db.users.find_one({"role": "buyer"})
    product_id = _seed_product(db, farmer["_id"])

    create_resp = client.post(
        "/offers",
        json={"product_id": product_id, "price": 1800, "quantity": 20},
        headers=_headers(buyer["_id"], "buyer"),
    )
    offer_id = create_resp.get_json()["item"]["id"]

    db.offers.update_one(
        {"_id": to_object_id(offer_id)},
        {"$set": {"status": "accepted", "updated_at": utcnow()}},
    )

    conflict = client.patch(
        f"/offers/{offer_id}/respond",
        json={"response": "rejected"},
        headers=_headers(farmer["_id"], "farmer"),
    )
    assert conflict.status_code == 409
