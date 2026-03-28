from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime
from bson import ObjectId
import os, json

app = Flask(__name__)
app.secret_key = "farmer_hackathon_secret_2024"

# Upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# ─── MongoDB Connection ────────────────────────────────────────────────────────
# Paste your MongoDB Atlas URI here, or use local MongoDB
# Get Atlas URI from: https://cloud.mongodb.com → Connect → Drivers
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/farm_to_market?retryWrites=true&w=majority")
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)
db           = client["farm_to_market"]
farmers_col  = db["farmers"]
products_col = db["products"]
buyer_Negotiation_col = db["buyer_Negotiations"]

try:
    farmers_col.create_index("farmer_id", unique=True)
    products_col.create_index("farmer_id")
    products_col.create_index("is_live")
except Exception:
    pass


# ─── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_farmer():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return None
    return farmers_col.find_one({"farmer_id": farmer_id}, {"_id": 0})


# ─── Role Selection (Splash Page) ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("role_selection.html")

@app.route("/entry", methods=["GET"])
def entry():
    return render_template("entry.html")


@app.route("/entry", methods=["POST"])
def entry_login():
    name = request.form.get("farmer_name", "").strip()
    if not name:
        return render_template("entry.html", error="Please enter your name to continue")
    # Generate a unique farmer_id from name (safe for demo)
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9]', '', name).upper()[:20]
    farmer_id = f"FARMER_{safe_name}"
    session["farmer_id"]   = farmer_id
    session["farmer_name"] = name
    return redirect(url_for("profile_setup"))


# ─── Profile Setup ─────────────────────────────────────────────────────────────

@app.route("/farmer/profile-setup", methods=["GET"])
def profile_setup():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("entry"))
    if farmers_col.find_one({"farmer_id": farmer_id}):
        return redirect(url_for("dashboard"))
    return render_template("profile_setup.html", farmer_id=farmer_id)


@app.route("/farmer/profile-setup", methods=["POST"])
def save_profile():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400

    required = ["name", "village", "city", "state", "pincode",
                "crop_types", "bank_acc_holder", "bank_acc_number", "bank_ifsc"]
    for field in required:
        if not data.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required"}), 400

    if not isinstance(data["crop_types"], list) or len(data["crop_types"]) == 0:
        return jsonify({"success": False, "error": "Select at least one crop type"}), 400

    farmer_doc = {
        "farmer_id":  farmer_id,
        "name":       data["name"].strip(),
        "location": {
            "village": data["village"].strip(),
            "city":    data["city"].strip(),
            "state":   data["state"].strip(),
            "pincode": data["pincode"].strip(),
        },
        "crop_types": data["crop_types"],
        "farm_size": {
            "value": float(data["farm_size"]) if data.get("farm_size") else None,
            "unit":  data.get("farm_size_unit", "acres"),
        },
        "payment": {
            "bank_acc_holder": data["bank_acc_holder"].strip(),
            "bank_acc_number": data["bank_acc_number"].strip(),
            "bank_ifsc":       data["bank_ifsc"].strip().upper(),
            "bank_name":       data.get("bank_name", "").strip(),
            "upi_id":          data.get("upi_id", "").strip(),
        },
        "profile_complete": True,
        "created_at": datetime.utcnow(),
    }
    try:
        farmers_col.insert_one(farmer_doc)
        return jsonify({"success": True, "redirect": url_for("dashboard")})
    except Exception as e:
        if "duplicate key" in str(e).lower():
            return jsonify({"success": False, "error": "Profile already exists"}), 409
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/farmer/dashboard")
def dashboard():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("entry"))
    farmer = farmers_col.find_one({"farmer_id": farmer_id}, {"_id": 0})
    if not farmer:
        return redirect(url_for("profile_setup"))

    # Fetch this farmer's products
    raw_products = list(products_col.find(
        {"farmer_id": farmer_id},
        {"_id": 1, "crop_name": 1, "quantity": 1, "quantity_unit": 1,
         "price_type": 1, "price": 1, "harvest_date": 1, "min_order_qty": 1,
         "min_order_unit": 1, "image_path": 1, "is_live": 1, "created_at": 1}
    ).sort("created_at", -1))

    # Convert ObjectId → string for template
    products = []
    for p in raw_products:
        p["id"] = str(p["_id"])
        del p["_id"]
        products.append(p)

    return render_template("dashboard.html", farmer=farmer, products=products,
                           now_hour=datetime.utcnow().hour)


