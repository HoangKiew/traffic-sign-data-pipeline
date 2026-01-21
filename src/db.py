from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

images_col = db["images"]
annotations_col = db["annotations"]
consensus_col = db["consensus"]
