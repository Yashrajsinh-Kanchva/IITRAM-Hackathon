from flask import Blueprint, request, jsonify
from db.db import wishlist_col, products_col
from bson import ObjectId

wishlist_bp = Blueprint('wishlist', __name__)

@wishlist_bp.route('/<user_id>', methods=['GET'])
def get_wishlist(user_id):
    wishlist = wishlist_col.find_one({"user_id": user_id})
    if not wishlist:
        return jsonify({"items": []})
    
    # Get full product details for each item in wishlist
    items = []
    # Make sure we handle product_ids as a list
    product_ids = wishlist.get("product_ids", [])
    for pid in product_ids:
        try:
            product = products_col.find_one({"_id": ObjectId(pid)})
            if product:
                product['_id'] = str(product['_id'])
                # Also include ID as a string for convenience
                product['id'] = str(product['_id'])
                product['name'] = product.get('name', product.get('crop_name', 'Fresh Harvest'))
                
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
                product['price'] = product.get('price', product.get('base_price', 0))
                
                items.append(product)
        except:
            continue
            
    return jsonify({"items": items})

@wishlist_bp.route('/toggle', methods=['POST'])
def toggle_wishlist():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')

    wishlist = wishlist_col.find_one({"user_id": user_id})
    if not wishlist:
        wishlist_col.insert_one({"user_id": user_id, "product_ids": [product_id]})
        return jsonify({"message": "Added to wishlist", "status": "added"})
    
    product_ids = wishlist.get("product_ids", [])
    if product_id in product_ids:
        product_ids.remove(product_id)
        wishlist_col.update_one({"user_id": user_id}, {"$set": {"product_ids": product_ids}})
        return jsonify({"message": "Removed from wishlist", "status": "removed"})
    else:
        product_ids.append(product_id)
        wishlist_col.update_one({"user_id": user_id}, {"$set": {"product_ids": product_ids}})
        return jsonify({"message": "Added to wishlist", "status": "added"})
