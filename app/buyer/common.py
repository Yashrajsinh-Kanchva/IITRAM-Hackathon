from datetime import datetime
import re
from typing import Any

from bson import ObjectId
from flask import current_app

from app.utils.time_utils import utcnow


DEFAULT_PRODUCT_IMAGE = "/buyer/images/placeholders/farm-default.jpg"

CATEGORY_IMAGE_FALLBACKS = {
    "vegetable": "/buyer/images/placeholders/vegetables-default.jpg",
    "fruit": "/buyer/images/placeholders/fruits-default.jpg",
    "grain": "/buyer/images/placeholders/grains-default.jpg",
    "pulse": "/buyer/images/placeholders/pulses-default.jpg",
    "spice": "/buyer/images/placeholders/spices-default.jpg",
    "cash_crop": "/buyer/images/placeholders/farm-default.jpg",
    "honey": "/buyer/images/placeholders/farm-default.jpg",
    "dairy": "/buyer/images/placeholders/farm-default.jpg",
    "farm": DEFAULT_PRODUCT_IMAGE,
}

CATEGORY_ALIASES = {
    "vegetables": "vegetable",
    "fruits": "fruit",
    "grains": "grain",
    "grain": "grain",
    "cereals": "grain",
    "cereal": "grain",
    "pulses": "pulse",
    "pulse": "pulse",
    "dal": "pulse",
    "lentils": "pulse",
    "spices": "spice",
    "spice": "spice",
    "cash crop": "cash_crop",
    "cash-crop": "cash_crop",
    "cashcrop": "cash_crop",
}

CROP_QUERY_MAP = {
    "tomato": "tomato,vegetable,farm",
    "potato": "potato,vegetable,farm",
    "onion": "onion,vegetable,farm",
    "brinjal": "brinjal,eggplant,farm",
    "cauliflower": "cauliflower,vegetable,farm",
    "cabbage": "cabbage,vegetable,farm",
    "carrot": "carrot,vegetable,farm",
    "spinach": "spinach,leafy,vegetable",
    "peas": "green peas,vegetable,farm",
    "cucumber": "cucumber,vegetable,farm",
    "bitter gourd": "bitter gourd,vegetable,farm",
    "bottle gourd": "bottle gourd,vegetable,farm",
    "capsicum": "capsicum,bell pepper,vegetable",
    "garlic": "garlic,vegetable,farm",
    "ginger": "ginger,root,farm",
    "okra": "okra,ladyfinger,farm",
    "radish": "radish,vegetable,farm",
    "beetroot": "beetroot,vegetable,farm",
    "mango": "mango,fruit,farm",
    "banana": "banana,fruit,farm",
    "apple": "apple,fruit,farm",
    "grapes": "grapes,fruit,farm",
    "watermelon": "watermelon,fruit,farm",
    "papaya": "papaya,fruit,farm",
    "pomegranate": "pomegranate,fruit,farm",
    "guava": "guava,fruit,farm",
    "lemon": "lemon,citrus,fruit",
    "orange": "orange,citrus,fruit",
    "pineapple": "pineapple,fruit,farm",
    "strawberry": "strawberry,fruit,farm",
    "coconut": "coconut,farm,fruit",
    "chikoo": "chikoo,sapota,fruit",
    "wheat": "wheat,grain,field",
    "rice": "rice,paddy,grain,field",
    "barley": "barley,grain,field",
    "maize": "maize,corn,grain,field",
    "corn": "corn,maize,grain,field",
    "jowar": "jowar,sorghum,grain",
    "bajra": "bajra,pearl millet,grain",
    "ragi": "ragi,finger millet,grain",
    "oats": "oats,grain,field",
    "lentils": "lentils,dal,pulses",
    "chickpeas": "chickpeas,chana,pulses",
    "moong": "moong,green gram,pulses",
    "urad": "urad,black gram,pulses",
    "toor": "toor dal,pigeon pea,pulses",
    "rajma": "rajma,kidney beans,pulses",
    "soybean": "soybean,pulses,farm",
    "turmeric": "turmeric,spice,farm",
    "chilli": "red chilli,spice,farm",
    "coriander": "coriander,spice,seed",
    "cumin": "cumin,jeera,spice",
    "pepper": "black pepper,spice",
    "cardamom": "cardamom,elaichi,spice",
    "mustard": "mustard,spice,seed",
    "fenugreek": "fenugreek,methi,spice",
    "cotton": "cotton,cash crop,farm",
    "sugarcane": "sugarcane,cash crop,farm",
    "groundnut": "groundnut,peanut,crop",
    "sunflower": "sunflower,cash crop,farm",
    "jute": "jute,cash crop,farm",
}

