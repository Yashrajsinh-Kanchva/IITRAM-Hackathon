from uuid import uuid4

from flask import Blueprint, jsonify, request

from app.buyer.common import as_non_empty_string, get_collections, now, serialize_datetime, to_object_id


orders_bp = Blueprint("buyer_orders", __name__)


@orders_bp.post("/")
def place_order():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    address = as_non_empty_string(data.get("address"))
    payment_method = as_non_empty_string(data.get("payment_method"))

    if not user_id or not address or not payment_method:
        return (
            jsonify({"error": "User ID, address, and payment method are required"}),
            400,
        )

    cols = get_collections()
    cart = cols["cart"].find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        return jsonify({"error": "Cart is empty"}), 400

    items = cart["items"]
    total_price = sum(
        float(item.get("price", 0) or 0) * int(item.get("quantity", 0) or 0)
        for item in items
    )
    if total_price <= 0:
        return jsonify({"error": "Cart total must be greater than zero"}), 400

    timestamp = now()
    buyer_order = {
        "user_id": user_id,
        "items": items,
        "total_price": round(total_price, 2),
        "address": address,
        "payment_method": payment_method,
        "status": "placed",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    order_id = cols["orders"].insert_one(buyer_order).inserted_id

    # Mirror into core admin-visible collections for integrated monitoring.
    user_doc = cols["users"].find_one({"_id": to_object_id(user_id)})
    order_number = f"BORD-{timestamp.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    cols["admin_orders"].insert_one(
        {
            "order_number": order_number,
            "buyer_name": (user_doc or {}).get("name") or "Buyer",
            "buyer_email": (user_doc or {}).get("email"),
            "buyer_id": user_id,
            "status": "pending",
            "total_amount": round(total_price, 2),
            "total_price": round(total_price, 2),
            "quantity": sum(int(item.get("quantity", 0) or 0) for item in items),
            "delivery_address": address,
            "source": "buyer_module",
            "source_order_id": str(order_id),
            "items": items,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    payment_status = "pending" if payment_method.lower() == "cod" else "paid"
    cols["transactions"].insert_one(
        {
            "transaction_ref": f"BTXN-{uuid4().hex[:12].upper()}",
            "order_number": order_number,
            "amount": round(total_price, 2),
            "payment_status": payment_status,
            "review_state": "pending_review",
            "gateway": payment_method.lower(),
            "source": "buyer_module",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )

    cols["cart"].delete_one({"user_id": user_id})
    for purchased_item in items:
        neg_id = purchased_item.get("neg_id")
        oid = to_object_id(neg_id) if neg_id else None
        if oid:
            cols["negotiations"].delete_one({"_id": oid})

    return (
        jsonify(
            {
                "message": "Order placed successfully",
                "order_id": str(order_id),
                "order_number": order_number,
            }
        ),
        201,
    )


@orders_bp.get("/<user_id>")
def get_orders(user_id):
    rows = list(
        get_collections()["orders"].find({"user_id": str(user_id)}).sort("created_at", -1)
    )
    for row in rows:
        row["_id"] = str(row["_id"])
        row["created_at"] = serialize_datetime(row.get("created_at"))
        row["updated_at"] = serialize_datetime(row.get("updated_at"))
    return jsonify(rows)
