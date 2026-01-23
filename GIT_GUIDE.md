# Hướng dẫn đẩy Project lên GitHub

## 📋 CHUẨN BỊ

### 1. Kiểm tra Git đã cài chưa
```powershell
git --version
```

Nếu chưa có, download tại: https://git-scm.com/download/win

### 2. Cấu hình Git (lần đầu)
```powershell
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

---

## 🚀 BƯỚC 1: TẠO REPOSITORY TRÊN GITHUB

1. Truy cập: https://github.com
2. Đăng nhập (hoặc tạo tài khoản mới)
3. Click nút **"New"** (góc trên bên trái)
4. Điền thông tin:
   - **Repository name**: `traffic-sign-data-pipeline`
   - **Description**: `Traffic Sign Detection & Classification Pipeline using YOLO and Computer Vision`
   - **Public** hoặc **Private**: Chọn theo ý bạn
   - ❌ **KHÔNG** tick "Add a README file" (vì đã có sẵn)
   - ❌ **KHÔNG** tick "Add .gitignore"
   - ❌ **KHÔNG** chọn license
5. Click **"Create repository"**

---

## 📦 BƯỚC 2: CHUẨN BỊ PROJECT

### 2.1. Kiểm tra .gitignore
File `.gitignore` đã có sẵn, kiểm tra xem đã đúng chưa:

```powershell
cat .gitignore
```

Nên có các dòng này:
```
# Python
__pycache__/
*.pyc
venv/

# Data (KHÔNG commit data lên Git)
minio_data/
mongo_data/
datasets/
output/
output_dataset/
temp_crawl/
analytics_charts/

# Models
*.pt
yolov8*.pt

# Logs
*.log
logs/
```

### 2.2. Tạo README.md (nếu chưa có)
```powershell
# Kiểm tra
ls README.md

# Nếu chưa có, tạo mới
echo "# Traffic Sign Detection Pipeline" > README.md
```

---

## 🔧 BƯỚC 3: KHỞI TẠO GIT

Mở PowerShell tại thư mục project:

```powershell
cd C:\Study\Nam3_K1\Data_Mining\traffic-sign-data-pipeline
```

### 3.1. Khởi tạo Git repository
```powershell
git init
```

### 3.2. Thêm tất cả files
```powershell
git add .
```

### 3.3. Kiểm tra files sẽ được commit
```powershell
git status
```

**Lưu ý:** Đảm bảo KHÔNG có các thư mục sau:
- ❌ `minio_data/`
- ❌ `mongo_data/`
- ❌ `datasets/` (nếu có nhiều ảnh)
- ❌ `venv/`
- ❌ `*.pt` (model files)

Nếu có, thêm vào `.gitignore` và chạy lại `git add .`

### 3.4. Commit lần đầu
```powershell
git commit -m "Initial commit: Traffic Sign Detection Pipeline"
```

---

## 🌐 BƯỚC 4: KẾT NỐI VỚI GITHUB

### 4.1. Thêm remote repository
```powershell
git remote add origin https://github.com/YOUR_USERNAME/traffic-sign-data-pipeline.git
```

**Thay `YOUR_USERNAME` bằng username GitHub của bạn!**

### 4.2. Kiểm tra remote
```powershell
git remote -v
```

Kết quả mong đợi:
```
origin  https://github.com/YOUR_USERNAME/traffic-sign-data-pipeline.git (fetch)
origin  https://github.com/YOUR_USERNAME/traffic-sign-data-pipeline.git (push)
```

### 4.3. Đổi tên branch thành main (nếu cần)
```powershell
git branch -M main
```

---

## ⬆️ BƯỚC 5: PUSH LÊN GITHUB

### 5.1. Push lần đầu
```powershell
git push -u origin main
```

**Lưu ý:** 
- Sẽ yêu cầu đăng nhập GitHub
- Nếu dùng 2FA, cần tạo **Personal Access Token** (xem phần dưới)

### 5.2. Nhập thông tin đăng nhập
- **Username**: GitHub username của bạn
- **Password**: 
  - ❌ KHÔNG dùng password GitHub
  - ✅ Dùng **Personal Access Token** (PAT)

---

## 🔑 TẠO PERSONAL ACCESS TOKEN (Nếu cần)

### Bước 1: Vào GitHub Settings
1. GitHub → Click avatar (góc phải) → **Settings**
2. Scroll xuống → Click **Developer settings** (cuối cùng bên trái)
3. Click **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token** → **Generate new token (classic)**

### Bước 2: Cấu hình token
- **Note**: `Git Push Token`
- **Expiration**: 90 days (hoặc No expiration)
- **Scopes**: Tick ✅ **repo** (tất cả sub-items)
- Click **Generate token**

### Bước 3: Copy token
- ⚠️ **QUAN TRỌNG**: Copy token ngay (chỉ hiện 1 lần!)
- Lưu vào file text an toàn

### Bước 4: Dùng token khi push
```powershell
git push -u origin main
```
- Username: GitHub username
- Password: **Paste token vừa copy**

---

## ✅ BƯỚC 6: KIỂM TRA

### 6.1. Kiểm tra trên GitHub
1. Vào: `https://github.com/YOUR_USERNAME/traffic-sign-data-pipeline`
2. Xem files đã được upload chưa
3. Kiểm tra README.md hiển thị đúng

