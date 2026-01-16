# KỊCH BẢN DEMO DỰ ÁN - CHI TIẾT

## 🎯 CHUẨN BỊ TRƯỚC KHI DEMO

### Checklist:
- [ ] Mở terminal tại `d:\1.KTDL`
- [ ] Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- [ ] Mở VS Code với project
- [ ] Chuẩn bị 6 ảnh biểu đồ trong `reports/figures/`
- [ ] Kiểm tra `data/metadata.csv` có 530 dòng
- [ ] Kiểm tra `data/processed/` có train/val/test

---

## PHẦN 1: GIỚI THIỆU (2 phút)

### Lời nói:
> "Chào thầy/cô! Em xin phép trình bày dự án **Xây dựng Data Pipeline Thu thập và Xử lý Dữ liệu Hình ảnh Biển báo Giao thông**."

> "Mục tiêu của em là thu thập dữ liệu biển báo giao thông Việt Nam từ web, làm sạch, phân tích và chuẩn bị dataset cho machine learning."

### Thao tác:
1. Mở PowerPoint slide (nếu có)
2. Hoặc mở file `OUTLINE_SLIDE.md`

---

## PHẦN 2: DEMO THU THẬP DỮ LIỆU (5 phút)

### 2.1. Giải thích phương pháp

**Lời nói:**
> "Em sử dụng **Web Scraping** để thu thập dữ liệu. Cụ thể, em dùng **Selenium WebDriver** để scrape động từ Google Images."

### Thao tác:
```powershell
# Mở file scraper
code medium_scraper.py
```

**Giải thích code (chỉ vào màn hình):**
- Dòng 24-30: Setup Selenium với Chrome headless
- Dòng 45-80: Hàm scrape_google_images - scroll và lấy ảnh
- Dòng 33-43: Hàm download_and_save - validate và lưu ảnh
- Dòng 110-140: 24 queries khác nhau cho 4 categories

**Lời nói:**
> "Em có 24 queries khác nhau, mỗi query tìm kiếm từ khóa như 'biển cấm giao thông việt nam', 'prohibitory traffic signs vietnam', v.v."

> "Selenium sẽ tự động scroll xuống để load thêm ảnh, sau đó lấy URL và download về."

### 2.2. Demo chạy scraper (OPTIONAL - nếu thầy muốn xem)

**Lời nói:**
> "Nếu thầy muốn, em có thể demo chạy scraper. Tuy nhiên vì mất 1-2 giờ nên em đã chạy sẵn rồi ạ."

**Nếu demo:**
```powershell
python medium_scraper.py
# Chờ 10-20 giây rồi Ctrl+C
```

**Giải thích output:**
- "SCRAPING..." - Bắt đầu
- "Selenium khởi động thành công" - WebDriver ready
- "bien cam giao thong viet nam" - Query đang chạy
- "-> 19 anh" - Kết quả

---

## PHẦN 3: DEMO DATA CLEANING (7 phút)

### 3.1. Xem dữ liệu raw

**Lời nói:**
> "Sau khi scraping, em có 815 ảnh raw trong thư mục `data/raw/`"

**Thao tác:**
```powershell
# Đếm số file
(Get-ChildItem -Path data\raw -Recurse -File).Count
# Output: 815
```

**Giải thích:**
> "Dữ liệu raw này có nhiều vấn đề: duplicate, outliers, ảnh quá nhỏ. Em cần làm sạch."

### 3.2. Giải thích code cleaning

**Thao tác:**
```powershell
code src\data_processing\clean.py
```

**Giải thích từng phần (chỉ vào code):**

**1. Tạo metadata (dòng 40-65):**
> "Em duyệt qua tất cả ảnh, lấy thông tin: filename, category, width, height, size_kb"

**2. Tính MD5 hash (dòng 67-78):**
> "Em tính MD5 hash cho mỗi ảnh để phát hiện duplicate. Nếu 2 ảnh giống hệt nhau, hash sẽ giống nhau."

**3. Phát hiện duplicate (dòng 102-122):**
> "Em tìm thấy 285 ảnh trùng lặp và loại bỏ chúng."

**4. Phát hiện outliers (dòng 208-249):**
> "Em dùng phương pháp IQR để tìm outliers. Phát hiện 62 outliers về width và 58 về height."

**5. Resize và split (dòng 339-377):**
> "Em resize tất cả ảnh về 64x64 pixels và chia thành train/val/test theo tỉ lệ 70/15/15."

### 3.3. Demo chạy cleaning

**Lời nói:**
> "Bây giờ em sẽ demo chạy cleaning. Vì đã chạy rồi nên em sẽ chạy lại để thầy xem output."

