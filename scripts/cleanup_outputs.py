import os
import shutil
import sys

# Thêm đường dẫn gốc project vào sys.path để import được utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def safe_remove(path):
    if os.path.isfile(path):
        try:
            os.remove(path)
        except Exception:
            pass
    elif os.path.isdir(path):
        try:
            shutil.rmtree(path)
        except Exception:
            pass

def cleanup_minio_and_mongo(delete_minio=True, delete_mongo=True):
    if delete_minio:
        print("Đang xóa dữ liệu MinIO (trừ traffic-signs-raw)...")
        try:
            from utils.database import MinIOClient
            minio = MinIOClient()
            buckets = minio.client.list_buckets()
            for bucket in buckets:
                name = bucket.name
                if name == "traffic-signs-raw":
                    continue
                while True:
                    objects = list(minio.client.list_objects(name, recursive=True))
                    if not objects:
                        break
                    for obj in objects:
                        minio.client.remove_object(name, obj.object_name)
                minio.client.remove_bucket(name)
            print("Đã xóa xong dữ liệu MinIO.")
        except Exception as e:
            print("Lỗi khi xóa dữ liệu MinIO:", e)
            print("Gợi ý: Lỗi 503 thường do MinIO chưa khởi động xong hoặc quá tải.")
            print("Vui lòng kiểm tra MinIO container (docker ps) và thử lại sau.")

    if delete_mongo:
        print("Đang xóa toàn bộ database MongoDB...")
        try:
            from utils.database import MongoDBClient
            mongo = MongoDBClient()
            db = mongo.db
            mongo.client.drop_database(db.name)
            print("Đã xóa xong database MongoDB.")
        except Exception as e:
            print("Lỗi khi xóa database MongoDB:", e)
            print("Gợi ý: Đảm bảo MongoDB container đang chạy và cấu hình đúng.")

def cleanup_folders(folders):
    print("Đang xóa các thư mục output/dataset/log/temp...")
    for folder in folders:
        safe_remove(folder)
    print("Đã xóa xong các thư mục.")

def main():
    # Danh sách các thư mục không chứa code cần xóa (ẩn hết, không in ra)
    folders = [
        "outputs",
        "output",
        "output_dataset",
        "analytics_charts",
        "compare_results",
        "sample_images",
        "downloads",
        "datasets",
        "logs",
        "temp_crawl",
        "minio_data",
        "mongo_data",
        "checkpoints"
    ]

    # Không in ra bất kỳ thông báo nào khi xóa
    print("Chọn kiểu xóa dữ liệu:")
    print("  1. Xóa toàn bộ thư mục không chứa code (output, datasets, logs, ...)")
    print("  2. Xóa dữ liệu MinIO (trừ traffic-signs-raw)")
    print("  3. Xóa dữ liệu MongoDB")
    print("  4. Xóa cả MinIO và MongoDB")
    print("  5. Xóa tất cả (thư mục + MinIO + MongoDB)")
    choice = input("Nhập lựa chọn (1-5): ").strip()

    if choice == "1":
        cleanup_folders(folders)
    elif choice == "2":
        cleanup_minio_and_mongo(delete_minio=True, delete_mongo=False)
    elif choice == "3":
        cleanup_minio_and_mongo(delete_minio=False, delete_mongo=True)
    elif choice == "4":
        cleanup_minio_and_mongo(delete_minio=True, delete_mongo=True)
    elif choice == "5":
        cleanup_folders(folders)
        cleanup_minio_and_mongo(delete_minio=True, delete_mongo=True)
    # Không in ra gì cả

if __name__ == "__main__":
    main()
