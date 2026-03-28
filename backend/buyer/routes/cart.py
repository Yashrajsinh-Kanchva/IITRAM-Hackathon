from flask import Blueprint, request, jsonify
from db.db import cart_col, products_col
from bson import ObjectId

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/<user_id>', methods=['GET'])
def get_cart(user_id):
    cart = cart_col.find_one({"user_id": user_id})
    if cart:
        cart['_id'] = str(cart['_id'])
        return jsonify(cart)
    return jsonify({"user_id": user_id, "items": []})

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({"error": "User ID and Product ID are required"}), 400

    product = products_col.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404

    negotiated_price = data.get('negotiated_price')
    neg_id = data.get('neg_id')
    final_price = float(negotiated_price) if negotiated_price else product.get('price', product.get('base_price', 0))

    img = product.get('image_url') or product.get('image_path')
    item = {
        "product_id": str(product['_id']),
        "name": product.get('name', product.get('crop_name', 'Fresh Harvest')),
        "price": final_price,
        "quantity": quantity,
        "image": img if img else 'https://images.unsplash.com/photo-1592841200221-a6898f307bac?q=80&w=400',
        "neg_id": neg_id
    }

    cart = cart_col.find_one({"user_id": user_id})
    if cart:
        # Check if item exists in cart
        items = cart.get('items', [])
        found = False
        for ex_item in items:
            if ex_item['product_id'] == product_id:
                ex_item['quantity'] += quantity
                found = True
                break
        if not found:
            items.append(item)
        cart_col.update_one({"user_id": user_id}, {"$set": {"items": items}})
    else:
        cart_col.insert_one({"user_id": user_id, "items": [item]})

    return jsonify({"message": "Item added to cart"}), 201

@cart_bp.route('/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    cart_col.update_one({"user_id": user_id}, {"$pull": {"items": {"product_id": product_id}}})
    return jsonify({"message": "Item removed from cart"})

@cart_bp.route('/update', methods=['POST'])
def update_cart_quantity():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    new_quantity = data.get('quantity')
    
    # Use array filters for precise update
    cart_col.update_one(
        {"user_id": user_id, "items.product_id": product_id},
        {"$set": {"items.$.quantity": new_quantity}}
    )
    return jsonify({"message": "Quantity updated"})