### 6.2. Kiểm tra local
```powershell
git log
git status
```

---

## 🔄 CẬP NHẬT SAU NÀY

### Khi có thay đổi mới:

```powershell
# 1. Xem files đã thay đổi
git status

# 2. Thêm files
git add .

# 3. Commit với message mô tả
git commit -m "Add visualization charts and improve detection"

# 4. Push lên GitHub
git push
```

### Commit message tốt:
```
✅ "Add YOLO batch processing for 10x speedup"
✅ "Fix Unicode encoding in logger"
✅ "Update README with installation guide"

❌ "update"
❌ "fix bug"
❌ "changes"
```

---

## 📝 MẸO HAY

### 1. Xem lịch sử commit
```powershell
git log --oneline
```

### 2. Hoàn tác thay đổi chưa commit
```powershell
git checkout -- filename.py
```

### 3. Xóa file khỏi Git (nhưng giữ local)
```powershell
git rm --cached filename
```

### 4. Tạo branch mới
```powershell
git checkout -b feature-new-model
```

### 5. Pull code mới nhất
```powershell
git pull origin main
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### ❌ KHÔNG commit:
- `venv/` - Virtual environment (quá lớn)
- `minio_data/`, `mongo_data/` - Database data
- `datasets/` - Ảnh (quá lớn, dùng Git LFS hoặc link download)
- `*.pt` - Model files (lớn, tải riêng)
- `*.log` - Log files
- `__pycache__/` - Python cache

### ✅ NÊN commit:
- Code Python (`.py`)
- Config files (`.yml`, `.json`)
- Documentation (`.md`)
- Requirements (`requirements.txt`)
- Scripts (`*.sh`, `*.ps1`)

---

## 🆘 XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi 1: "fatal: not a git repository"
```powershell
# Chưa init git
git init
```

### Lỗi 2: "remote origin already exists"
```powershell
# Xóa remote cũ
git remote remove origin

# Thêm lại
git remote add origin https://github.com/YOUR_USERNAME/repo.git
```

### Lỗi 3: "failed to push some refs"
```powershell
# Pull trước khi push
git pull origin main --rebase
git push
```

### Lỗi 4: "Authentication failed"
```powershell
# Dùng Personal Access Token thay vì password
# Hoặc dùng SSH key
```

### Lỗi 5: File quá lớn (> 100MB)
```powershell
# Xóa khỏi Git
git rm --cached large_file.pt

# Thêm vào .gitignore
echo "large_file.pt" >> .gitignore

# Commit
git add .gitignore
git commit -m "Remove large file from Git"
```

---

## 📚 TÀI LIỆU THAM KHẢO

- Git Documentation: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

---

## 🎯 CHECKLIST HOÀN THÀNH

- [ ] Cài đặt Git
- [ ] Cấu hình user.name và user.email
- [ ] Tạo repository trên GitHub
- [ ] Kiểm tra .gitignore
- [ ] `git init`
- [ ] `git add .`
- [ ] `git commit -m "Initial commit"`
- [ ] `git remote add origin ...`
- [ ] `git push -u origin main`
- [ ] Kiểm tra trên GitHub
- [ ] Tạo Personal Access Token (nếu cần)

---

**Chúc bạn thành công! 🎉**
