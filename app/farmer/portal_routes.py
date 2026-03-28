import re
from pathlib import Path

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from app.utils.time_utils import utcnow


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

GRAIN_CROPS = {"wheat", "rice", "maize", "bajra", "barley", "millet"}
FRUIT_CROPS = {"mango", "banana", "guava", "papaya", "pomegranate", "apple", "orange"}
VEGETABLE_CROPS = {
    "tomato",
    "potato",
    "onion",
    "brinjal",
    "eggplant",
    "cauliflower",
    "peas",
    "carrot",
    "cabbage",
    "chili",
}


farmer_portal_bp = Blueprint(
    "farmer_portal",
    __name__,
    url_prefix="/farmer",
    template_folder="../templates/farmer",
    static_folder="../static/farmer",
    static_url_path="/farmer/static",
)

farmer_public_api_bp = Blueprint("farmer_public_api", __name__, url_prefix="/api")


def _collections():
    db = current_app.db
    return {
        "farmers": db["farmers"],
        "products": db["products"],
        "negotiations": db["buyer_Negotiations"],
    }


def _upload_dir():
    upload_dir = Path(current_app.root_path) / "static" / "farmer" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_farmer_id(name):
    safe_name = re.sub(r"[^a-zA-Z0-9]", "", str(name or "")).upper()[:20]
    return f"FARMER_{safe_name}"


def _get_farmer():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return None
    farmer = _collections()["farmers"].find_one({"farmer_id": farmer_id}, {"_id": 0})
    return farmer


def _crop_category(crop_name):
    token = str(crop_name or "").strip().lower().split()
    key = token[-1] if token else ""
    if key in GRAIN_CROPS:
        return "grain"
    if key in FRUIT_CROPS:
        return "fruit"
    if key in VEGETABLE_CROPS:
        return "vegetable"
    return "vegetable"


def _to_object_id(value):
    try:
        return ObjectId(str(value))
    except Exception:
        return None


@farmer_portal_bp.get("")
@farmer_portal_bp.get("/")
def farmer_role_selection():
    return render_template("farmer/role_selection.html")


@farmer_portal_bp.get("/entry")
def farmer_entry():
    return render_template("farmer/entry.html")


@farmer_portal_bp.post("/entry")
def farmer_entry_login():
    name = str(request.form.get("farmer_name") or "").strip()
    if not name:
        return render_template("farmer/entry.html", error="Please enter your name to continue")

    farmer_id = _safe_farmer_id(name)
    session["farmer_id"] = farmer_id
    session["farmer_name"] = name
    return redirect(url_for("farmer_portal.profile_setup"))


@farmer_portal_bp.get("/profile-setup")
def profile_setup():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("farmer_portal.farmer_entry"))
    if _collections()["farmers"].find_one({"farmer_id": farmer_id}):
        return redirect(url_for("farmer_portal.dashboard"))
    return render_template("farmer/profile_setup.html", farmer_id=farmer_id)


@farmer_portal_bp.post("/profile-setup")
def save_profile():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    required_fields = [
        "name",
        "village",
        "city",
        "state",
        "pincode",
        "crop_types",
        "bank_acc_holder",
        "bank_acc_number",
        "bank_ifsc",
    ]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required"}), 400

    crop_types = data.get("crop_types")
    if not isinstance(crop_types, list) or not crop_types:
        return jsonify({"success": False, "error": "Select at least one crop type"}), 400

    farmer_doc = {
        "farmer_id": farmer_id,
        "name": str(data.get("name")).strip(),
        "location": {
            "village": str(data.get("village")).strip(),
            "city": str(data.get("city")).strip(),
            "state": str(data.get("state")).strip(),
            "pincode": str(data.get("pincode")).strip(),
        },
        "crop_types": crop_types,
        "farm_size": {
            "value": float(data.get("farm_size")) if data.get("farm_size") else None,
            "unit": str(data.get("farm_size_unit") or "acres"),
        },
        "payment": {
            "bank_acc_holder": str(data.get("bank_acc_holder")).strip(),
            "bank_acc_number": str(data.get("bank_acc_number")).strip(),
            "bank_ifsc": str(data.get("bank_ifsc")).strip().upper(),
            "bank_name": str(data.get("bank_name") or "").strip(),
            "upi_id": str(data.get("upi_id") or "").strip(),
        },
        "profile_complete": True,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }

    farmers_col = _collections()["farmers"]
    existing = farmers_col.find_one({"farmer_id": farmer_id})
    if existing:
        farmers_col.update_one({"_id": existing["_id"]}, {"$set": farmer_doc})
    else:
        farmers_col.insert_one(farmer_doc)

    return jsonify({"success": True, "redirect": url_for("farmer_portal.dashboard")})