@app.route("/farmer/new-dashboard")
def new_dashboard():
    # Renders the new standalone dashboard we just built
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return redirect(url_for("entry"))
        
    # Since teammate's DB schema didn't include farmer_id in buyer_Negotiations,
    # we must find all products belonging to this farmer, extract string IDs, and join natively.
    farmer_products = list(products_col.find({"farmer_id": farmer_id}))
    product_ids = [str(p["_id"]) for p in farmer_products]
    
    raw_offers = list(buyer_Negotiation_col.find(
        {"product_id": {"$in": product_ids}, "status": "pending"}
    ).sort("created_at", -1))
    
    offers = []
    for raw in raw_offers:
        raw["id"] = str(raw["_id"])
        del raw["_id"]
        
        # Robustly bridge the variable names requested by the teammate's database 
        raw["buyer_name"] = raw.get("user_name", raw.get("buyer_name", "Unknown Buyer"))
        raw["crop_name"] = raw.get("product_name", raw.get("crop_name", "Unknown Product"))
        raw["offered_price"] = raw.get("negotiated_price", raw.get("offered_price", 0))
        raw["original_price"] = raw.get("original_price", 0)
        raw["quantity"] = raw.get("quantity", "Custom") # Teammate didn't provide this uniformly!
        raw["message"] = raw.get("message", "")
        
        offers.append(raw)
        
    farmer_name = session.get("farmer_name", "Farmer")
    return render_template("farmer_dashboard.html", farmer_name=farmer_name, offers=offers)


