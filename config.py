import os

# Cach dung:
# 1) Neu dung MongoDB local (mongod chay tren may ban):
#    -> Khong can set gi, mac dinh se la "mongodb://localhost:27017"
#
# 2) Neu dung MongoDB Atlas:
#    - Tren Windows (cmd):
#        set MONGODB_URI="mongodb+srv://<user>:<pass>@<cluster-url>/?retryWrites=true&w=majority"
#        set MONGODB_DB=traffic_signs_db
#        set MONGODB_COLLECTION=images
#    - Sau do chay:
#        python main.py

# MongoDB connection string (doc tu ENV, neu khong co thi dung localhost)
CONNECTION_STRING = os.environ.get("")

DATABASE_NAME = os.environ.get("MONGODB_DB", "traffic_signs_db")
COLLECTION_NAME = os.environ.get("MONGODB_COLLECTION", "images")
