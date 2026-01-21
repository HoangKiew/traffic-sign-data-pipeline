import cv2
import os
from db import images_col

RAW_ROOT = "data/raw_images"
PROCESSED_ROOT = "data/processed_images"

os.makedirs(PROCESSED_ROOT, exist_ok=True)

for img in images_col.find({"stage": "raw"}):
    raw_path = img["raw_path"]

    if not os.path.exists(raw_path):
        print(f"⚠ Missing file: {raw_path}")
        continue

    im = cv2.imread(raw_path)
    if im is None:
        print(f"⚠ Broken image skipped: {raw_path}")
        continue

    im = cv2.resize(im, (640, 640))
    im = cv2.bilateralFilter(im, 9, 75, 75)

    filename = os.path.basename(raw_path)
    save_path = os.path.join(PROCESSED_ROOT, filename)

    cv2.imwrite(save_path, im)

    images_col.update_one(
        {"_id": img["_id"]},
        {"$set": {
            "processed_path": save_path,
            "stage": "processed"
        }}
    )

print("✔ Preprocess done (valid images only)")
