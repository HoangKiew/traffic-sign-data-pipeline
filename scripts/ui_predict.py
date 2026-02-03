import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import sys
import os

# Thêm đường dẫn để import detector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from processing_labeling.detector import TrafficSignDetector

st.set_page_config(page_title="Traffic Sign Classifier Demo", layout="centered")

st.title("🚦 Traffic Sign Classifier Demo")
st.write("Tải ảnh biển báo (crop) lên để kiểm tra kết quả phân loại của module classification đã train từ pipeline.")

uploaded_file = st.file_uploader("Chọn ảnh biển báo (JPG/PNG)", type=["jpg", "jpeg", "png"])

# --- Load model classification đã train từ pipeline ---
@st.cache_resource
def load_classification_model():
    model_path = "model_classification.pt"
    if not os.path.exists(model_path):
        st.error(f"Không tìm thấy file model: {model_path}\n"
                 "Vui lòng train và export model phân loại (model_classification.pt) vào thư mục này.")
        st.stop()
    model = torch.load(model_path, map_location="cpu")
    model.eval()
    return model

def preprocess_image(img):
    # Resize, normalize, chuyển về tensor (tùy theo pipeline bạn train)
    img_resized = cv2.resize(img, (64, 64))
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_tensor = torch.from_numpy(img_rgb).float().permute(2,0,1) / 255.0
    img_tensor = img_tensor.unsqueeze(0)  # Add batch dim
    return img_tensor

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        st.error("Không đọc được ảnh. Hãy thử lại với file khác.")
        st.stop()

    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Ảnh đã tải lên", use_column_width=True)

    # --- PHÂN LOẠI ---
    model = load_classification_model()
    img_tensor = preprocess_image(img)
    with torch.no_grad():
        logits = model(img_tensor)
        pred = logits.argmax(dim=1).item()
        prob = torch.softmax(logits, dim=1)[0, pred].item()
    st.success(f"Kết quả phân loại: **{CLASS_NAMES[pred]}** (score: {prob:.2f})")

st.markdown("---")
st.info(
    "Module này sử dụng model classification đã train từ pipeline (không phải YOLO). "
    "Hãy upload ảnh crop biển báo (ảnh chỉ chứa 1 biển báo) để kiểm tra kết quả phân loại."
)