**Thao tác:**
```powershell
python src\data_processing\clean.py
```

**Giải thích output khi chạy:**

1. **"Đang tạo metadata..."**
   > "Đang đọc thông tin 815 ảnh"

2. **"Đang tính MD5 hash..."**
   > "Tính hash để detect duplicate"

3. **"Tìm thấy 439 ảnh trùng lặp"**
   > "Đây là danh sách các nhóm ảnh trùng. Ví dụ Hash 00f9960a có 3 ảnh giống nhau."

4. **"df.info()"**
   > "Thông tin dataset: 815 entries, 9 columns, không có missing values"

5. **"df.describe()"**
   > "Thống kê: Mean width 188px, Median 156px, Std 213px. Mean > Median chứng tỏ có outliers."

6. **"Phân bố theo category"**
   > "informative: 238, prohibitory: 219, mandatory: 183, warning: 175. Khá cân bằng."

7. **"Phát hiện outliers"**
   > "62 outliers width, 58 outliers height. Đây là những ảnh quá lớn hoặc quá nhỏ."

8. **"Đã loại bỏ 285 exact duplicates"**
   > "Từ 815 ảnh xuống còn 530 ảnh sạch."

9. **"Chia dataset: Train 368, Val 81, Test 81"**
   > "Chia theo tỉ lệ 70/15/15 cho từng category."

10. **"Đang xử lý train set... 368/368 ảnh"**
    > "Resize và lưu vào data/processed/"

### 3.4. Xem kết quả

**Thao tác:**
```powershell
# Xem metadata
code data\metadata.csv
```

**Giải thích:**
> "File metadata.csv có 530 dòng (sau khi loại duplicate), 9 cột: image_path, filename, category, width, height, format, mode, size_kb, md5_hash."

**Thao tác:**
```powershell
# Xem processed
ls data\processed\train\
```

**Giải thích:**
> "Thư mục processed có train/val/test, mỗi thư mục có 4 categories. Tất cả ảnh đã resize về 64x64."

---

## PHẦN 4: DEMO VISUALIZATION (5 phút)

### 4.1. Giải thích code visualization

**Thao tác:**
```powershell
code src\visualization\visualizer.py
```

**Giải thích:**
> "Em tạo 6 biểu đồ để phân tích dataset:"
> "1. Phân bố category - Bar chart"
> "2. Histogram kích thước - Width và Height"
> "3. Scatter plot - Width vs Height"
> "4. Box plot - Phát hiện outliers"
> "5. Mean/Median/Std - So sánh thống kê"
> "6. File size distribution - Phân bố kích thước file"

### 4.2. Demo chạy visualization

**Thao tác:**
```powershell
python src\visualization\visualizer.py
```

**Giải thích output:**
> "Đã tạo 6 file PNG trong reports/figures/"

### 4.3. Xem và giải thích từng biểu đồ

**Mở từng ảnh và giải thích:**

**1. phan_bo_category.png**
> "Biểu đồ này cho thấy phân bố số lượng ảnh theo category. Dataset khá cân bằng, informative nhiều nhất 238 ảnh, warning ít nhất 175 ảnh."

**2. histogram_kich_thuoc.png**
> "2 histogram cho width và height. Hầu hết ảnh tập trung ở 120-162px (width) và 106-140px (height). Có một số outliers rất lớn."

**3. bieu_do_width_height.png**
> "Scatter plot cho thấy mối quan hệ giữa width và height. Các điểm phân tán theo đường chéo, chứng tỏ ảnh rộng thì cao. Không phân biệt rõ category theo kích thước."

**4. box_plot_width_height.png**
> "Box plot cho thấy median, Q1, Q3 và outliers. Median width 156px, height 121px. Có nhiều outliers phía trên (ảnh quá lớn)."

**5. thong_ke_mean_median_std.png**
> "So sánh Mean, Median, Std. Mean > Median chứng tỏ có outliers kéo giá trị lên. Std cao chứng tỏ dữ liệu phân tán."

**6. phan_bo_file_size.png**
> "Histogram file size. Hầu hết ảnh 7-12 KB, rất nhẹ. Mean 20 KB. Có 1 outlier 3150 KB rất nặng."

---

## PHẦN 5: DEMO PYTHON PANDAS (3 phút)

### 5.1. Mở Python interactive

**Thao tác:**
```powershell
python
```

### 5.2. Demo các lệnh pandas

**Lời nói:**
> "Em sẽ demo một số lệnh pandas để phân tích dữ liệu."

