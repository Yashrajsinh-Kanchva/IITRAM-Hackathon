from flask import Blueprint, request, jsonify
from db.db import orders_col, cart_col, negotiations_col
from datetime import datetime
from bson import ObjectId

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/', methods=['POST'])
def place_order():
    data = request.json
    user_id = data.get('user_id')
    address = data.get('address')
    payment_method = data.get('payment_method')
    
    if not user_id or not address or not payment_method:
        return jsonify({"error": "User ID, address, and payment method are required"}), 400

    cart = cart_col.find_one({"user_id": user_id})
    if not cart or not cart.get('items'):
        return jsonify({"error": "Cart is empty"}), 400

    items = cart['items']
    total_price = sum(item['price'] * item['quantity'] for item in items)
    
    order = {
        "user_id": user_id,
        "items": items,
        "total_price": total_price,
        "address": address,
        "payment_method": payment_method,
        "status": "placed",
        "created_at": datetime.now().isoformat()
    }
    
    order_id = orders_col.insert_one(order).inserted_id
    
    # Clear cart after order
    cart_col.delete_one({"user_id": user_id})
    
    # Purge completed negotiations securely since payment was successful
    for purchased_item in items:
        nid = purchased_item.get("neg_id")
        if nid:
            try:
                negotiations_col.delete_one({"_id": ObjectId(nid)})
            except:
                pass
    
    return jsonify({"message": "Order placed successfully", "order_id": str(order_id)}), 201

@orders_bp.route('/<user_id>', methods=['GET'])
def get_orders(user_id):
    orders = list(orders_col.find({"user_id": user_id}))
    for o in orders:
        o['_id'] = str(o['_id'])
    return jsonify(orders)