CROP_ALIASES = {
    "tomatoes": "tomato",
    "onions": "onion",
    "potatoes": "potato",
    "eggplant": "brinjal",
    "aubergine": "brinjal",
    "ladyfinger": "okra",
    "lady finger": "okra",
    "bhindi": "okra",
    "lauki": "bottle gourd",
    "karela": "bitter gourd",
    "chili": "chilli",
    "chilies": "chilli",
    "chillies": "chilli",
    "dal": "lentils",
    "chana": "chickpeas",
    "kabuli chana": "chickpeas",
    "chick pea": "chickpeas",
    "chick peas": "chickpeas",
    "arhar": "toor",
    "toor dal": "toor",
    "pigeon pea": "toor",
    "masoor": "lentils",
    "red lentil": "lentils",
    "black gram": "urad",
    "green gram": "moong",
    "kidney beans": "rajma",
    "jeera": "cumin",
    "methi": "fenugreek",
    "sapota": "chikoo",
    "sorghum": "jowar",
    "finger millet": "ragi",
    "sweet corn": "maize",
    "peanut": "groundnut",
    "peanuts": "groundnut",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())).strip()


def _make_unsplash_url(query: str) -> str:
    clean = str(query or "").replace(" ", "+").strip("+")
    if not clean:
        clean = "farm,produce,agriculture"
    return f"https://source.unsplash.com/400x300/?{clean}"


def _canonical_crop(crop_name: Any) -> str:
    text = _normalize_text(crop_name)
    if not text:
        return ""

    for alias in sorted(CROP_ALIASES, key=len, reverse=True):
        if alias in text:
            return CROP_ALIASES[alias]

    for key in sorted(CROP_QUERY_MAP, key=len, reverse=True):
        if key in text:
            return key
    return ""


def _resolve_uploaded_image(product: dict) -> str:
    raw_image = str(product.get("image_url") or product.get("image_path") or "").strip()
    if not raw_image:
        return ""
    if raw_image.startswith("uploads/"):
        return f"/farmer/static/{raw_image}"
    if raw_image.startswith("/uploads/"):
        return f"/farmer/static/{raw_image.lstrip('/')}"
    if raw_image.startswith("/farmer/static/"):
        return raw_image
    if raw_image.startswith(("http://", "https://")):
        return raw_image
    if raw_image.startswith("/"):
        return raw_image
    return f"/{raw_image.lstrip('/')}"


def suggest_crop_image_url(crop_name: Any, category: str) -> str:
    canonical = _canonical_crop(crop_name)
    if canonical and CROP_QUERY_MAP.get(canonical):
        return _make_unsplash_url(CROP_QUERY_MAP[canonical])
    normalized_category = normalize_category(category or "")
    return CATEGORY_IMAGE_FALLBACKS.get(normalized_category, DEFAULT_PRODUCT_IMAGE)


def infer_category_from_product(product: dict) -> str:
    text = " ".join(
        str(part or "").strip().lower()
        for part in (
            product.get("category"),
            product.get("crop_name"),
            product.get("name"),
            product.get("description"),
        )
    )
    if not text:
        return ""
    if "honey" in text or "madhu" in text:
        return "honey"
    if any(token in text for token in ("milk", "dairy", "paneer", "curd", "ghee", "butter", "cheese", "yogurt")):
        return "dairy"
    if any(token in text for token in ("mango", "banana", "apple", "orange", "grape", "papaya", "guava", "fruit")):
        return "fruit"
    if any(token in text for token in ("wheat", "rice", "maize", "grain", "millet", "barley", "bajra", "jowar")):
        return "grain"
    if any(token in text for token in ("lentil", "dal", "chickpea", "chana", "moong", "urad", "rajma", "pulse", "soybean")):
        return "pulse"
    if any(token in text for token in ("turmeric", "chilli", "chili", "coriander", "cumin", "pepper", "cardamom", "mustard", "fenugreek", "spice")):
        return "spice"
    if any(token in text for token in ("cotton", "sugarcane", "groundnut", "sunflower", "jute", "cash crop")):
        return "cash_crop"
    if any(
        token in text
        for token in (
            "tomato",
            "onion",
            "potato",
            "brinjal",
            "eggplant",
            "cabbage",
            "carrot",
            "cauliflower",
            "peas",
            "vegetable",
        )
    ):
        return "vegetable"
    return ""


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
    value = _normalize_text(category)
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
    inferred_category = infer_category_from_product(out)
    out["category"] = normalize_category(out.get("category") or inferred_category or "all")

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

    out["image_url"] = _resolve_uploaded_image(out)
    out["suggested_image_url"] = suggest_crop_image_url(
        out.get("crop_name") or out.get("name"),
        out["category"],
    )
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
