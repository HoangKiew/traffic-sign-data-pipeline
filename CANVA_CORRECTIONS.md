# 🔴 CANVA PRESENTATION - DANH SÁCH SỬA CHỮA

## 📊 TỔNG QUAN

Đây là danh sách các điểm **SAI/THIẾU** trong Canva presentation so với project thực tế, cần sửa lại để đảm bảo tính chính xác.

---

## ❌ PHẢI SỬA NGAY (Sai số liệu)

### 1. **Slide 7: Dataset Size - SAI SỐ LIỆU**

**Hiện tại (SAI)**:
- Tổng ảnh sau clean: **1,888 images**
- Raw images: **~3,150**
- Duplicates removed: **1,262**

**Cần sửa thành**:
- Tổng ảnh sau clean: **1,433 images** ✏️
- Raw images: **2,695** ✏️
- Duplicates removed: **1,262** ✅ (ĐÚNG)

---

### 2. **Slide 8-9: Category Distribution - SAI SỐ LƯỢNG**

**Hiện tại (SAI)**:
- Balanced data: ~244-245 images/category

**Cần sửa thành**:
- **informative**: 415 ảnh ✏️
- **mandatory**: 367 ảnh ✏️
- **prohibitory**: 357 ảnh ✏️
- **warning**: 294 ảnh ✏️

**Lưu ý**: Dataset **KHÔNG CÂN BẰNG HOÀN TOÀN** (khác nhau 294-415), không phải 244-245 như slide hiện tại.

---

## ⚠️ NÊN THÊM (Tính năng quan trọng)

### 3. **Slide 7: THIẾU Perceptual Hash**

**Hiện tại**: Chỉ đề cập MD5 hash

**Cần thêm**:
```
Duplicate Detection:
✅ MD5 Hash: Phát hiện ảnh trùng lặp hoàn toàn (exact duplicates)
✅ Perceptual Hash: Phát hiện ảnh tương tự (similar images)
   - Tìm ảnh giống nhau nhưng khác resolution/format
   - Threshold: 5 (Hamming distance)
   - Tool: imagehash library
```

---

### 4. **Slide 7: THIẾU Blur Detection**

**Hiện tại**: Không đề cập

**Cần thêm**:
```
Quality Control:
✅ Blur Detection: Laplacian Variance
   - Method: cv2.Laplacian() variance
   - Threshold: 100.0
   - Loại bỏ ảnh mờ để đảm bảo chất lượng dataset
```

---

### 5. **Slide mới: THIẾU MongoDB Integration**

**Hiện tại**: Không đề cập storage solution

**Cần thêm slide mới**:
```
Data Integration - MongoDB Atlas

✅ Database: traffic_signs_db
✅ Collection: images
✅ Storage:
   - Metadata: filename, category, width, height, size, format
   - Image bytes: Binary format (BSON)
   - MD5 hash: Duplicate tracking

Ưu điểm:
- Scalable storage
- Query metadata nhanh
- Production-ready
```

---

### 6. **Slide 5: Tools & Technologies - THIẾU**

**Hiện tại**:
- Python, Pandas, Matplotlib, Seaborn
- Selenium, Requests, BeautifulSoup
- OpenCV

**Cần thêm**:
```
Tools & Technologies:

Data Collection:
- Selenium, BeautifulSoup, Requests

Data Processing:
- Pandas, NumPy
- OpenCV, Pillow (PIL)
- imagehash ← THÊM MỚI
- pymongo ← THÊM MỚI

Visualization:
- Matplotlib, Seaborn

Utilities:
- tqdm (Progress bars) ← THÊM MỚI
```

---

### 7. **Slide mới: THIẾU Data Sources**

**Hiện tại**: Không rõ nguồn dữ liệu

**Cần thêm slide mới**:
```
Data Collection - Sources

Source 1: Google Images
- Method: Selenium WebDriver
- Automated scrolling & clicking
- 5 queries per category

Source 2: Bing Images  
- Method: BeautifulSoup + Requests
- Fallback khi Google không đủ
- 5 queries per category

Total Queries: 20 queries
- prohibitory: 5 queries
- warning: 5 queries
- mandatory: 5 queries
- informative: 5 queries

Kết quả: 2,695 raw images
```

