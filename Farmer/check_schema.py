from pymongo import MongoClient
import os

MONGO_URI = "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/farm_to_market?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["farm_to_market"]

col = db["buyer_Negotiation"]

doc = col.find_one()
if doc:
    print("Found Document Schema Keys:", list(doc.keys()))
    print("Document:", doc)
else:
    print("Collection is absolutely empty.")

