from pymongo import MongoClient
import os

# MongoDB Atlas connection string
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = "farm_to_market"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Centralized Collections with "buyer_" prefix
users_col = db["buyer_Users"]
products_col = db["products"] # Sourced directly from actual products table
cart_col = db["buyer_Cart"]
orders_col = db["buyer_Orders"]
negotiations_col = db["buyer_Negotiations"]
wishlist_col = db["buyer_Wishlist"]

def get_db():
    return db
