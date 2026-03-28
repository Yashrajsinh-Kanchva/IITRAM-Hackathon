from flask import Blueprint, jsonify, request

from app.buyer.common import (
    DEFAULT_PRODUCT_IMAGE,
    as_non_empty_string,
    get_collections,
    normalize_product,
    to_object_id,
)


cart_bp = Blueprint("buyer_cart", __name__)


@cart_bp.get("/<user_id>")
def get_cart(user_id):
    cart = get_collections()["cart"].find_one({"user_id": str(user_id)})
    if not cart:
        return jsonify({"user_id": str(user_id), "items": []})
    cart["_id"] = str(cart["_id"])
    return jsonify(cart)


@cart_bp.post("/add")
def add_to_cart():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    product_id = as_non_empty_string(data.get("product_id"))
    quantity = int(data.get("quantity") or 1)

    if not user_id or not product_id:
        return jsonify({"error": "User ID and Product ID are required"}), 400
    if quantity <= 0:
        return jsonify({"error": "quantity must be > 0"}), 400

    cols = get_collections()
    product = cols["products"].find_one({"_id": to_object_id(product_id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    normalized = normalize_product(product)

    negotiated_price = data.get("negotiated_price")
    neg_id = data.get("neg_id")
    final_price = (
        float(negotiated_price)
        if negotiated_price is not None
        else float(normalized.get("price") or 0)
    )
    if final_price <= 0:
        return jsonify({"error": "invalid product price"}), 400

    item = {
        "product_id": str(product["_id"]),
        "name": normalized["name"],
        "price": final_price,
        "quantity": quantity,
        "image": normalized.get("image_url") or DEFAULT_PRODUCT_IMAGE,
        "neg_id": str(neg_id) if neg_id else None,
    }

    cart_col = cols["cart"]
    cart = cart_col.find_one({"user_id": user_id})
    if cart:
        items = cart.get("items", [])
        found = False
        for existing in items:
            if existing.get("product_id") == item["product_id"]:
                existing["quantity"] = int(existing.get("quantity", 0)) + quantity
                if item.get("neg_id"):
                    existing["neg_id"] = item["neg_id"]
                existing["price"] = item["price"]
                found = True
                break
        if not found:
            items.append(item)
        cart_col.update_one({"user_id": user_id}, {"$set": {"items": items}})
    else:
        cart_col.insert_one({"user_id": user_id, "items": [item]})

    return jsonify({"message": "Item added to cart"}), 201


@cart_bp.post("/remove")
def remove_from_cart():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    product_id = as_non_empty_string(data.get("product_id"))
    get_collections()["cart"].update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}},
    )
    return jsonify({"message": "Item removed from cart"})


@cart_bp.post("/update")
def update_cart_quantity():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    product_id = as_non_empty_string(data.get("product_id"))
    new_quantity = int(data.get("quantity") or 0)

    if new_quantity <= 0:
        get_collections()["cart"].update_one(
            {"user_id": user_id},
            {"$pull": {"items": {"product_id": product_id}}},
        )
        return jsonify({"message": "Item removed from cart"})

    get_collections()["cart"].update_one(
        {"user_id": user_id, "items.product_id": product_id},
        {"$set": {"items.$.quantity": new_quantity}},
    )
    return jsonify({"message": "Quantity updated"})
