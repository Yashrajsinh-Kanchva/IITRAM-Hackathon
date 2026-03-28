from datetime import datetime
from typing import Any

from bson import ObjectId
from flask import current_app

from app.utils.time_utils import utcnow


DEFAULT_PRODUCT_IMAGE = (
    "https://images.unsplash.com/photo-1592841200221-a6898f307bac?q=80&w=400"
)

CATEGORY_ALIASES = {
    "vegetables": "vegetable",
    "fruits": "fruit",
    "grains": "grain",
}


def get_collections():
    db = current_app.db
    return {
        "users": db.users,
        "products": db.products,
        "cart": db["buyer_Cart"],
        "orders": db["buyer_Orders"],
        "negotiations": db["buyer_Negotiations"],
        "wishlist": db["buyer_Wishlist"],
        "legacy_users": db["buyer_Users"],
        "admin_orders": db.orders,
        "transactions": db.transactions,
    }


def normalize_category(category: str) -> str:
    value = str(category or "").strip().lower()
    return CATEGORY_ALIASES.get(value, value)


def parse_bool_arg(value: Any):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def to_object_id(value: Any):
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def normalize_product(product):
    if not product:
        return None

    out = {**product}
    out["_id"] = str(out.get("_id"))
    out["id"] = out["_id"]
    out["name"] = out.get("name", out.get("crop_name", "Fresh Harvest"))
    out["category"] = out.get("category", "all")

    farmer_loc = out.get("farmer_location", {})
    loc_str = (
        farmer_loc.get("state", "Gujarat")
        if isinstance(farmer_loc, dict)
        else str(farmer_loc or "Gujarat")
    )

    if "farmer" not in out or not isinstance(out["farmer"], dict):
        out["farmer"] = {
            "name": out.get("farmer_name", "Verified Local Farmer"),
            "location": loc_str,
            "rating": out.get("rating", 4.8),
        }

    image = out.get("image_url") or out.get("image_path")
    out["image_url"] = image if image else DEFAULT_PRODUCT_IMAGE
    out["isOrganic"] = bool(out.get("isOrganic", True))
    out["isFresh"] = bool(out.get("isFresh", True))
    out["price"] = out.get("price", out.get("base_price", 0))
    out["quantity"] = out.get("quantity", out.get("stock_qty", out.get("stock", 100)))
    out["description"] = out.get(
        "description",
        f"Fresh {out['name']} directly harvested from {loc_str}.",
    )
    return out


def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def as_non_empty_string(value):
    text = str(value or "").replace("\x00", "").strip()
    return text


def now():
    return utcnow()
