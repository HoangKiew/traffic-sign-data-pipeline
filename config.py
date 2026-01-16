import os
from dotenv import load_dotenv

# Nạp dữ liệu từ file .env vào bộ nhớ tạm (environment variables)
load_dotenv() 

# Lấy dữ liệu ra dùng. Nếu file .env bị mất, nó sẽ dùng localhost để tránh crash code.
CONNECTION_STRING = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("MONGODB_DB", "traffic_signs_db")
COLLECTION_NAME = os.environ.get("MONGODB_COLLECTION", "images")

print(f"Đã sẵn sàng kết nối tới database: {DATABASE_NAME}")