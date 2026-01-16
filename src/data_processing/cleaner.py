import pandas as pd
import numpy as np
from pathlib import Path
import sys
from PIL import Image
import hashlib
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from pymongo import MongoClient
    from bson import Binary
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

from config import CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME


class DataCleaner:

    def __init__(self, raw_dir="data/raw"):
        self.raw_dir = Path(raw_dir)
        self.df = None

    def create_metadata(self):
        print("\n[1] TAO METADATA TU ANH RAW")
        print("-" * 50)

        data = []
        categories = ["prohibitory", "warning", "mandatory", "informative"]

        for category in categories:
            category_path = self.raw_dir / category
            if not category_path.exists():
                print(f"Khong tim thay thu muc: {category_path}")
                continue

            images = list(category_path.glob("*.*"))
            print(f"{category}: {len(images)} anh")

            for img_file in images:
                if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                    continue
                try:
                    with Image.open(img_file) as img:
                        data.append({
                            "image_path": str(img_file),
                            "filename": img_file.name,
                            "category": category,
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "mode": img.mode,
                            "size_kb": img_file.stat().st_size / 1024
                        })
                except:
                    print(f"Loi doc anh: {img_file.name}")

        self.df = pd.DataFrame(data)
        print(f"Tong so anh hop le: {len(self.df)}")
        return self.df

    def add_md5_hash(self):
        print("\n[2] TINH MD5 HASH")
        print("-" * 50)

        def md5(path):
            try:
                with open(path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
            except:
                return None

        self.df["md5_hash"] = tqdm(
            self.df["image_path"].apply(md5),
            total=len(self.df),
            desc="MD5"
        )

    def add_perceptual_hash(self):
        if not HAS_IMAGEHASH:
            print("imagehash chua cai. Bo qua pHash.")
            return

        print("\n[3] TINH PERCEPTUAL HASH")
        print("-" * 50)

        def phash(path):
            try:
                return str(imagehash.average_hash(Image.open(path)))
            except:
                return None

        self.df["phash"] = tqdm(
            self.df["image_path"].apply(phash),
            total=len(self.df),
            desc="pHash"
        )

    def detect_and_remove_blurry(self, threshold=100.0):
        if not HAS_CV2:
            print("OpenCV chua cai. Bo qua loc anh mo.")
            return

        print("\n[4] LOC ANH MO (LAPLACIAN)")
        print("-" * 50)

        def lap_var(path):
            try:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                return cv2.Laplacian(img, cv2.CV_64F).var()
            except:
                return np.nan

        self.df["laplacian_var"] = tqdm(
            self.df["image_path"].apply(lap_var),
            total=len(self.df),
            desc="Sharpness"
        )

        before = len(self.df)
        self.df = self.df[self.df["laplacian_var"] >= threshold]
        after = len(self.df)

        print(f"So anh giu lai: {after}/{before}")

    def clean_data(self, min_size=32):
        print("\n[5] LAM SACH DU LIEU")
        print("-" * 50)

        before = len(self.df)

        self.df = self.df.drop_duplicates(subset=["filename"])
        self.df = self.df.drop_duplicates(subset=["md5_hash"])
        self.df = self.df[
            (self.df["width"] >= min_size) &
            (self.df["height"] >= min_size)
        ]

        after = len(self.df)
        print(f"So anh con lai sau clean: {after}/{before}")

    def upload_to_mongodb(self, drop_existing=True, include_image=True):
        if not HAS_MONGO:
            print("pymongo chua cai. Bo qua upload MongoDB.")
            return

        print("\n[6] UPLOAD METADATA LEN MONGODB")
        print("-" * 50)

        client = MongoClient(CONNECTION_STRING)
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        if drop_existing:
            collection.delete_many({})
            print("Da xoa du lieu cu trong collection.")

        docs = []
        for _, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Upload"):
            doc = {
                "filename": row["filename"],
                "category": row["category"],
                "width": int(row["width"]),
                "height": int(row["height"]),
                "size_kb": float(row["size_kb"]),
                "format": row["format"],
                "image_path": row["image_path"],
                "md5_hash": row["md5_hash"],
            }
            if include_image:
                with open(row["image_path"], "rb") as f:
                    doc["image"] = Binary(f.read())
            docs.append(doc)

        if docs:
            collection.insert_many(docs)
            print(f"Da insert {len(docs)} documents.")

        client.close()

    def resize_and_save(self, target_size=(64, 64), output_dir="data/processed"):
        print("\n[7] RESIZE VA LUU ANH")
        print("-" * 50)

        out_path = Path(output_dir)
        for cat in self.df["category"].unique():
            (out_path / cat).mkdir(parents=True, exist_ok=True)

        for _, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Resize"):
            img = Image.open(row["image_path"]).convert("RGB")
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            save_path = out_path / row["category"] / f"{Path(row['filename']).stem}.png"
            img.save(save_path)

        print(f"Anh da luu tai: {out_path}")


if __name__ == "__main__":
    print("\nCLEANER PIPELINE - TRAFFIC SIGN DATA")
    print("=" * 60)

    p = DataCleaner()
    p.create_metadata()
    p.add_md5_hash()
    p.add_perceptual_hash()
    p.detect_and_remove_blurry()
    p.clean_data()
    p.upload_to_mongodb(drop_existing=True, include_image=True)
    p.resize_and_save()

    print("\nHOAN TAT CLEANING PIPELINE")
