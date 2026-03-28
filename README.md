# 🚜 Farm-To-Market | Buyer-Side E-Commerce

A premium, agriculture-dedicated e-commerce platform connecting buyers directly with local farmers. Designed for a high-performance, responsive hackathon demonstration.

## 🌟 Key Features
- **Amazon-style Marketplace**: Dynamic grid for browsing fresh produce, dairy, and grains.
- **Embedded Farmer Profiles**: Every product highlights its origin, farmer location, and rating.
- **Smart Filtering**: Seamless search by product name, category tags, organic/fresh status, and price ranges.
- **Persistent Cart System**: Cart data is synchronized with MongoDB Atlas for cross-session persistence.
- **Secure Auth**: Hashed password storage with session-based user tracking.
- **Regional Discovery**: Direct insights into where your food comes from.

## 🧠 Tech Stack
- **Frontend**: HTML5, CSS3 (Custom Design System), Vanilla ES6 JavaScript.
- **Backend**: Python Flask REST API.
- **Database**: MongoDB Atlas (PyMongo).

## 📁 Project Structure
```text
/farm-to-market
 ├── /frontend          # HTML/CSS/JS Assets
 ├── /backend           # Flask API Blueprints
 ├── db.py              # MongoDB Connection
 ├── app.py             # Server Entry Point
 ├── seed.py            # Data Seeding Script
 └── requirements.txt   # Python Dependencies
```

## 🚀 Setup Instructions

### 1. Database Connection
The application is pre-configured to connect to the following MongoDB Atlas Cluster:
`mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority`

### 2. Backend Installation
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Seed the database with sample products
python seed.py

# Start the Flask server
python backend/app.py
```

### 3. Frontend Access
Simply open `frontend/index.html` in your browser once the server is running.
The frontend communicates with the API at `http://localhost:5000/api`.

## 🔌 API Documentation

### AUTH
- `POST /api/signup`: Register a new buyer account.
- `POST /api/login`: Authenticate and start a session.

### PRODUCTS
- `GET /api/products`: Fetch all products with query filters (`search`, `category`, `organic`, `fresh`).
- `GET /api/products/<id>`: Get detailed technical specs and farmer metadata for a single item.

### CART
- `GET /api/cart/<user_id>`: Retrieve the buyer's persistent cart.
- `POST /api/cart/add`: Multi-quantity addition to the MongoDB cart.
- `POST /api/cart/remove`: Line-item removal from the array.

### ORDERS
- `POST /api/orders/`: Submit a checkout form and create a permanent order record.
- `GET /api/orders/<user_id>`: View the buyer's order history.

## 🎯 Hackathon Highlights
- **Premium Organic Theme**: Vibrant forest-green palette (`#2D6A4F`) with high-impact typography.
- **No Separate Collections**: Complies with the 'Embedded Farmer' constraint for 10x faster query performance.
- **Mobile First**: Fully responsive Amazon-like UI for ordering on the go.
