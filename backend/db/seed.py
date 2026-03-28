from backend.db import products_col
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from db import products_col

# Sample Agriculture Products
sample_products = [
    {
        "name": "Organic Roma Tomatoes",
        "category": "vegetables",
        "price": 45,
        "quantity": 250,
        "image_url": "https://images.unsplash.com/photo-1592841200221-a6898f307bac?q=80&w=400",
        "description": "Sweet, organic vine-ripened tomatoes, perfect for salads and sauces.",
        "farmer": {
            "name": "Ramesh Patel",
            "location": "Gujarat",
            "rating": 4.5
        },
        "isOrganic": True,
        "isFresh": True
    },
    {
        "name": "Nandini Premium Cow Milk",
        "category": "dairy",
        "price": 54,
        "quantity": 100,
        "image_url": "https://images.unsplash.com/photo-1550583760-d8cc62d400db?q=80&w=400",
        "description": "Pure, pasteurized cow milk delivered fresh from our dairy farm.",
        "farmer": {
            "name": "Ananya Sharma",
            "location": "Karnataka",
            "rating": 4.8
        },
        "isOrganic": False,
        "isFresh": True
    },
    {
        "name": "Sharbati Whole Wheat",
        "category": "grains",
        "price": 60,
        "quantity": 500,
        "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?q=80&w=400",
        "description": "Premium Sharbati wheat grains from the fertile fields of Madhya Pradesh.",
        "farmer": {
            "name": "Rajesh Singh",
            "location": "Madhya Pradesh",
            "rating": 4.2
        },
        "isOrganic": True,
        "isFresh": False
    },
    {
        "name": "Kesar Mangoes (Box)",
        "category": "fruits",
        "price": 1200,
        "quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?q=80&w=400",
        "description": "Sweet, aromatic Kesar mangoes from Junagadh orchards. Fresh harvest.",
        "farmer": {
            "name": "Yash Patel",
            "location": "Gujarat",
            "rating": 4.9
        },
        "isOrganic": True,
        "isFresh": True
    },
    {
        "name": "Farm Fresh Sweet Corn",
        "category": "vegetables",
        "price": 30,
        "quantity": 150,
        "image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?q=80&w=400",
        "description": "Tender and sweet golden kernels, harvested daily for ultimate freshness.",
        "farmer": {
            "name": "Karan Kumar",
            "location": "Maharashtra",
            "rating": 4.0
        },
        "isOrganic": False,
        "isFresh": True
    }
]

def seed_db():
    print("Clearing existing products...")
    products_col.delete_many({})
    print("Inserting sample products...")
    products_col.insert_many(sample_products)
    print("Seeding complete!")

if __name__ == "__main__":
    seed_db()
