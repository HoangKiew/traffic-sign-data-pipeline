import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database import MinIOClient

def download_crops_by_class(bucket="traffic-signs-crop-classified", out_dir="outputs/crops"):
    minio = MinIOClient()
    img_names = minio.list_images(bucket=bucket)
    print(f"Found {len(img_names)} images in bucket '{bucket}'")
    for img_name in img_names:
        # Giả định: tên file hoặc folder chứa class_id, ví dụ: class_0/abc.jpg hoặc 0_abc.jpg
        # Ưu tiên: class_id là số đầu tiên trong tên file hoặc folder
        parts = img_name.replace("\\", "/").split("/")
        class_id = None
        for part in parts:
            if part.startswith("class_"):
                class_id = part.split("_")[1]
                break
            if part.isdigit():
                class_id = part
                break
            if "_" in part and part.split("_")[0].isdigit():
                class_id = part.split("_")[0]
                break
        if class_id is None:
            class_id = "unknown"
        save_dir = os.path.join(out_dir, f"class_{class_id}")
        os.makedirs(save_dir, exist_ok=True)
        data = minio.download_image(img_name, bucket=bucket)
        if data:
            fname = os.path.basename(img_name)
            with open(os.path.join(save_dir, fname), "wb") as f:
                f.write(data)
    print("✅ Done. All crops downloaded and sorted by class.")

if __name__ == "__main__":
    download_crops_by_class()
