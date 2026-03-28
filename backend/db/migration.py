from pymongo import MongoClient

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

old_db_name = "Farm-To-Market"
new_db_name = "farm_to_market"

collections_mapping = {
    "Users": "buyer_Users",
    "Products": "buyer_Products",
    "Cart": "buyer_Cart",
    "Orders": "buyer_Orders",
    "Negotiations": "buyer_Negotiations",
    "Wishlist": "buyer_Wishlist"
}

def migrate_database():
    old_db = client[old_db_name]
    new_db = client[new_db_name]

    print(f"Starting Migration: {old_db_name} -> {new_db_name}")

    for old_col_name, new_col_name in collections_mapping.items():
        old_col = old_db[old_col_name]
        new_col = new_db[new_col_name]

        # Get all documents from old collection
        documents = list(old_col.find({}))
        if not documents:
            print(f"  [SKIP] Collection '{old_col_name}' is empty.")
            continue

        inserted_count = 0
        skipped_count = 0

        # Insert documents safely (avoiding duplicates by _id)
        for doc in documents:
            doc_id = doc.get("_id")
            if not new_col.find_one({"_id": doc_id}):
                new_col.insert_one(doc)
                inserted_count += 1
            else:
                skipped_count += 1

        print(f"  [DONE] {old_col_name} -> {new_col_name} | Migrated: {inserted_count} | Skipped (Existing): {skipped_count}")

    print("\nMigration Script Finished! Please run validate.py to verify data integrity.")

if __name__ == "__main__":
    migrate_database()