---

### 8. **Slide mới: THIẾU Train/Val/Test Split**

**Hiện tại**: Không đề cập

**Cần thêm slide mới**:
```
Data Split - Train/Validation/Test

✅ Stratified Split theo category
✅ Tỷ lệ: 70% / 15% / 15%

Kết quả:
- Train: 1,000 ảnh (70%)
- Validation: 215 ảnh (15%)
- Test: 218 ảnh (15%)

Đặc điểm:
- Giữ tỷ lệ category cho mỗi split
- Xử lý edge cases (category có ít ảnh)
- Random seed: 42 (reproducible)
```

---

## 🔄 CẬP NHẬT (Hoàn thiện)

### 9. **Slide 7: Average Image Size - CẦN KIỂM TRA**

**Hiện tại**: 
- Average width: ~238px
- Average height: ~302px

**Cần làm**:
1. Chạy: `python src/visualization/visualizer.py`
2. Kiểm tra file: `reports/figures/thong_ke_mean_median_std.png`
3. Cập nhật số liệu chính xác vào slide

---

### 10. **Slide 17: Future Work - CẬP NHẬT**

**Hiện tại**:
- Mở rộng dataset >5,000 ảnh
- Data Augmentation
- Train CNN/YOLO models
- Automation với Airflow/Docker

**Cần sửa thành**:
```
Completed Features:
✅ MongoDB integration
✅ Blur detection (Laplacian variance)
✅ Perceptual hash (similar image detection)
✅ Automated scraping (Google + Bing)

Future Work:
⏳ Mở rộng dataset >2,000 ảnh
⏳ Normalization (pixel scaling [0,1])
⏳ Data Augmentation (flip, rotate, brightness)
⏳ Feature Extraction (CNN pretrained: EfficientNet/ResNet)
⏳ Model Training (Classification: LogReg/SVM/CNN)
⏳ Model Evaluation (Confusion Matrix, Metrics)
⏳ Deployment (Airflow/Docker automation)
```

---

## 📋 CHECKLIST SỬA CANVA

### **BẮT BUỘC** (Sai số liệu - Ưu tiên cao):
- [ ] **Slide 7**: Sửa 1,888 → **1,433 ảnh**
- [ ] **Slide 7**: Sửa ~3,150 → **2,695 ảnh raw**
- [ ] **Slide 8-9**: Sửa category distribution (415/367/357/294)

### **KHUYẾN NGHỊ** (Tính năng quan trọng - Ưu tiên trung bình):
- [ ] **Slide 7**: Thêm **Perceptual Hash**
- [ ] **Slide 7**: Thêm **Blur Detection**
- [ ] **Slide 5**: Thêm tools (pymongo, imagehash, tqdm)

### **TÙY CHỌN** (Hoàn thiện - Ưu tiên thấp):
- [ ] **Slide mới**: Thêm **MongoDB Integration**
- [ ] **Slide mới**: Thêm **Data Sources** (Google + Bing)
- [ ] **Slide mới**: Thêm **Train/Val/Test Split**
- [ ] **Slide 17**: Cập nhật **Future Work**

---

## 🎯 3 ĐIỀU QUAN TRỌNG NHẤT

1. ❌ **Số liệu dataset SAI**: 1,888 → **1,433 ảnh** (PHẢI SỬA)
2. ⚠️ **THIẾU Perceptual Hash** (tính năng độc đáo)
3. ⚠️ **THIẾU Blur Detection** (tính năng độc đáo)

---

## 📝 GHI CHÚ

- **Perceptual Hash** và **Blur Detection** là 2 tính năng **VƯỢT TRỘI** so với các project khác
- **MongoDB Integration** cho thấy tính **production-ready** của project
- Dataset **KHÔNG CÂN BẰNG HOÀN TOÀN** nhưng vẫn ở mức chấp nhận được (294-415)

---

**Ngày tạo**: 2026-01-16  
**Mục đích**: Sửa chữa Canva presentation cho chính xác với project thực tế
