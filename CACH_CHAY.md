# 🚀 HƯỚNG DẪN CHẠY PIPELINE

## 📋 Tổng quan

Pipeline đơn giản gồm **3 bước**:
1. **Scraping** - Cào dữ liệu từ trình duyệt
2. **Cleaning** - Làm sạch dữ liệu
3. **Visualization** - Tạo biểu đồ

---

## ⚙️ BƯỚC 1: CÀI ĐẶT

### 1.1. Tạo Virtual Environment

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (CMD):**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

✅ **Kiểm tra:** Dòng lệnh sẽ có `(venv)` ở đầu

### 1.2. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

⏱️ **Thời gian:** ~2-3 phút

---

## 🌐 BƯỚC 2: SCRAPING (Thu thập dữ liệu)

### Cách 1: Chạy Scraper riêng (Khuyên dùng)

```bash
python src/data_collection/scraper.py
```

**Kết quả:**
- Ảnh được lưu vào `data/raw/<category>/`
- 4 categories: prohibitory, warning, mandatory, informative

### Cách 2: Thêm URLs vào code

1. Mở file `src/data_collection/scraper.py`
2. Thêm URLs bạn muốn scrape:

```python
scraper = TrafficSignScraper()
scraper.scrape_website('https://example.com/traffic-signs', 'prohibitory')
scraper.scrape_website('https://example.com/warning-signs', 'warning')
# ... thêm các URLs khác
```

3. Chạy lại:
```bash
python src/data_collection/scraper.py
```

⏱️ **Thời gian:** ~30-60 phút (tùy số lượng ảnh)

✅ **Kiểm tra:** Xem ảnh trong `data/raw/`

---

## 🚀 BƯỚC 3: CHẠY PIPELINE CHÍNH

### Chạy toàn bộ pipeline (Scraping → Cleaning → Visualization)

```bash
python main.py
```

**Pipeline sẽ tự động:**
1. ✅ Kiểm tra dữ liệu trong `data/raw/`
2. ✅ Làm sạch dữ liệu → `data/metadata.csv`
3. ✅ Tạo 4 biểu đồ → `reports/figures/`

⏱️ **Thời gian:** ~2-5 phút

---

## 📊 KẾT QUẢ

Sau khi chạy `python main.py`, bạn sẽ có:

### 1. Metadata (`data/metadata.csv`)
- Bảng thông tin đầy đủ về tất cả ảnh
- Các cột: image_path, filename, category, width, height, format, size_kb, md5_hash, phash

### 2. Biểu đồ (`reports/figures/`)
- ✅ `category_distribution.png` - Phân bố số lượng theo category
- ✅ `size_histogram.png` - Histogram kích thước ảnh
- ✅ `scatter_width_height.png` - Scatter plot Width vs Height
- ✅ `statistics_summary.png` - Thống kê tổng hợp (mean, median, std)

---

## 📖 XEM KẾT QUẢ

### Xem Metadata

**Windows:**
```bash
notepad data\metadata.csv
```

**Linux/Mac:**
```bash
cat data/metadata.csv
```

**Hoặc mở bằng Excel/LibreOffice**

### Xem Biểu đồ

**Windows:**
```bash
explorer reports\figures
```

**Linux:**
```bash
xdg-open reports/figures
```

**Mac:**
```bash
open reports/figures
```

---

## 🔄 WORKFLOW HOÀN CHỈNH

```bash
# Bước 1: Cài đặt
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Bước 2: Scraping (nếu chưa có dữ liệu)
python src/data_collection/scraper.py

# Bước 3: Chạy pipeline
python main.py

# Bước 4: Xem kết quả
explorer reports\figures
notepad data\metadata.csv
```

---

## ⚠️ LƯU Ý

### 1. Nếu chưa có dữ liệu
- Pipeline sẽ hỏi bạn có muốn scrape không
- Hoặc chạy `python src/data_collection/scraper.py` trước

### 2. Nếu đã có dữ liệu trong `data/raw/`
- Pipeline sẽ tự động sử dụng dữ liệu có sẵn
- Bỏ qua bước scraping

### 3. Lỗi thường gặp

**Lỗi: "ModuleNotFoundError"**
```bash
# Đảm bảo đã activate venv
venv\Scripts\activate

# Cài đặt lại dependencies
pip install -r requirements.txt
```

**Lỗi: "No images found"**
```bash
# Chạy scraper trước
python src/data_collection/scraper.py
```

**Lỗi: "Permission denied"**
- Kiểm tra quyền ghi file trong thư mục `data/` và `reports/`
- Chạy terminal với quyền Administrator (Windows)

---

## ✅ CHECKLIST

- [ ] Đã tạo và activate virtual environment
- [ ] Đã cài đặt dependencies (`pip install -r requirements.txt`)
- [ ] Đã có dữ liệu trong `data/raw/` (hoặc đã chạy scraper)
- [ ] Đã chạy `python main.py`
- [ ] Đã kiểm tra `data/metadata.csv`
- [ ] Đã xem biểu đồ trong `reports/figures/`

---

## 💡 TIPS

1. **Scraping nhiều nguồn:** Thêm nhiều URLs vào scraper để có dữ liệu đa dạng
2. **Kiểm tra metadata:** Xem `data/metadata.csv` để hiểu dữ liệu trước khi visualization
3. **Biểu đồ chất lượng:** Tất cả biểu đồ được lưu ở 300 DPI, sẵn sàng cho báo cáo

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra file `HUONG_DAN_DON_GIAN.md` - Hướng dẫn chi tiết
2. Kiểm tra console output để xem lỗi cụ thể
3. Đảm bảo đã cài đặt đầy đủ dependencies

---

**Chúc bạn thành công! 🎉**

