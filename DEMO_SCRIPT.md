# 🎬 SCRIPT DEMO CHO THẦY

## 📋 Chuẩn bị trước khi demo

### 1. Kiểm tra dữ liệu
```bash
# Đếm số ảnh
ls data\raw\*\*.jpg | Measure-Object | Select-Object -ExpandProperty Count
```

**Kết quả mong đợi:** ~199 ảnh (hoặc nhiều hơn nếu đã scrape thêm)

### 2. Activate venv
```bash
.\venv\Scripts\Activate.ps1
```

---

## 🎬 DEMO PIPELINE (5-10 phút)

### **Bước 1: Giới thiệu project** (1 phút)

**Nói với thầy:**
> "Thưa thầy, em xin demo đề tài **'Xây dựng Data Pipeline Thu thập và Xử lý Dữ liệu Hình ảnh Biển báo Giao thông'**
> 
> Pipeline gồm 3 bước chính:
> 1. **Data Collection** - Thu thập dữ liệu bằng web scraping
> 2. **Data Cleaning** - Làm sạch và phát hiện duplicates
> 3. **Data Visualization** - Trực quan hóa dữ liệu"

---

### **Bước 2: Chạy Pipeline** (2-3 phút)

**Chạy lệnh:**
```bash
python main.py
```

**Giải thích trong khi chạy:**
> "Em đang chạy pipeline tự động. Pipeline sẽ:
> 1. Đọc 199 ảnh từ `data/raw/`
> 2. Tạo metadata với pandas
> 3. Tính MD5 hash để phát hiện duplicates
> 4. Tính Perceptual hash để phát hiện ảnh tương tự
> 5. Phân tích dữ liệu (info, describe, outliers)
> 6. Tạo 4 biểu đồ visualization"

**Output sẽ hiển thị:**
```
🚀 BẮT ĐẦU PIPELINE
============================================================

🧹 STEP 1: Data Cleaning + Hash Detection
----------------------------------------------------------------------
📊 Đang tạo metadata từ raw images...
✓ Đã tạo metadata cho 199 images

🔐 Đang tính MD5 hash...
✓ Đã tính MD5 hash cho 199 images

🎨 Đang tính Perceptual hash...
✓ Đã tính Perceptual hash cho 199 images

🔍 Tìm exact duplicates (MD5)...
✓ Không có ảnh trùng lặp

🔎 Tìm similar images (threshold=5)...
⚠️  Tìm thấy 2 nhóm ảnh tương tự

📋 THÔNG TIN DỮ LIỆU (df.info())
...

✅ STEP 1 HOÀN TẤT!

📊 STEP 2: Data Visualization
----------------------------------------------------------------------
✓ Đã lưu: reports\figures\category_distribution.png
✓ Đã lưu: reports\figures\size_histogram.png
✓ Đã lưu: reports\figures\scatter_width_height.png
✓ Đã lưu: reports\figures\statistics_summary.png

✅ STEP 2 HOÀN TẤT!

🎉 PIPELINE HOÀN TẤT!
```

---

### **Bước 3: Show kết quả** (3-4 phút)

#### A. Metadata CSV
```bash
notepad data\metadata.csv
```

**Giải thích:**
> "Đây là file metadata.csv chứa thông tin đầy đủ về 199 ảnh:
> - Đường dẫn file
> - Category (prohibitory, warning, mandatory, informative)
> - Kích thước (width, height)
> - MD5 hash (phát hiện duplicates)
> - Perceptual hash (phát hiện ảnh tương tự)"

#### B. Biểu đồ Visualization
```bash
explorer reports\figures
```

**Mở từng biểu đồ và giải thích:**

**1. category_distribution.png**
> "Biểu đồ phân bố category cho thấy:
> - Informative: 114 ảnh (nhiều nhất)
> - Mandatory: 53 ảnh
> - Prohibitory: 22 ảnh
> - Warning: 10 ảnh (ít nhất)
> 
> → Dữ liệu **không cân bằng** (imbalanced)"

**2. size_histogram.png**
> "Histogram kích thước ảnh:
> - Phần lớn ảnh có kích thước 120x120px
> - Có một số ảnh lớn hơn (3072x2304px)
> - → Cần resize về kích thước chuẩn"

**3. scatter_width_height.png**
> "Scatter plot Width vs Height:
> - Hầu hết ảnh có tỷ lệ gần vuông (width ≈ height)
> - Phân bố theo từng category
> - Dễ nhận diện outliers"

