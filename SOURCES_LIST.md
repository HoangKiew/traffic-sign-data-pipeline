# 🌐 DANH SÁCH NGUỒN ĐỂ SCRAPE BIỂN BÁO GIAO THÔNG

## Chiến lược: Scrape ít từ nhiều nguồn → Tránh rate limit

---

## 📋 Danh sách URLs theo category

### 1. PROHIBITORY (Biển cấm) - Cần ~50 ảnh

#### Wikipedia & Wikimedia
- https://vi.wikipedia.org/wiki/Bi%E1%BB%83n_c%E1%BA%A5m
- https://commons.wikimedia.org/wiki/Category:Prohibitory_road_signs_in_Vietnam
- https://commons.wikimedia.org/wiki/Category:Regulatory_road_signs_in_Vietnam

#### Trang chính phủ VN
- https://vophutoan.com/bien-bao-cam/
- https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Quyet-dinh-4915-QD-BGTVT-2015-ky-hieu-bien-bao-duong-bo-289651.aspx

#### Google Images (dùng Selenium)
- Search: "biển cấm đường việt nam"
- Search: "biển cấm rẽ"
- Search: "biển cấm dừng đỗ"

---

### 2. WARNING (Biển cảnh báo) - Cần ~50 ảnh

#### Wikipedia & Wikimedia
- https://vi.wikipedia.org/wiki/Bi%E1%BB%83n_c%E1%BA%A3nh_b%C3%A1o
- https://commons.wikimedia.org/wiki/Category:Warning_road_signs_in_Vietnam
- https://commons.wikimedia.org/wiki/Category:Danger_warning_signs

#### Trang VN
- https://vophutoan.com/bien-bao-canh-bao/
- https://csgt.vn/bien-bao-canh-bao-giao-thong

#### Google Images
- Search: "biển cảnh báo giao thông việt nam"
- Search: "biển báo nguy hiểm đường bộ"
- Search: "biển cảnh báo khúc cua"

---

### 3. MANDATORY (Biển hiệu lệnh) - Cần ~50 ảnh

#### Wikipedia & Wikimedia
- https://vi.wikipedia.org/wiki/Bi%E1%BB%83n_hi%E1%BB%87u_l%E1%BB%87nh
- https://commons.wikimedia.org/wiki/Category:Mandatory_road_signs_in_Vietnam

#### Trang VN
- https://vophutoan.com/bien-bao-hieu-lenh/
- https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/tu-van-phap-luat/43161/tong-hop-cac-loai-bien-bao-hieu-lenh-va-y-nghia-cua-tung-bien-bao

#### Google Images
- Search: "biển hiệu lệnh giao thông"
- Search: "biển bắt buộc rẽ"

---

### 4. INFORMATIVE (Biển chỉ dẫn) - Cần ~50 ảnh

#### Wikipedia & Wikimedia
- https://vi.wikipedia.org/wiki/Bi%E1%BB%83n_ch%E1%BB%89_d%E1%BA%ABn
- https://commons.wikimedia.org/wiki/Category:Information_road_signs_in_Vietnam

#### Trang VN
- https://vophutoan.com/bien-bao-chi-dan/
- https://csgt.vn/bien-bao-chi-dan

#### Google Images
- Search: "biển chỉ dẫn đường bộ việt nam"
- Search: "biển chỉ dẫn địa điểm"

---

## 🎯 Chiến lược Scraping

### Mục tiêu: 200-300 ảnh mới (tổng ~400-500 ảnh)

**Phân bổ:**
- Prohibitory: +40 ảnh (13 → 53)
- Warning: +50 ảnh (1 → 51)
- Mandatory: +0 ảnh (51 → 51) ✅ Đủ rồi
- Informative: +0 ảnh (113 → 113) ✅ Đủ rồi

**→ Tổng cần scrape thêm: ~90 ảnh**

---

## ⚙️ Cấu hình Scraper

### Delay settings:
```python
DELAY_BETWEEN_IMAGES = 2.0  # 2 giây giữa mỗi ảnh
DELAY_BETWEEN_PAGES = 10.0  # 10 giây giữa mỗi trang
DELAY_BETWEEN_SOURCES = 30.0  # 30 giây giữa mỗi nguồn
```

### Limits:
```python
MAX_IMAGES_PER_SOURCE = 15  # Tối đa 15 ảnh/nguồn
MAX_RETRIES = 3
TIMEOUT = 15
```

---

## 📝 Workflow

1. **Scrape từ nguồn 1** (15 ảnh) → Đợi 30s
2. **Scrape từ nguồn 2** (15 ảnh) → Đợi 30s
3. **Scrape từ nguồn 3** (15 ảnh) → Đợi 30s
4. ...
5. **Lặp lại** cho đến khi đủ

**Ưu điểm:**
- ✅ Không bị rate limit (mỗi nguồn chỉ 15 ảnh)
- ✅ Dữ liệu đa dạng (nhiều nguồn khác nhau)
- ✅ Có thể dừng/tiếp tục bất cứ lúc nào

---

## 🚀 Cách sử dụng

### Option 1: Chạy script tự động
```bash
python scrape_multiple_sources.py
```

### Option 2: Chạy interactive (khuyên dùng)
```bash
python interactive_scraper.py
```
Nhập từng URL, chọn category, script tự động delay

---

## ⏱️ Ước tính thời gian

- **90 ảnh** × 2s delay = 180s = **3 phút** (chỉ download)
- **6 nguồn** × 30s delay = 180s = **3 phút** (delay giữa nguồn)
- **Tổng: ~6-10 phút** (bao gồm xử lý)

---

## 💡 Tips

1. **Ưu tiên scrape Warning và Prohibitory** (đang thiếu nhất)
2. **Dùng interactive scraper** để control tốt hơn
3. **Check kết quả sau mỗi 20-30 ảnh**
4. **Nếu bị rate limit** → Tăng delay lên 3-5s

---

**Cập nhật:** 2026-01-01
