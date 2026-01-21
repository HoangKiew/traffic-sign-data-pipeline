from ultralytics import YOLO
from db import images_col, annotations_col

model = YOLO("models/yolov8n.pt")

for img in images_col.find({"stage": "transformed"}):
    results = model(img["transformed_path"])

    for r in results:
        for box in r.boxes:
            annotations_col.insert_one({
                "image_id": img["_id"],
                "model": "yolov8n",
                "label": int(box.cls),
                "confidence": float(box.conf)
            })

print("✔ YOLOv8n labeling done")
