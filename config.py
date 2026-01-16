import os

CONNECTION_STRING = os.environ.get("MONGODB_URI", "mongodb+srv://trafficuser:uyen893605@cluster0.dnskt2r.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = os.environ.get("MONGODB_DB", "traffic_signs_db")
COLLECTION_NAME = os.environ.get("MONGODB_COLLECTION", "images")
