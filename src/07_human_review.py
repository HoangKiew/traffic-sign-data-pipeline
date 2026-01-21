from db import consensus_col

for doc in consensus_col.find({"status": "conflict"}):
    consensus_col.update_one(
        {"_id": doc["_id"]},
        {"$set": {"final_label": "manual_label", "status": "human"}}
    )

print("✔ Human review done")
