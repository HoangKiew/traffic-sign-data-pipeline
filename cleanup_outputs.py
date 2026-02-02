import os
import shutil

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
        try:
            from utils.database import MinIOClient
            minio = MinIOClient()
            buckets = minio.client.list_buckets()
            for bucket in buckets:
                name = bucket.name
                if name == "traffic-signs-raw":
                    continue
                print(f"🗑️ Đang xóa toàn bộ file trong bucket: {name}")
                objects = list(minio.client.list_objects(name))
                for obj in objects:
                    minio.client.remove_object(name, obj.object_name)
        except Exception as e:
            print(f"⚠️ Lỗi xóa MinIO: {e}")

    if delete_mongo:
        try:
            from utils.database import MongoDBClient
            mongo = MongoDBClient()
            db = mongo.db
            print(f"🗑️ Đang xóa toàn bộ dữ liệu MongoDB trong database: {db.name}")
            for col_name in db.list_collection_names():
                result = db[col_name].delete_many({})
                print(f"   - Đã xóa {result.deleted_count} documents ở collection '{col_name}'")
        except Exception as e:
            print(f"⚠️ Lỗi xóa MongoDB: {e}")

def cleanup_folders(folders):
    for folder in folders:
        safe_remove(folder)
    print("✅ Đã xóa các thư mục được chọn.")

def main():
    print("Chọn kiểu xóa dữ liệu:")
    print("  1. Xóa các thư mục kết quả (labels, logs, output, ...}")
    print("  2. Xóa dữ liệu MinIO (trừ traffic-signs-raw)")
    print("  3. Xóa dữ liệu MongoDB")
    print("  4. Xóa cả MinIO và MongoDB")
    print("  5. Xóa tất cả (thư mục + MinIO + MongoDB)")
    choice = input("Nhập lựa chọn (1-5): ").strip()

    folders = [
        "datasets/labels",
        "datasets/labels_n",
        "datasets/labels_x",
        "compare_results",
        "analytics_charts",
        "sample_images",
        "downloads",
        "output",
        "output_dataset",
        "temp_crawl",
        "logs"
    ]

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
    else:
        print("Không hợp lệ. Vui lòng chọn từ 1 đến 5.")

if __name__ == "__main__":
    main()
