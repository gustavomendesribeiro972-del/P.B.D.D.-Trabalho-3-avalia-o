import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config.env")

client = MongoClient(os.getenv("MONGODB_URI"))

database = client[
    os.getenv("MONGODB_DATABASE", "ecommerce")
]

products_collection = database["produtos"]