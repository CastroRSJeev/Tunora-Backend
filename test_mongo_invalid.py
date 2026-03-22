import pymongo
import certifi
import sys

uri = "mongodb+srv://rudegamer89b_db_user:PkPF6a6NBrhfZot7@tunora.w630k5n.mongodb.net/?appName=Tunora&tlsAllowInvalidCertificates=true"

print(f"Testing connection with tlsAllowInvalidCertificates=true...")
client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
    client.admin.command('ping')
    print("Success with tlsAllowInvalidCertificates!")
except Exception as e:
    print(f"Failed:\n{e}")
