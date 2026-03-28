from pymongo import MongoClient

MONGO_URI = "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['farm_to_market']
cols = db.list_collection_names()
print("Collections in farm_to_market:", cols)

for col in cols:
    print(f"Count in {col}:", db[col].count_documents({}))
    if db[col].count_documents({}) > 0:
        print("Sample:", db[col].find_one({}, {"_id": 0}))
