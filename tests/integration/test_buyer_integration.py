from app.utils.serialization import to_object_id
from app.utils.time_utils import utcnow


def test_login_selector_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login As Admin" in response.data
    assert b"Login As Buyer" in response.data


def test_buyer_signup_and_login(client, db):
    signup = client.post(
        "/api/signup",
        json={
            "name": "Buyer Two",
            "email": "buyer.two@example.com",
            "password": "buyerpass123",
        },
    )
    assert signup.status_code == 201

    user = db.users.find_one({"email": "buyer.two@example.com", "role": "buyer"})
    assert user is not None
    assert user.get("password_hash")
    assert user["password_hash"] != "buyerpass123"

    login = client.post(
        "/api/login",
        json={"email": "buyer.two@example.com", "password": "buyerpass123"},
    )
    assert login.status_code == 200
    payload = login.get_json()
    assert payload["user"]["email"] == "buyer.two@example.com"
    assert payload["user"]["id"] == str(user["_id"])


def test_buyer_end_to_end_flow(client, db):
    now = utcnow()
    buyer = db.users.find_one({"role": "buyer"})
    assert buyer is not None

    product_id = db.products.insert_one(
        {
            "name": "Fresh Onion",
            "description": "Freshly harvested onions from nearby farm.",
            "category": "vegetable",
            "price": 900,
            "status": "approved",
            "isOrganic": True,
            "isFresh": True,
            "farmer": {"name": "Farmer One", "location": "Anand", "rating": 4.7},
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    products_resp = client.get("/api/products")
    assert products_resp.status_code == 200
    products = products_resp.get_json()
    assert any(item["_id"] == str(product_id) for item in products)

    neg_submit = client.post(
        "/api/negotiate/submit",
        json={
            "user_id": str(buyer["_id"]),
            "user_name": buyer["name"],
            "product_id": str(product_id),
            "negotiated_price": 800,
            "message": "Can we close at 800?",
        },
    )
    assert neg_submit.status_code == 201

    neg_list = client.get(f"/api/negotiate/{buyer['_id']}")
    assert neg_list.status_code == 200
    negotiations = neg_list.get_json()
    assert len(negotiations) >= 1
    neg_id = negotiations[0]["_id"]

    add_to_cart = client.post(
        "/api/cart/add",
        json={
            "user_id": str(buyer["_id"]),
            "product_id": str(product_id),
            "quantity": 2,
            "negotiated_price": 800,
            "neg_id": neg_id,
        },
    )
    assert add_to_cart.status_code == 201

    cart_resp = client.get(f"/api/cart/{buyer['_id']}")
    assert cart_resp.status_code == 200
    cart = cart_resp.get_json()
    assert len(cart.get("items", [])) == 1
    assert cart["items"][0]["price"] == 800

    wishlist_toggle = client.post(
        "/api/wishlist/toggle",
        json={"user_id": str(buyer["_id"]), "product_id": str(product_id)},
    )
    assert wishlist_toggle.status_code == 200
    assert wishlist_toggle.get_json()["status"] == "added"

    wishlist_get = client.get(f"/api/wishlist/{buyer['_id']}")
    assert wishlist_get.status_code == 200
    assert len(wishlist_get.get_json()["items"]) == 1

    place_order = client.post(
        "/api/orders/",
        json={
            "user_id": str(buyer["_id"]),
            "address": "IITRAM Campus, Ahmedabad",
            "payment_method": "UPI",
        },
    )
    assert place_order.status_code == 201
    order_payload = place_order.get_json()
    assert order_payload.get("order_number")

    buyer_orders = client.get(f"/api/orders/{buyer['_id']}")
    assert buyer_orders.status_code == 200
    assert len(buyer_orders.get_json()) >= 1

    admin_order = db.orders.find_one({"order_number": order_payload["order_number"]})
    assert admin_order is not None
    assert admin_order.get("source") == "buyer_module"

    txn = db.transactions.find_one({"order_number": order_payload["order_number"]})
    assert txn is not None

    negotiation_doc = db["buyer_Negotiations"].find_one({"_id": to_object_id(neg_id)})
    assert negotiation_doc is None

    cart_after = client.get(f"/api/cart/{buyer['_id']}")
    assert cart_after.status_code == 200
    assert cart_after.get_json().get("items") == []
