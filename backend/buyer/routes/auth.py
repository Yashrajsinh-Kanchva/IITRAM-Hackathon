from flask import Blueprint, request, jsonify
from db.db import users_col
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    if users_col.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    user_id = users_col.insert_one({
        "name": name,
        "email": email,
        "password": hashed_pw
    }).inserted_id

    return jsonify({"message": "Signup successful", "user_id": str(user_id)}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = users_col.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email']
            }
        }), 200
    
    return jsonify({"error": "Invalid email or password"}), 401
