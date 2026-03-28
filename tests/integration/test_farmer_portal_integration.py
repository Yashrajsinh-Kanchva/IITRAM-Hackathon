from app.utils.serialization import to_object_id
from app.utils.time_utils import utcnow


def _bootstrap_farmer_session(client, name="Farmer Test"):
    response = client.post(
        "/farmer/entry",
        data={"farmer_name": name},
        follow_redirects=False,
    )
    assert response.status_code in {302, 303}


def _complete_profile(client):
    payload = {
        "name": "Farmer Test",
        "village": "Village A",
        "city": "City A",
        "state": "Gujarat",
        "pincode": "380001",
        "crop_types": ["Tomato", "Onion"],
        "farm_size": 3,
        "farm_size_unit": "acres",
        "bank_acc_holder": "Farmer Test",
        "bank_acc_number": "123456789012",
        "bank_ifsc": "SBIN0001234",
        "bank_name": "State Bank",
        "upi_id": "farmer@testupi",
    }
    response = client.post("/farmer/profile-setup", json=payload)
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_farmer_role_selection_page(client):
    response = client.get("/farmer")
    assert response.status_code == 200
    assert b"I am a Farmer" in response.data
    assert b"I am a Buyer" in response.data


def test_farmer_profile_setup_and_product_flow(client, db):
    _bootstrap_farmer_session(client)
    _complete_profile(client)

    add_product = client.post(
        "/farmer/add-product",
        data={
            "crop_name": "Tomato",
            "quantity": "100",
            "quantity_unit": "kg",
            "price_type": "fixed",
            "price": "25",
            "harvest_date": "2026-04-10",
            "min_order_qty": "10",
            "min_order_unit": "kg",
        },
    )
    assert add_product.status_code == 200
    payload = add_product.get_json()
    assert payload["success"] is True
    product_id = payload["product_id"]

    product_doc = db.products.find_one({"_id": to_object_id(product_id)})
    assert product_doc is not None
    assert product_doc["crop_name"] == "Tomato"
    assert product_doc["name"] == "Tomato"
    assert product_doc["category"] == "vegetable"

    dashboard = client.get("/farmer/dashboard")
    assert dashboard.status_code == 200
    assert b"My Listed Products" in dashboard.data

    toggle = client.post(f"/farmer/product/{product_id}/toggle")
    assert toggle.status_code == 200
    assert toggle.get_json()["success"] is True

    delete = client.post(f"/farmer/product/{product_id}/delete")
    assert delete.status_code == 200
    assert delete.get_json()["success"] is True


def test_farmer_negotiation_actions(client, db):
    _bootstrap_farmer_session(client, name="Farmer Negotiator")
    _complete_profile(client)

    product_id = db.products.insert_one(
        {
            "farmer_id": "FARMER_FARMERNEGOTIATOR",
            "crop_name": "Onion",
            "name": "Onion",
            "category": "vegetable",
            "quantity": 50,
            "quantity_unit": "kg",
            "price_type": "fixed",
            "price": 30,
            "status": "approved",
            "is_live": True,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    ).inserted_id

    offer_id = db["buyer_Negotiations"].insert_one(
        {
            "user_id": "buyer-1",
            "user_name": "Buyer One",
            "product_id": str(product_id),
            "product_name": "Onion",
            "original_price": 30,
            "negotiated_price": 25,
            "message": "Can you reduce price?",
            "status": "pending",
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    ).inserted_id

    counter = client.post(
        "/farmer/api/negotiate",
        json={
            "offer_id": str(offer_id),
            "action": "counter",
            "counter_price": 28,
            "counter_message": "Best I can do",
        },
    )
    assert counter.status_code == 200
    assert counter.get_json()["success"] is True
    updated = db["buyer_Negotiations"].find_one({"_id": offer_id})
    assert updated["status"] == "counter_offered"
    assert float(updated["negotiated_price"]) == 28.0

    accept = client.post(
        "/farmer/api/negotiate",
        json={"offer_id": str(offer_id), "action": "accept"},
    )
    assert accept.status_code == 200
    assert accept.get_json()["success"] is True
    accepted_doc = db["buyer_Negotiations"].find_one({"_id": offer_id})
    assert accepted_doc["status"] == "accepted"

    reject_offer_id = db["buyer_Negotiations"].insert_one(
        {
            "user_id": "buyer-2",
            "user_name": "Buyer Two",
            "product_id": str(product_id),
            "product_name": "Onion",
            "original_price": 30,
            "negotiated_price": 26,
            "message": "Another offer",
            "status": "pending",
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    ).inserted_id

    reject = client.post(
        "/farmer/api/negotiate",
        json={"offer_id": str(reject_offer_id), "action": "reject"},
    )
    assert reject.status_code == 200
    assert reject.get_json()["success"] is True
    assert db["buyer_Negotiations"].find_one({"_id": reject_offer_id}) is None


def test_public_farmer_profile_api_hides_payment(client, db):
    db["farmers"].insert_one(
        {
            "farmer_id": "FARMER_PUBLIC01",
            "name": "Public Farmer",
            "location": {
                "village": "Village B",
                "city": "City B",
                "state": "Gujarat",
                "pincode": "380002",
            },
            "crop_types": ["Wheat"],
            "payment": {
                "bank_acc_holder": "Public Farmer",
                "bank_acc_number": "1234567890",
                "bank_ifsc": "SBIN0009999",
            },
            "profile_complete": True,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    )

    response = client.get("/api/farmer/FARMER_PUBLIC01")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["farmer_id"] == "FARMER_PUBLIC01"
    assert "payment" not in payload
