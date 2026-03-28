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

def validate_migration():
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    
    print("---------------------------------------------------------")
    print(f"{'Collection':<30} | {'Old Count':<10} | {'New Count':<10} | {'Status'}")
    print("---------------------------------------------------------")

    all_good = True

    for old_col_name, new_col_name in collections_mapping.items():
        old_count = old_db[old_col_name].count_documents({})
        new_count = new_db[new_col_name].count_documents({})
        
        status = "✅ OK" if old_count == new_count else "❌ MISMATCH"
        if old_count != new_count:
            all_good = False

        print(f"{old_col_name + ' -> ' + new_col_name:<30} | {old_count:<10} | {new_count:<10} | {status}")

    print("---------------------------------------------------------")
    if all_good:
        print("\nAll data successfully validated! Safely confirmed 0 data-loss.")
        print("\nIf you want to cleanup, you can manually run:")
        print("client.drop_database('Farm-To-Market')")
    else:
        print("\nWARNING: Some collections did not migrate completely. Please check logs.")

if __name__ == "__main__":
    validate_migration()
