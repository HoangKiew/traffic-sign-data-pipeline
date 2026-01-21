import cv2
import os
import numpy as np
from db import images_col
from config import IMAGE_SIZE

TRANSFORM_DIR = "data/transformed_images"
os.makedirs(TRANSFORM_DIR, exist_ok=True)


def resize_pad(img, size=IMAGE_SIZE):
    h, w, _ = img.shape
    scale = min(size / w, size / h)
    nw, nh = int(w * scale), int(h * scale)

    img_resized = cv2.resize(img, (nw, nh))

    canvas = np.ones((size, size, 3), dtype=np.uint8) * 128
    x_offset = (size - nw) // 2
    y_offset = (size - nh) // 2
    canvas[y_offset:y_offset+nh, x_offset:x_offset+nw] = img_resized

    return canvas


count = 0
for img in images_col.find({"stage": "processed"}):
    path = img.get("processed_path")

    if not path or not os.path.exists(path):
        print(f"⚠ Missing file: {path}")
        continue

    im = cv2.imread(path)
    if im is None:
        print(f"⚠ Cannot read image: {path}")
        continue

    im = resize_pad(im)

    save_path = path.replace("processed_images", "transformed_images")
    cv2.imwrite(save_path, im)

    images_col.update_one(
        {"_id": img["_id"]},
        {"$set": {
            "transformed_path": save_path,
            "stage": "transformed"
        }}
    )

    count += 1

print(f"✔ Transform done ({count} images)")
