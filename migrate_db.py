from pymongo import MongoClient

# Re-using the same MongoDB Atlas URI
MONGO_URI = "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

# The old database where we previously stored our Farmer and Product data
db_old = client["krishiconnect"]

# The new database that your friend created
db_new = client["farm_to_market"]

def migrate_collection(col_name):
    old_col = db_old[col_name]
    new_col = db_new[col_name]
    
    docs = list(old_col.find({}))
    if not docs:
        print(f"No documents found in old {col_name} collection.")
        return 0

    inserted_count = 0
    for doc in docs:
        # Check if already exists in the new DB by exactly the same _id
        existing = new_col.find_one({"_id": doc["_id"]})
        if not existing:
            new_col.insert_one(doc)
            inserted_count += 1
        else:
            print(f"Document {doc['_id']} already exists in new {col_name}, skipping to prevent overwrite.")
            
    return inserted_count

print("Starting migration from krishiconnect -> farm_to_market...")

farmers_moved = migrate_collection("farmers")
products_moved = migrate_collection("products")

print(f"Success! Migrated {farmers_moved} farmers and {products_moved} products into farm_to_market.")
