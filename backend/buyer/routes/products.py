from flask import Blueprint, request, jsonify
from db.db import products_col
from bson import ObjectId

products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
def get_products():
    """
    Fetch all products with optional filters
    Params: search, category, min_price, max_price, organic, fresh
    """
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'all')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    organic = request.args.get('organic', type=bool)
    fresh = request.args.get('fresh', type=bool)

    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if category != 'all':
        query["category"] = category
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None: query["price"]["$gte"] = min_price
        if max_price is not None: query["price"]["$lte"] = max_price
    if organic:
        query["isOrganic"] = True
    if fresh:
        query["isFresh"] = True

    products = list(products_col.find(query))
    for p in products:
        p['_id'] = str(p['_id'])
        # Dynamic Schema Normalization for Farmer-Module Integration
        p['name'] = p.get('name', p.get('crop_name', 'Fresh Harvest'))
        p['category'] = p.get('category', 'all')
        
        farmer_loc = p.get('farmer_location', {})
        loc_str = farmer_loc.get('state', 'Gujarat') if isinstance(farmer_loc, dict) else str(farmer_loc)
        
        if 'farmer' not in p or not isinstance(p['farmer'], dict):
            p['farmer'] = {
                'name': p.get('farmer_name', 'Verified Local Farmer'),
                'location': loc_str,
                'rating': p.get('rating', 4.8)
            }
            
        img = p.get('image_url') or p.get('image_path')
        p['image_url'] = img if img else 'https://images.unsplash.com/photo-1592841200221-a6898f307bac?q=80&w=400'
        
        p['isOrganic'] = p.get('isOrganic', True)
        p['isFresh'] = p.get('isFresh', True)
        p['price'] = p.get('price', p.get('base_price', 0))
        p['quantity'] = p.get('quantity', 100)
        p['description'] = p.get('description', f"Fresh {p['name']} directly harvested from {loc_str}.")
    return jsonify(products)

@products_bp.route('/<id>', methods=['GET'])
def get_product(id):
    try:
        product = products_col.find_one({"_id": ObjectId(id)})
        if product:
            product['_id'] = str(product['_id'])
            
            product['name'] = product.get('name', product.get('crop_name', 'Fresh Harvest'))
            product['category'] = product.get('category', 'all')
            
            farmer_loc = product.get('farmer_location', {})
            loc_str = farmer_loc.get('state', 'Gujarat') if isinstance(farmer_loc, dict) else str(farmer_loc)
            
            if 'farmer' not in product or not isinstance(product['farmer'], dict):
                product['farmer'] = {
                    'name': product.get('farmer_name', 'Verified Local Farmer'),
                    'location': loc_str,
                    'rating': product.get('rating', 4.8)
                }
                
            img = product.get('image_url') or product.get('image_path')
            product['image_url'] = img if img else 'https://images.unsplash.com/photo-1592841200221-a6898f307bac?q=80&w=400'
            
            product['isOrganic'] = product.get('isOrganic', True)
            product['isFresh'] = product.get('isFresh', True)
            product['price'] = product.get('price', product.get('base_price', 0))
            product['quantity'] = product.get('quantity', 100)
            product['description'] = product.get('description', f"Fresh {product['name']} directly harvested from {loc_str}.")
            
            return jsonify(product)
        return jsonify({"error": "Product not found"}), 404
    except:
        return jsonify({"error": "Invalid Product ID"}), 400
