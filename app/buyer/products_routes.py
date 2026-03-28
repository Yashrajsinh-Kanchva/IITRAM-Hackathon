from flask import Blueprint, jsonify, request

from app.buyer.common import (
    get_collections,
    normalize_category,
    normalize_product,
    parse_bool_arg,
    to_object_id,
)


products_bp = Blueprint("buyer_products", __name__)


@products_bp.get("")
@products_bp.get("/")
def get_products():
    search = (request.args.get("search") or "").strip()
    category = normalize_category(request.args.get("category", "all"))
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    organic = parse_bool_arg(request.args.get("organic"))
    fresh = parse_bool_arg(request.args.get("fresh"))

    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if category and category != "all":
        query["category"] = {"$in": [category, f"{category}s"]}
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if organic is True:
        query["isOrganic"] = True
    if fresh is True:
        query["isFresh"] = True

    docs = list(get_collections()["products"].find(query).sort("created_at", -1))
    return jsonify([normalize_product(doc) for doc in docs])


@products_bp.get("/<product_id>")
def get_product(product_id):
    oid = to_object_id(product_id)
    if not oid:
        return jsonify({"error": "Invalid Product ID"}), 400

    product = get_collections()["products"].find_one({"_id": oid})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(normalize_product(product))
