import pymongo
import certifi
import sys

uri = "mongodb+srv://rudegamer89b_db_user:PkPF6a6NBrhfZot7@tunora.w630k5n.mongodb.net/?appName=Tunora"

print(f"Testing basic connection...")
client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
    client.admin.command('ping')
    print("Success without certifi!")
except Exception as e:
    print(f"Failed without certifi:\n{e}")

print(f"\nTesting with certifi...")
client_cert = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
try:
    client_cert.admin.command('ping')
    print("Success with certifi!")
except Exception as e:
    print(f"Failed with certifi:\n{e}")
