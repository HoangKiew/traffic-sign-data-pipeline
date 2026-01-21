from db import consensus_col

total = consensus_col.count_documents({})
auto = consensus_col.count_documents({"status": "auto"})
human = consensus_col.count_documents({"status": "human"})

print("Total samples:", total)
print("Auto accepted:", auto)
print("Human reviewed:", human)

if total > 0:
    print("Auto ratio:", round(auto / total, 2))
