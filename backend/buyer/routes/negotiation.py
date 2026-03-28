from flask import Blueprint, request, jsonify
from db.db import negotiations_col, products_col
from bson import ObjectId
from datetime import datetime

negotiation_bp = Blueprint('negotiate', __name__)

@negotiation_bp.route('/submit', methods=['POST'])
def submit_negotiation():
    data = request.get_json()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    product_id = data.get('product_id')
    negotiated_price = data.get('negotiated_price')
    message = data.get('message')

    # Fetch product details for original price and name
    product = products_col.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404

    negotiation = {
        "user_id": user_id,
        "user_name": user_name,
        "product_id": product_id,
        "product_name": product.get('name', product.get('crop_name', 'Fresh Harvest')),
        "original_price": product.get('price', product.get('base_price', 0)),
        "negotiated_price": float(negotiated_price),
        "message": message,
        "status": "pending",
        "created_at": datetime.now()
    }

    negotiations_col.insert_one(negotiation)
    return jsonify({"message": "Negotiation offer sent successfully!"}), 201

@negotiation_bp.route('/<user_id>', methods=['GET'])
def get_user_negotiations(user_id):
    negotiations = list(negotiations_col.find({"user_id": user_id}).sort("created_at", -1))
    for n in negotiations:
        n['_id'] = str(n['_id'])
    return jsonify(negotiations)

@negotiation_bp.route('/update/<neg_id>', methods=['POST'])
def update_negotiation(neg_id):
    data = request.json
    new_price = float(data.get('negotiated_price'))
    new_msg = data.get('message')
    
    negotiations_col.update_one(
        {"_id": ObjectId(neg_id)},
        {"$set": {
            "negotiated_price": new_price,
            "message": new_msg,
            "status": "pending",
            "updated_at": datetime.now()
        }}
    )
    return jsonify({"message": "Negotiation offer successfully updated!"}), 200

@negotiation_bp.route('/reject/<neg_id>', methods=['POST'])
def reject_negotiation(neg_id):
    negotiations_col.update_one(
        {"_id": ObjectId(neg_id)},
        {"$set": {
            "status": "rejected",
            "updated_at": datetime.now()
        }}
    )
    return jsonify({"message": "Negotiation offer securely rejected."}), 200
