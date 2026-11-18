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

def teste_mongo():
    print("Tentando conectar com o MongoDB...")
    try:
        client.admin.command("ping")
        print("Conexão estabelecida (MDB) com sucesso!")

        #Produtos test:
        print(
        "Quantidade de produtos:",
        products_collection.count_documents({})
        )

        print(
            "Primeiros produtos:",
            list(products_collection.find().limit(3))
        )
        
    except Exception as e:
        raise Exception ("Ocorreu um erro ao conectar com o MongoDB: ", e)