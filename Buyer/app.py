from flask import Flask, render_template, request, jsonify, session, abort
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)
app.secret_key = "buyer_hackathon_secret_2024"

# ─── MongoDB Connection ────────────────────────────────────────────────────────
# Re-using the same MongoDB Atlas URI so Buyers can see what Farmers are posting!
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/farm_to_market?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
db = client.farm_to_market

# Collections (Same as Farmer App)
farmers_col = db.farmers
products_col = db.products
offers_col = db.offers

# Dummy User Setup for Buyer Testing
@app.before_request
def mock_buyer_auth():
    if "buyer_id" not in session:
        session["buyer_id"] = "BUYER_999"
        session["buyer_name"] = "Taj Mahal Palace Hotels"


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template("marketplace.html")

@app.route("/api/marketplace", methods=["GET"])
def api_marketplace():
    """
    Fetch all LIVE products with optional search and filters.
    """
    search_query = request.args.get("q", "").strip()
    location_filter = request.args.get("loc", "").strip()
    
    # Base query: must be live
    query = {"is_live": True}
    
    # 1. Search by crop name (case-insensitive regex)
    if search_query:
        query["crop_name"] = {"$regex": search_query, "$options": "i"}

    products_cursor = products_col.find(query).sort("created_at", -1)
    
    # Join with farmer info manually to populate location/name
    products = []
    for p in products_cursor:
        p["id"] = str(p["_id"])
        del p["_id"]
        
        # Attach farmer info
        farmer = farmers_col.find_one({"farmer_id": p.get("farmer_id")}, {"_id": 0, "name": 1, "location": 1})
        if farmer:
            p["farmer_name"] = farmer.get("name", "Unknown Farmer")
            p["location"] = farmer.get("location", "Unknown Location")
        else:
            p["farmer_name"] = "Unknown Farmer"
            p["location"] = "Unknown Location"
            
        # 2. Location filter (Client-side-like filtering after join, for simplicity in hackathon)
        if location_filter and location_filter.lower() not in p["location"].lower():
            continue
            
        products.append(p)
        
    return jsonify({"success": True, "data": products})

@app.route("/product/<product_id>", methods=["GET"])
def product_detail(product_id):
    """
    Show detailed product page.
    """
    try:
        product = products_col.find_one({"_id": ObjectId(product_id)})
    except Exception:
        abort(404)
        
    if not product:
        abort(404)
        
    product["id"] = str(product["_id"])
    del product["_id"]
    
    farmer = farmers_col.find_one({"farmer_id": product.get("farmer_id")}, {"_id": 0})
    if not farmer:
        farmer = {"name": "Unknown Farmer", "location": "Unknown Location"}
        
    return render_template("product_detail.html", product=product, farmer=farmer)


if __name__ == "__main__":
    # Note: Running on 5001 so the Farmer app can keep running on 5000 simultaneously!
    app.run(debug=True, port=5001)
