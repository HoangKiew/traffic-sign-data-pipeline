# 🎯 Interactive Scraper - Hướng dẫn sử dụng

## Cách dùng siêu đơn giản:

### Bước 1: Chạy script
```bash
.\venv\Scripts\Activate.ps1
python interactive_scraper.py
```

### Bước 2: Nhập URL trang web
Ví dụ:
```
🔗 Nhập URL: https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam
```

### Bước 3: Chọn category
```
📂 Chọn category (1-4):
   1. prohibitory  (Biển cấm)
   2. warning      (Biển cảnh báo)
   3. mandatory    (Biển hiệu lệnh)
   4. informative  (Biển chỉ dẫn)
```

### Bước 4: Script tự động cào!
```
✓ image_1.jpg (800x600)
✓ image_2.jpg (1024x768)
✓ image_3.jpg (640x480)
...
✅ Đã cào 25/30 ảnh
```

---

## 💡 Tips:

### Các trang hay để cào:
1. **Wikipedia**
   ```
   https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam
   ```

2. **Wikimedia Commons** (search results)
   ```
   https://commons.wikimedia.org/w/index.php?search=Vietnam+Traffic+Sign&title=Special:MediaSearch&type=image
   ```

3. **Google Images** (cần mở bằng browser trước)
   - Mở Google Images
   - Search "biển cấm đường việt nam"
   - Copy URL
   - Paste vào script

4. **Trang chính phủ**
   ```
   https://vophutoan.com/tai-lieu/tieu-chuan/qcvn-412019-bgtvt-bao-hieu-duong-bo/
   ```

---

## 🚀 Workflow đề xuất:

1. **Mở browser** → Search ảnh biển báo
2. **Copy URL** của trang kết quả
3. **Paste vào script** → Chọn category
4. **Lặp lại** với các trang khác
5. **Gõ 'stats'** để xem đã cào được bao nhiêu
6. **Gõ 'quit'** khi xong

---

## ⌨️ Commands:

- `quit` - Thoát
- `stats` - Xem thống kê
- Nhập URL - Cào trang đó

---

## 📊 Ví dụ session:

```
🔗 Nhập URL: https://vi.wikipedia.org/wiki/Biển_cấm
📂 Chọn category: 1
✅ Đã cào 15 ảnh

🔗 Nhập URL: https://vi.wikipedia.org/wiki/Biển_cảnh_báo
📂 Chọn category: 2
✅ Đã cào 20 ảnh

🔗 Nhập URL: stats
📊 THỐNG KÊ
   prohibitory    :  15 ảnh
   warning        :  20 ảnh
   mandatory      :   0 ảnh
   informative    :   0 ảnh
   TỔNG           :  35 ảnh

🔗 Nhập URL: quit
👋 Tạm biệt!
```

---

**Ưu điểm:**
- ✅ Không bị rate limit (bạn tự control tốc độ)
- ✅ Chọn được category chính xác
- ✅ Thấy ngay kết quả
- ✅ Linh hoạt, cào trang nào cũng được