**4. statistics_summary.png**
> "Thống kê tổng hợp:
> - Mean, median, std của width/height
> - Box plot phát hiện outliers
> - Pie chart phân bố category"

---

### **Bước 4: Trả lời câu hỏi thầy** (2-3 phút)

#### Câu hỏi thường gặp:

**Q1: "Em lấy dữ liệu từ đâu?"**
> "Dạ em sử dụng **web scraping** từ 4 nguồn:
> 1. Wikipedia tiếng Việt
> 2. Wikimedia Commons
> 3. VoPhuToan.com (QCVN 41:2019)
> 4. ThuVienPhapLuat.vn
> 
> Công nghệ: Python với **Requests** và **BeautifulSoup**"

**Q2: "Tại sao chỉ 199 ảnh?"**
> "Dạ 199 ảnh là dữ liệu **raw** ban đầu. Em có thể:
> 1. Scrape thêm từ Google Images (có script sẵn)
> 2. Dùng **Data Augmentation** để tăng lên ~1000 ảnh
> 
> Với visualization thì 199 ảnh là **đủ** để phân tích"

**Q3: "Có phát hiện duplicates không?"**
> "Dạ có! Em dùng 2 phương pháp:
> 1. **MD5 hash** - Phát hiện ảnh trùng lặp hoàn toàn (0 duplicates)
> 2. **Perceptual hash** - Phát hiện ảnh tương tự (2 nhóm similar)
> 
> → Dữ liệu khá sạch"

**Q4: "Bước tiếp theo là gì?"**
> "Dạ em sẽ:
> 1. **Image Preprocessing** - Resize về 64x64px, split train/val/test
> 2. **Data Augmentation** - Tăng dữ liệu lên ~1000 ảnh
> 3. **Model Training** - Train CNN để phân loại (optional)
> 
> Nhưng phần chính là **Data Pipeline** đã hoàn thành"

---

## 📊 BACKUP PLAN (Nếu có lỗi)

### Nếu `main.py` lỗi:
```bash
# Chạy từng bước
python src/data_processing/cleaner.py
python src/visualization/visualizer.py
```

### Nếu không có dữ liệu:
```bash
# Scrape nhanh
python src/data_collection/scraper.py
```

### Nếu thiếu thư viện:
```bash
pip install -r requirements.txt
```

---

## ✅ CHECKLIST DEMO

**Trước khi demo:**
- [ ] Đã có dữ liệu trong `data/raw/`
- [ ] Đã activate venv
- [ ] Đã test chạy `python main.py` một lần
- [ ] Đã xem trước các biểu đồ
- [ ] Đã đọc `ANSWER_FOR_TEACHER.md`

**Trong khi demo:**
- [ ] Giải thích rõ ràng từng bước
- [ ] Show output trong console
- [ ] Mở metadata.csv
- [ ] Mở từng biểu đồ và giải thích
- [ ] Trả lời câu hỏi tự tin

**Sau demo:**
- [ ] Hỏi thầy có câu hỏi gì không
- [ ] Sẵn sàng show code nếu thầy muốn

---

## 💡 TIPS

1. **Nói chậm, rõ ràng** - Thầy cần hiểu
2. **Show kết quả trước, code sau** - Kết quả quan trọng hơn
3. **Nhấn mạnh công nghệ** - Requests, BeautifulSoup, Pandas, Matplotlib
4. **Giải thích vấn đề** - Imbalanced data, outliers
5. **Tự tin** - Bạn đã làm tốt rồi!

---

## 🎬 SCRIPT MẪU

**Mở đầu:**
> "Thưa thầy, em xin phép demo đề tài. Em sẽ chạy pipeline tự động để thầy thấy kết quả."

**Trong khi chạy:**
> "Pipeline đang chạy... Em thấy nó đang tạo metadata... tính hash... phát hiện duplicates... tạo biểu đồ..."

**Show kết quả:**
> "Đây là metadata.csv... Đây là 4 biểu đồ visualization... Thầy thấy biểu đồ này cho thấy dữ liệu không cân bằng..."

**Kết thúc:**
> "Em xin cảm ơn thầy đã xem. Thầy có câu hỏi gì cho em không ạ?"

---

**Chúc bạn demo thành công! 🎉**
