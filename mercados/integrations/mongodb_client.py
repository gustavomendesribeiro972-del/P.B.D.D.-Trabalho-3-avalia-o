import os
from pymongo import MongoClient

client = MongoClient(
    os.getenv("MONGODB_URI")
)

database = client[
    os.getenv("MONGODB_DATABASE", "ecommerce")
]

products_collection = database["produtos"]