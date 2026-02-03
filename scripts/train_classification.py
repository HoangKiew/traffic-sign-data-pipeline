"""
Train classification model từ ảnh crop đã chuẩn bị bởi pipeline.
Sinh ra file model_classification.pt để dùng cho inference/Streamlit UI.
"""

import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, datasets, models
from torch.utils.data import DataLoader
from tqdm import tqdm

# --- Thêm import cho MinIO và PIL ---
from minio import Minio
from io import BytesIO
from PIL import Image

# --- CONFIG ---
CROP_ROOT = "datasets/crops"  # Nếu train local, giữ nguyên. Nếu train từ MinIO, không dùng biến này.
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "traffic-signs-crop-n"  # Đổi tên bucket nếu cần
MODEL_OUT = "model_classification.pt"
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 5
IMG_SIZE = 64
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- DATASET TỪ MINIO ---
class MinioImageDataset(torch.utils.data.Dataset):
    def __init__(self, minio_client, bucket, transform=None):
        self.minio_client = minio_client
        self.bucket = bucket
        self.transform = transform
        self.samples = []
        objects = minio_client.list_objects(bucket, recursive=True)
        for obj in objects:
            if obj.object_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                parts = obj.object_name.split('/')
                if len(parts) >= 2 and parts[0].startswith('class_'):
                    class_idx = int(parts[0].replace('class_', ''))
                    self.samples.append((obj.object_name, class_idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        object_name, class_idx = self.samples[idx]
        resp = self.minio_client.get_object(self.bucket, object_name)
        img_bytes = resp.read()
        img = Image.open(BytesIO(img_bytes)).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, class_idx

# --- CHỌN NGUỒN DỮ LIỆU ---
USE_MINIO = True  # Đặt True để train trực tiếp từ MinIO, False để train local

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

if USE_MINIO:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    dataset = MinioImageDataset(minio_client, MINIO_BUCKET, transform=transform)
    if len(dataset) == 0:
        print("❌ Không tìm thấy ảnh crop nào trong bucket MinIO!")
        print(f"Kiểm tra lại bucket: {MINIO_BUCKET}")
        print("Gợi ý:")
        print(" - Đảm bảo đã chạy xong các bước detect/crop (main.py) và gán nhãn (label_data.py --dual-yolo).")
        print(" - Kiểm tra bucket trên MinIO Console (http://localhost:9001) xem có dữ liệu class_*/xxx.jpg chưa.")
        print(" - Nếu chưa có, hãy chạy lại pipeline hoặc kiểm tra scripts/label_data.py.")
        print(" - Đảm bảo bạn chạy label_data.py với --dual-yolo để sinh crop phân loại vào bucket này.")
        exit(1)
else:
    dataset = datasets.ImageFolder(CROP_ROOT, transform=transform)
    if len(dataset) == 0:
        print("❌ Không tìm thấy ảnh crop nào trong thư mục local!")
        print(f"Kiểm tra lại thư mục: {CROP_ROOT}")
        exit(1)

train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)

# --- MODEL ---
model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
model = model.to(DEVICE)

# --- TRAIN ---
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

print(f"Train samples: {len(dataset)} | Classes: {getattr(dataset, 'classes', 'from MinIO')}")
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for imgs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * imgs.size(0)
        _, preds = outputs.max(1)
        correct += (preds == labels).sum().item()
        total += imgs.size(0)
    print(f"Epoch {epoch+1}: Loss={running_loss/total:.4f} | Acc={correct/total:.4f}")

# --- SAVE ---
torch.save(model, MODEL_OUT)
print(f"✅ Đã lưu model classification: {MODEL_OUT}")

# --- HƯỚNG DẪN CHUẨN BỊ DỮ LIỆU ---
# Nếu train local: Đảm bảo bạn đã có thư mục datasets/crops/class_0/, class_1/, ..., class_4/
# Nếu train từ MinIO: Đảm bảo bucket {MINIO_BUCKET} có cấu trúc class_0/xxx.jpg, class_1/xxx.jpg, ...
