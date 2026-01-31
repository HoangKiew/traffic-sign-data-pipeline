# Đánh giá luồng hoạt động pipeline hiện tại

## 1. **Luồng hoạt động đã có**

### **A. Web Scraping**
- `download_from_web.py` + `data_collection/web_scraper.py`
- Crawl ảnh từ Google/Bing với nhiều từ khóa, upload lên MinIO bucket `traffic-signs-raw`.
- Đã xử lý tốt lỗi thread, retry, batch upload.

### **B. Fast Filtering**
- `fast_filter.py`
- Lọc ảnh rác, trùng lặp, quá nhỏ, tỷ lệ dị dạng trực tiếp trên MinIO bucket `traffic-signs-raw`.
- Ảnh không đạt bị xóa khỏi bucket này.

### **C. Data Cleaning & Preprocessing**
- `main.py`
- Tiền xử lý ảnh (cân bằng sáng, tăng nét, khử nhiễu) trên ảnh từ MinIO bucket `traffic-signs-raw`.
- **Detect biển báo bằng YOLO (mặc định 1 model, thường là yolov8n)**, chỉ upload ảnh có biển báo sang MinIO bucket `traffic-signs-processed`.
- Ảnh gốc ở `traffic-signs-raw` **luôn giữ nguyên, không xóa**.

### **D. Detection & Classification**
- `master_pipeline.py`, `fast_detection.py`
- **Detect biển báo trên ảnh từ MinIO bucket `traffic-signs-processed` bằng 1 model YOLO (yolov8n)**.
- **Phân loại loại biển báo** (Cấm, Nguy hiểm, Hiệu lệnh, Chỉ dẫn, Khác) dựa trên màu sắc hoặc logic riêng.
- **Lưu file nhãn YOLO** vào `datasets/labels/`.

### **E. So sánh 2 model YOLO**
- `master_pipeline.py --dual-metadata`
- **Sau khi đã có ảnh đã xử lý**, pipeline có thể chạy detect song song bằng 2 model YOLO (yolov8n, yolov8x) cho từng ảnh processed.
- **Lưu metadata so sánh** (kết quả từng model) vào MongoDB và file JSON để phân tích sự khác biệt, không phải để phân loại chính thức.

### **F. Labeling & Database Upload**
- `label_data.py`
- Gán nhãn lại (nếu cần) và upload metadata (bounding box, class, confidence, ...) lên MongoDB.

### **G. Visualization**
- `visualize_analytics.py`, `visualize_separate_charts.py`
- Tạo biểu đồ phân tích dataset (phân bố class, kích thước, vị trí, ...).

### **H. Performance & Logging**
- `utils/performance_monitor.py`, `utils/logger.py`
- Theo dõi hiệu năng, log chi tiết, checkpoint, resume pipeline.

---

## 2. **Điểm mạnh hiện tại**
- **Modular**: Mỗi bước tách biệt, dễ chạy lại từng phần.
- **Batch processing**: YOLO, MinIO, MongoDB đều hỗ trợ batch.
- **Error handling tốt**: Retry, skip on error, checkpoint.
- **Không mất dữ liệu gốc**: Ảnh raw luôn giữ nguyên.
- **Có so sánh 2 model YOLO**: Đánh giá chất lượng detect.
- **Visualization đa dạng**: 10+ biểu đồ, phân tích chi tiết.

---

## 3. **Những điểm có thể cải tiến**

### **A. Tự động hóa pipeline hơn nữa**
- Cho phép chạy từng stage hoặc toàn bộ qua unified CLI, hỗ trợ resume chi tiết từng bước.
- Cho phép cấu hình batch size, device, threshold qua CLI hoặc file config.

### **B. Tối ưu hiệu năng**
- Thêm multiprocessing cho bước tiền xử lý (main.py) nếu CPU mạnh.
- Tối ưu batch size tự động theo RAM/VRAM.
- Hỗ trợ streaming lớn (không load hết ảnh vào RAM).

### **C. Metadata & Traceability**
- Gắn thêm thông tin nguồn (source), thời gian crawl, hash ảnh vào metadata từng ảnh (ví dụ: `"source": "Google", "crawled_at": ..., "image_hash": ...`).
- Khi detect bằng 2 model, lưu luôn nhãn của cả 2 model vào metadata từng ảnh (hiện đã có, nhưng có thể chuẩn hóa hơn, ví dụ: `"detections": {"yolov8n": [...], "yolov8x": [...]}`).

### **D. Quản lý dữ liệu tốt hơn**
- Có script dọn dẹp bucket processed (xóa ảnh lỗi, ảnh không có nhãn).
- Có script kiểm tra đồng bộ giữa MinIO và MongoDB (ảnh có nhãn nhưng mất file, hoặc ngược lại).
- **Không xóa ảnh ở bucket raw, chỉ giữ ảnh hợp lệ ở processed.**

### **E. Visualization nâng cao**
- Thêm dashboard realtime (Streamlit, Dash) để xem tiến trình và thống kê.
- Thêm heatmap vị trí biển báo trên ảnh thực tế (dựa trên metadata nhãn).

### **F. Hỗ trợ training lại**
- Tích hợp script train lại YOLO với dữ liệu đã gán nhãn, tự động push model mới vào MinIO/models.

### **G. Đa dạng hóa nguồn dữ liệu**
- Hỗ trợ thêm các nguồn ảnh khác (camera hành trình, Wikimedia, v.v.) và gắn nhãn nguồn vào metadata.

### **H. Kiểm thử & CI/CD**
- Thêm unit test cho các module chính.
- Tích hợp CI/CD để kiểm tra code khi push lên GitHub.

---

## 4. **Tóm tắt đề xuất cải tiến**
- Tự động hóa CLI pipeline, cho phép resume từng bước.
- Tối ưu batch/multiprocessing cho mọi bước.
- Chuẩn hóa metadata, trace nguồn và kết quả detect của nhiều model.
- Thêm script kiểm tra/dọn dẹp dữ liệu.
- Dashboard realtime cho visualize và monitoring.
- Hỗ trợ training lại và quản lý model (train lại YOLO với nhãn mới, push lên MinIO/models).
- Đa dạng hóa nguồn ảnh và metadata (gắn source, thời gian crawl, hash).
- Thêm kiểm thử tự động.
- Thêm heatmap vị trí biển báo thực tế từ metadata.

---

## **Tóm tắt quy trình hiện tại**
1. **YOLO đầu tiên** (thường yolov8n) được dùng để detect biển báo và lọc ảnh hợp lệ (ảnh không có biển báo bị loại khỏi processed).
2. **Sau đó**, pipeline có thể dùng **2 model YOLO** (yolov8n, yolov8x) để detect song song trên ảnh đã qua xử lý, **so sánh kết quả nhận diện** (không phải train lại model, chỉ detect/inference).
3. **Việc phân loại** (class_id) chủ yếu dựa trên logic màu sắc hoặc kết quả detect của model đầu tiên, không phải là train lại 2 model rồi phân loại.

---

## **Lưu ý**
- **Không có bước train lại 2 model YOLO để phân loại** trong pipeline chính. Việc dùng 2 model là để so sánh kết quả detect, không phải để train phân loại mới.
- Nếu muốn train lại 2 model với nhãn mới, cần bổ sung script train riêng biệt.
