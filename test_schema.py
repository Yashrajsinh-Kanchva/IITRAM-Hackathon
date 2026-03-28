import pprint
from backend.db.db import db
doc = db['products'].find_one()
print("SCHEMA FOR PRODUCTS COLLECTION:")
pprint.pprint(doc)
