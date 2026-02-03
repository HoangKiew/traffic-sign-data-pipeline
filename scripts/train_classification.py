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

# --- CONFIG ---
CROP_ROOT = "datasets/crops"  # Thư mục chứa các ảnh crop, mỗi class 1 thư mục con: class_0/, class_1/, ...
MODEL_OUT = "model_classification.pt"
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 5
IMG_SIZE = 64
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- DATASET ---
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(CROP_ROOT, transform=transform)
train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)

# --- MODEL ---
model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
model = model.to(DEVICE)

# --- TRAIN ---
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

print(f"Train samples: {len(dataset)} | Classes: {dataset.classes}")
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
# Đảm bảo bạn đã có thư mục datasets/crops/class_0/, class_1/, ..., class_4/
# Mỗi thư mục chứa các ảnh crop thuộc class tương ứng.
# Nếu chưa có, hãy copy ảnh crop từ MinIO về local theo từng class.
