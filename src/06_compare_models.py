from db import images_col, annotations_col, consensus_col

for img in images_col.find({"stage": "transformed"}):
    annos = list(annotations_col.find({"image_id": img["_id"]}))

    try:
        a = next(x for x in annos if x["model"] == "yolov8n")
        b = next(x for x in annos if x["model"] == "yolov8s")
    except StopIteration:
        continue

    if a["label"] == b["label"]:
        consensus_col.insert_one({
            "image_id": img["_id"],
            "final_label": a["label"],
            "status": "auto",
            "models": ["yolov8n", "yolov8s"]
        })
    else:
        consensus_col.insert_one({
            "image_id": img["_id"],
            "final_label": None,
            "status": "conflict",
            "models": ["yolov8n", "yolov8s"]
        })

print("✔ Model comparison done")