@farmer_portal_bp.get("/dashboard")
def dashboard():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("farmer_portal.farmer_entry"))

    farmer = _get_farmer()
    if not farmer:
        return redirect(url_for("farmer_portal.profile_setup"))

    raw_products = list(
        _collections()["products"]
        .find(
            {"farmer_id": farmer_id},
            {
                "_id": 1,
                "crop_name": 1,
                "quantity": 1,
                "quantity_unit": 1,
                "price_type": 1,
                "price": 1,
                "harvest_date": 1,
                "min_order_qty": 1,
                "min_order_unit": 1,
                "image_path": 1,
                "is_live": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
    )
    products = []
    for row in raw_products:
        row["id"] = str(row["_id"])
        del row["_id"]
        products.append(row)

    return render_template(
        "farmer/dashboard.html",
        farmer=farmer,
        products=products,
        now_hour=utcnow().hour,
    )


@farmer_portal_bp.get("/new-dashboard")
def new_dashboard():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("farmer_portal.farmer_entry"))

    products = list(_collections()["products"].find({"farmer_id": farmer_id}, {"_id": 1}))
    product_ids = [str(row["_id"]) for row in products]
    raw_offers = list(
        _collections()["negotiations"]
        .find({"product_id": {"$in": product_ids}, "status": "pending"})
        .sort("created_at", -1)
    )

    offers = []
    for row in raw_offers:
        row["id"] = str(row["_id"])
        del row["_id"]
        row["buyer_name"] = row.get("user_name", row.get("buyer_name", "Unknown Buyer"))
        row["crop_name"] = row.get("product_name", row.get("crop_name", "Unknown Product"))
        row["offered_price"] = row.get("negotiated_price", row.get("offered_price", 0))
        row["original_price"] = row.get("original_price", 0)
        row["quantity"] = row.get("quantity", "Custom")
        row["message"] = row.get("message", "")
        offers.append(row)

    return render_template(
        "farmer/farmer_dashboard.html",
        farmer_name=session.get("farmer_name", "Farmer"),
        offers=offers,
    )


@farmer_portal_bp.post("/api/negotiate")
def negotiate_action():
    if not session.get("farmer_id"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    offer_id = data.get("offer_id")
    action = str(data.get("action") or "").strip().lower()
    if not offer_id or not action:
        return jsonify({"success": False, "error": "Missing data"}), 400

    oid = _to_object_id(offer_id)
    if not oid:
        return jsonify({"success": False, "error": "Invalid offer id"}), 400

    negotiations_col = _collections()["negotiations"]

    if action == "reject":
        result = negotiations_col.delete_one({"_id": oid})
        if result.deleted_count == 1:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Offer not found or already changed"}), 404

    if action == "accept":
        update_doc = {"$set": {"status": "accepted", "updated_at": utcnow()}}
    elif action == "counter":
        counter_price = data.get("counter_price")
        try:
            counter_price = float(counter_price)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Missing counter price"}), 400
        update_doc = {
            "$set": {
                "status": "counter_offered",
                "negotiated_price": counter_price,
                "counter_message": str(data.get("counter_message") or "").strip(),
                "updated_at": utcnow(),
            }
        }
    else:
        return jsonify({"success": False, "error": "Invalid action"}), 400

    result = negotiations_col.update_one({"_id": oid}, update_doc)
    if result.matched_count == 0:
        return jsonify({"success": False, "error": "Offer not found or already changed"}), 404
    return jsonify({"success": True})


@farmer_portal_bp.get("/add-product")
def add_product():
    if not _get_farmer():
        return redirect(url_for("farmer_portal.profile_setup"))
    return render_template("farmer/add_product.html", farmer=_get_farmer())


@farmer_portal_bp.post("/add-product")
def save_product():
    farmer_id = session.get("farmer_id")
    farmer = _get_farmer()
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    if not farmer:
        return jsonify({"success": False, "error": "Complete your profile first"}), 403

    crop_name = str(request.form.get("crop_name") or "").strip()
    quantity = str(request.form.get("quantity") or "").strip()
    quantity_unit = str(request.form.get("quantity_unit") or "kg").strip()
    price_type = str(request.form.get("price_type") or "fixed").strip()
    price = str(request.form.get("price") or "").strip()
    harvest_date = str(request.form.get("harvest_date") or "").strip()
    min_order_qty = str(request.form.get("min_order_qty") or "").strip()
    min_order_unit = str(request.form.get("min_order_unit") or "kg").strip()

    errors = {}
    if not crop_name:
        errors["crop_name"] = "Crop name is required"
    if not quantity:
        errors["quantity"] = "Quantity is required"
    if not harvest_date:
        errors["harvest_date"] = "Harvest date is required"
    if not min_order_qty:
        errors["min_order_qty"] = "Minimum order is required"
    if price_type == "fixed" and not price:
        errors["price"] = "Enter a price or choose Negotiable"
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    image_path = None
    file = request.files.get("image")
    if file and file.filename and _allowed_file(file.filename):
        extension = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{farmer_id}_{int(utcnow().timestamp())}.{extension}"
        file.save(_upload_dir() / filename)
        image_path = f"uploads/{filename}"

    category = _crop_category(crop_name)
    normalized_price = float(price) if price and price_type == "fixed" else None
    product_doc = {
        "farmer_id": farmer_id,
        "farmer_name": farmer.get("name"),
        "farmer_location": farmer.get("location", {}),
        "crop_name": crop_name,
        "name": crop_name,
        "category": category,
        "quantity": float(quantity),
        "quantity_unit": quantity_unit,
        "price_type": price_type,
        "price": normalized_price,
        "base_price": normalized_price,
        "status": "approved",
        "harvest_date": harvest_date,
        "min_order_qty": float(min_order_qty),
        "min_order_unit": min_order_unit,
        "image_path": image_path,
        "is_live": True,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    inserted = _collections()["products"].insert_one(product_doc)
    return jsonify(
        {
            "success": True,
            "product_id": str(inserted.inserted_id),
            "redirect": url_for("farmer_portal.dashboard"),
        }
    )


@farmer_portal_bp.post("/product/<product_id>/toggle")
def toggle_product(product_id):
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    oid = _to_object_id(product_id)
    if not oid:
        return jsonify({"success": False, "error": "Invalid product id"}), 400

    products_col = _collections()["products"]
    product = products_col.find_one({"_id": oid, "farmer_id": farmer_id})
    if not product:
        return jsonify({"success": False, "error": "Not found"}), 404

    next_state = not bool(product.get("is_live"))
    products_col.update_one({"_id": oid}, {"$set": {"is_live": next_state, "updated_at": utcnow()}})
    return jsonify({"success": True, "is_live": next_state})


@farmer_portal_bp.post("/product/<product_id>/delete")
def delete_product(product_id):
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    oid = _to_object_id(product_id)
    if not oid:
        return jsonify({"success": False, "error": "Invalid product id"}), 400

    result = _collections()["products"].delete_one({"_id": oid, "farmer_id": farmer_id})
    if result.deleted_count == 0:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


@farmer_portal_bp.get("/logout")
def logout():
    session.clear()
    return render_template("farmer/logged_out.html")


@farmer_public_api_bp.get("/farmer/<farmer_id>")
def get_farmer_profile(farmer_id):
    farmer = _collections()["farmers"].find_one({"farmer_id": farmer_id}, {"_id": 0, "payment": 0})
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify(farmer)