@app.route("/farmer/api/negotiate", methods=["POST"])
def negotiate_action():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    data = request.get_json()
    offer_id = data.get("offer_id")
    action = data.get("action")  # 'accept', 'reject', 'counter'
    counter_price = data.get("counter_price")
    counter_message = data.get("counter_message", "")

    if not offer_id or not action:
        return jsonify({"success": False, "error": "Missing data"}), 400

    update_doc = {}
    if action == "accept":
        update_doc = {"$set": {"status": "accepted"}}
    elif action == "reject":
        pass # Will be handled as a physical DB deletion below
    elif action == "counter":
        if not counter_price:
            return jsonify({"success": False, "error": "Missing counter price"}), 400
        from numbers import Number
        update_doc = {"$set": {"status": "counter_offered", "negotiated_price": float(counter_price), "counter_message": counter_message}}
    else:
        return jsonify({"success": False, "error": "Invalid action"}), 400

    try:
        from bson import ObjectId
        # Cannot filter by farmer_id here because teammate forgot to include it in their buyer_Negotiations dataset! 
        if action == "reject":
            res = buyer_Negotiation_col.delete_one({"_id": ObjectId(offer_id)})
            if res.deleted_count == 1:
                return jsonify({"success": True})
        else:
            res = buyer_Negotiation_col.update_one(
                {"_id": ObjectId(offer_id)},
                update_doc
            )
            if res.modified_count == 1:
                return jsonify({"success": True})
                
        return jsonify({"success": False, "error": "Offer not found or already changed"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Add Product ───────────────────────────────────────────────────────────────

@app.route("/farmer/add-product", methods=["GET"])
def add_product():
    farmer = get_farmer()
    if not farmer:
        return redirect(url_for("profile_setup"))
    return render_template("add_product.html", farmer=farmer)


@app.route("/farmer/add-product", methods=["POST"])
def save_product():
    farmer_id = session.get("farmer_id")
    if not farmer_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    farmer = farmers_col.find_one({"farmer_id": farmer_id})
    if not farmer:
        return jsonify({"success": False, "error": "Complete your profile first"}), 403

    # ── Form fields
    crop_name     = request.form.get("crop_name", "").strip()
    quantity      = request.form.get("quantity", "").strip()
    quantity_unit = request.form.get("quantity_unit", "kg").strip()
    price_type    = request.form.get("price_type", "fixed").strip()
    price         = request.form.get("price", "").strip()
    harvest_date  = request.form.get("harvest_date", "").strip()
    min_order_qty = request.form.get("min_order_qty", "").strip()
    min_order_unit= request.form.get("min_order_unit", "kg").strip()

    # Validate required
    errors = {}
    if not crop_name:           errors["crop_name"]    = "Crop name is required"
    if not quantity:            errors["quantity"]     = "Quantity is required"
    if not harvest_date:        errors["harvest_date"] = "Harvest date is required"
    if not min_order_qty:       errors["min_order_qty"]= "Minimum order is required"
    if price_type == "fixed" and not price:
        errors["price"] = "Enter a price or choose Negotiable"
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # ── Image upload
    image_path = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            ext      = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{farmer_id}_{int(datetime.utcnow().timestamp())}.{ext}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

    product_doc = {
        "farmer_id":      farmer_id,
        "farmer_name":    farmer["name"],
        "farmer_location": farmer.get("location", {}),
        "crop_name":      crop_name,
        "quantity":       float(quantity),
        "quantity_unit":  quantity_unit,
        "price_type":     price_type,                          # "fixed" or "negotiable"
        "price":          float(price) if price and price_type == "fixed" else None,
        "harvest_date":   harvest_date,
        "min_order_qty":  float(min_order_qty),
        "min_order_unit": min_order_unit,
        "image_path":     image_path,
        "is_live":        True,
        "created_at":     datetime.utcnow(),
    }

    try:
        result = products_col.insert_one(product_doc)
        return jsonify({
            "success": True,
            "product_id": str(result.inserted_id),
            "redirect": url_for("dashboard")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Toggle Product Live/Pause ──────────────────────────────────────────────────

@app.route("/farmer/product/<product_id>/toggle", methods=["POST"])
def toggle_product(product_id):
    farmer_id = session.get("farmer_id", "FARMER_001")
    product = products_col.find_one({"_id": ObjectId(product_id), "farmer_id": farmer_id})
    if not product:
        return jsonify({"success": False, "error": "Not found"}), 404

    new_status = not product["is_live"]
    products_col.update_one({"_id": ObjectId(product_id)}, {"$set": {"is_live": new_status}})
    return jsonify({"success": True, "is_live": new_status})


# ─── Delete Product ────────────────────────────────────────────────────────────

@app.route("/farmer/product/<product_id>/delete", methods=["POST"])
def delete_product(product_id):
    farmer_id = session.get("farmer_id", "FARMER_001")
    result = products_col.delete_one({"_id": ObjectId(product_id), "farmer_id": farmer_id})
    if result.deleted_count == 0:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


# ─── Logout ───────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))   # go to entry so another farmer can log in



# ─── Public API (buyer side uses this later) ───────────────────────────────────

@app.route("/api/products", methods=["GET"])
def get_live_products():
    products = list(products_col.find(
        {"is_live": True},
        {"_id": 1, "farmer_name": 1, "farmer_location": 1,
         "crop_name": 1, "quantity": 1, "quantity_unit": 1,
         "price_type": 1, "price": 1, "harvest_date": 1,
         "min_order_qty": 1, "min_order_unit": 1, "image_path": 1}
    ))
    for p in products:
        p["id"] = str(p["_id"])
        del p["_id"]
    return jsonify(products)


@app.route("/api/farmer/<farmer_id>", methods=["GET"])
def get_farmer_profile(farmer_id):
    farmer = farmers_col.find_one(
        {"farmer_id": farmer_id},
        {"_id": 0, "payment": 0}
    )
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify(farmer)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
