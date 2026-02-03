import os
import glob
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')  # Sửa lỗi backend, dùng non-GUI
import matplotlib.pyplot as plt
import json

LABEL_DIR = "datasets/labels"
SPLIT_RATIO = [0.7, 0.15, 0.15]  # train/val/test
SEED = 42

def load_label_info(label_dir):
    files = glob.glob(os.path.join(label_dir, "*.txt"))
    infos = []
    for f in files:
        with open(f) as fin:
            for line in fin:
                if line.startswith("#"): continue
                parts = line.strip().split()
                if len(parts) >= 1:
                    cls = int(parts[0])
                    infos.append({"file": os.path.basename(f), "class": cls})
    df = pd.DataFrame(infos)
    return df

def stratified_split(df, split_ratio, seed=42):
    train_idx, temp_idx = train_test_split(
        df.index, test_size=split_ratio[1]+split_ratio[2], stratify=df['class'], random_state=seed
    )
    val_ratio = split_ratio[1] / (split_ratio[1]+split_ratio[2])
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=1-val_ratio, stratify=df.loc[temp_idx]['class'], random_state=seed
    )
    return train_idx, val_idx, test_idx

def main():
    df = load_label_info(LABEL_DIR)
    print(f"Tổng số object: {len(df)}")
    train_idx, val_idx, test_idx = stratified_split(df, SPLIT_RATIO, SEED)
    split_df = pd.DataFrame(
        [(int(idx), "train") for idx in train_idx] +
        [(int(idx), "val") for idx in val_idx] +
        [(int(idx), "test") for idx in test_idx],
        columns=["index", "split"]
    )
    split_df.to_parquet("split_indices.parquet")
    with open("sampling_report.json", "w") as f:
        json.dump({
            "split_ratio": SPLIT_RATIO,
            "seed": SEED,
            "class_distribution": {
                "train": df.loc[train_idx]['class'].value_counts().to_dict(),
                "val": df.loc[val_idx]['class'].value_counts().to_dict(),
                "test": df.loc[test_idx]['class'].value_counts().to_dict()
            }
        }, f, indent=2)
    # Visualize imbalance
    plt.figure(figsize=(8,5))
    train_dist = df.loc[train_idx]['class'].value_counts().sort_index()
    val_dist = df.loc[val_idx]['class'].value_counts().sort_index()
    test_dist = df.loc[test_idx]['class'].value_counts().sort_index()
    x = np.arange(len(train_dist))
    plt.bar(x-0.2, train_dist.values, width=0.2, label="Train")
    plt.bar(x, val_dist.values, width=0.2, label="Val")
    plt.bar(x+0.2, test_dist.values, width=0.2, label="Test")
    plt.xticks(x, [str(i) for i in train_dist.index])
    plt.ylabel("Số lượng")
    plt.title("Class Distribution by Split")
    plt.legend()
    plt.tight_layout()
    plt.savefig("split_class_distribution.png", dpi=150)
    plt.close()
    print("✅ Đã lưu split_indices.parquet, sampling_report.json, split_class_distribution.png")

if __name__ == "__main__":
    main()