**Code demo:**
```python
import pandas as pd

# Đọc metadata
df = pd.read_csv('data/metadata.csv')

# 1. df.info()
df.info()
# Giải thích: "530 entries, 9 columns, không có null"

# 2. df.describe()
df.describe()
# Giải thích: "Thống kê mô tả: mean, std, min, max, quartiles"

# 3. Phân bố category
df['category'].value_counts()
# Giải thích: "informative: 238, prohibitory: 219, ..."

# 4. Lọc outliers
outliers = df[df['width'] > 1000]
print(f"Số outliers: {len(outliers)}")
# Giải thích: "Có X ảnh có width > 1000px"

# 5. Tính mean theo category
df.groupby('category')['width'].mean()
# Giải thích: "Mean width của từng category"

# Thoát
exit()
```

---

## PHẦN 6: TRẢ LỜI CÂU HỎI (5 phút)

### Câu hỏi dự kiến và cách trả lời:

**Q1: "Em lấy dữ liệu từ đâu?"**
> "Em scrape từ Google Images bằng Selenium WebDriver. Em có 24 queries khác nhau cho 4 loại biển báo."

**Q2: "Tại sao có nhiều duplicate?"**
> "Vì các queries khác nhau có thể trả về cùng một ảnh. Ví dụ query 'biển cấm' và 'prohibitory signs' đều trả về ảnh biển cấm đỗ xe. Em dùng MD5 hash để phát hiện và loại bỏ."

**Q3: "Outliers là gì? Xử lý như thế nào?"**
> "Outliers là ảnh có kích thước bất thường, quá lớn hoặc quá nhỏ. Em dùng IQR method để phát hiện. Em giữ lại để phân tích nhưng sẽ resize về 64x64 khi preprocessing."

**Q4: "Tại sao chia train/val/test?"**
> "Train để huấn luyện model, Val để điều chỉnh hyperparameters, Test để đánh giá cuối cùng. Chia theo tỉ lệ 70/15/15 để đảm bảo đủ dữ liệu cho cả 3 tập."

**Q5: "Dataset này dùng để làm gì?"**
> "Em chuẩn bị dataset này để train model phân loại biển báo giao thông. Sau này có thể phát triển thành app nhận diện biển báo tự động."

**Q6: "Có gặp khó khăn gì không?"**
> "Có ạ. Khó khăn lớn nhất là duplicate nhiều (35%) và scraping chậm (1-2 giờ). Em đã giải quyết bằng MD5 hash và tối ưu số queries."

**Q7: "Sao không dùng dataset có sẵn?"**
> "Theo yêu cầu đề tài, em cần thu thập dữ liệu thô từ nguồn gốc để học kỹ năng data collection thực tế."

**Q8: "Visualization có ý nghĩa gì?"**
> "Visualization giúp em hiểu rõ dataset: phân bố cân bằng không, có outliers không, mối quan hệ giữa các biến. Từ đó quyết định cách preprocessing phù hợp."

---

## PHẦN 7: KẾT LUẬN (2 phút)

**Lời nói:**
> "Tóm lại, em đã hoàn thành pipeline thu thập và xử lý dữ liệu:"
> "- Thu thập: 815 ảnh từ Google Images"
> "- Cleaning: Loại 285 duplicate, còn 530 ảnh sạch"
> "- Visualization: 6 biểu đồ phân tích"
> "- Preprocessing: Resize và chia train/val/test"

> "Dataset này sẵn sàng cho bước tiếp theo là training model phân loại biển báo."

> "Em xin cảm ơn thầy/cô đã lắng nghe!"

---

## 📋 CHECKLIST CUỐI CÙNG

Trước khi demo, kiểm tra:
- [ ] Virtual environment đã activate
- [ ] Tất cả files code chạy được
- [ ] 6 ảnh biểu đồ có trong reports/figures/
- [ ] metadata.csv có 530 dòng
- [ ] data/processed/ có đủ train/val/test
- [ ] Đã đọc kỹ ANSWER.md để trả lời câu hỏi
- [ ] Tự tin, nói rõ ràng, không vội vàng

---

## ⏱️ THỜI GIAN PHÂN BỔ

| Phần | Thời gian | Nội dung |
|------|-----------|----------|
| 1. Giới thiệu | 2 phút | Mục tiêu, phạm vi |
| 2. Thu thập dữ liệu | 5 phút | Giải thích scraping, demo code |
| 3. Data cleaning | 7 phút | Giải thích + demo chạy |
| 4. Visualization | 5 phút | Giải thích 6 biểu đồ |
| 5. Pandas demo | 3 phút | Interactive Python |
| 6. Q&A | 5 phút | Trả lời câu hỏi |
| 7. Kết luận | 2 phút | Tóm tắt |
| **Tổng** | **29 phút** | Dự phòng 1 phút |

---

**CHÚC BẠN DEMO THÀNH CÔNG! 🎉**
