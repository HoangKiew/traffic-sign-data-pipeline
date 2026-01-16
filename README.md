# Traffic Sign Data Pipeline - Quick Start Guide

## Muc tieu

Xay dung **Data Pipeline** thu thap va xu ly du lieu hinh anh bien bao giao thong cong khai (4 loai: `prohibitory`, `warning`, `mandatory`, `informative`) **phuc vu bai toan phan loai bien bao** (chuan hoa, luu tru, truc quan hoa, training model).

---

## 1. Setup moi truong

```bash
# Tao venv (Windows)
python -m venv venv
venv\Scripts\activate

# Cai dependencies
pip install -r requirements.txt
```

---

## 2. Thu thap du lieu (Scraping)

```bash
# Chay scraper chinh (Selenium + BeautifulSoup + requests)
python src/data_collection/scraper.py
```

Anh duoc luu vao: `data/raw/`

---

## 3. Chay toan bo Data Pipeline end-to-end

```bash
python main.py
```

Pipeline thuc hien:

1. **Web scraping (neu can)**  
   - Kiem tra `data/raw/` da co anh hay chua.  
   - Neu chua co, huong dan chay scraper.  
   - Neu da co, hoi co muon scrape them khong.

2. **Data Cleaning & Preprocessing**
   - Tao metadata (width, height, size, format, category, duong dan anh).
   - Tinh **MD5 hash** va **perceptual hash** de phat hien anh trung lap / gan giong.
   - Phan tich thong ke co ban (EDA), kiem tra missing, outlier.
   - **Detect va loai bo anh mo** bang Laplacian variance.
   - Xoa anh trung lap, anh qua nho, outlier (neu chon).

3. **Data Integration -> MongoDB**
   - Day metadata (va tuy chon ca bytes anh) len MongoDB Atlas:  
     - Database: `traffic_signs_db`  
     - Collection: `images`

4. **Split + Resize dataset**
   - Chia thanh **train / val / test** theo tung category (khoang 70/15/15, co xu ly truong hop it anh).
   - Resize anh ve **224x224** va luu vao: `data/processed/train|val|test/<category>/*.png`

5. **Feature Extraction (CNN pretrained)**
   - Dung **EfficientNetB0** hoac **ResNet50** (`include_top=False`, `pooling='avg'`) lam feature extractor.
   - Extract vector dac trung cho **train/val/test** va luu:
     - `data/features/<model_name>/features_train.npy`
     - `data/features/<model_name>/features_val.npy`
     - `data/features/<model_name>/features_test.npy`
     - `data/features/<model_name>/labels_*.npy`
     - `data/features/<model_name>/class_indices.json`

6. **Training & Evaluation baseline model**
   - Train **classifier truyen thong** tren features:
     - `logreg` (Logistic Regression) / `svm` / `rf` (Random Forest).  
   - Hoac **CNN end-to-end** (`BASELINE_MODEL_TYPE = 'cnn'`):
     - Dung pretrained EfficientNet/ResNet lam backbone.
     - **Data augmentation** on-the-fly: flip, rotate, shift, zoom, shear, brightness, noise.
     - Co tuy chon **fine-tune** (unfreeze base model, LR nho hon).
   - Luu:
     - Model: `models/*.joblib` hoac `models/*.h5`
     - Metrics (classification report + accuracy): `models/*_metrics.json`
     - Confusion matrix heatmap + per-class accuracy: `reports/models/*.png`
     - Neu train CNN: accuracy/loss curves: `reports/models/cnn_*_accuracy.png`, `cnn_*_loss.png`

7. **Visualization (EDA)**
   - Doc metadata tu CSV (neu co) hoac tu MongoDB.
   - Ve 4 bieu do chinh:
     - Bar chart phan bo so anh theo category.
     - Histogram width/height.
     - Scatter plot width vs height.
     - Bieu do thong ke width/height/size.  
   - Luu tai: `reports/figures/`

---

## 4. Chay tung buoc rieng le (tuy chon)

### 4.1 Clean + Split + Resize doc lap

```bash
python src/data_processing/cleaner.py
```

Script nay:

- Thuc hien cleaning (giong main pipeline, bao gom blur detect).  
- Chia train/val/test theo category.  
- Resize anh (mặc dinh 64x64 trong script, co the doi tham so) va luu vao `data/processed/`.

### 4.2 Feature Extraction doc lap

```bash
python src/feature_extraction/extract_features.py
```

Mac dinh dung `EfficientNetB0`:

- Doc anh tu `data/processed/train|val|test`.
- Luu features va labels vao `data/features/efficientnetb0/`.

### 4.3 Train baseline model doc lap

```bash
# Train Logistic Regression tren features EfficientNetB0
python src/modeling/train_baseline.py
```

Trong code co the doi:

- `model_type`: `logreg`, `svm`, `rf`, hoac `cnn`.  
- `base_model_name`: `efficientnetb0` hoac `resnet50`.  
- `epochs`, `batch_size`, `fine_tune` (neu dung `cnn`).

---

## 5. Truc quan hoa doc lap

```bash
python src/visualization/visualizer.py
```

Visualizer se:

- Uu tien doc `data/metadata.csv` neu ban export CSV (`save_metadata()` trong cleaner).  
- Neu khong co CSV, se doc metadata tu MongoDB (`traffic_signs_db.images`).  

Bieu do luu tai: `reports/figures/`

---

## 6. Ket qua mong doi

- Anh da lam sach: `data/raw/` va `data/processed/`.
- Train/Val/Test: chia gan ti le 70/15/15 theo tung category.
- Features vector cho moi anh (EfficientNet/ResNet) trong `data/features/<model_name>/`.
- Model va metrics luu trong `models/` va `reports/models/`.
- Bieu do EDA: `reports/figures/`.

---

## 7. Tech Stack

- Data: `pandas`, `numpy`
- Image: `Pillow`, `opencv-python`, `tqdm`
- Storage: MongoDB Atlas (`pymongo`, BSON `Binary` cho anh)
- Feature extraction / Deep learning: `tensorflow` / `tf.keras` (EfficientNetB0, ResNet50)
- Classical ML: `scikit-learn` (LogisticRegression, SVM, RandomForest)
- Visualization: `matplotlib`, `seaborn`
- Web scraping: `Selenium`, `BeautifulSoup`, `requests`

---

## 8. Cau truc thu muc chinh

```text
traffic-sign-data-pipeline/
├── data/
│   ├── raw/                 # Anh goc tu scraper
│   ├── processed/           # Anh resize (train/val/test) - phuc vu training
├── src/
│   ├── data_collection/     # scraper.py  (thu thap anh cong khai)
│   ├── data_processing/     # cleaner.py  (clean + blur detect + split + resize + upload MongoDB)
│   ├── feature_extraction/  # extract_features.py (CNN pretrained -> features .npy)
│   ├── modeling/            # train_baseline.py (train + evaluate models)
│   └── visualization/       # visualizer.py (EDA & bieu do tu MongoDB)
├── reports/
│   ├── figures/             # Bieu do EDA
│   └── models/              # Confusion matrix, per-class acc, learning curves
├── models/                  # Model artifacts (.joblib, .h5, history JSON)
├── cleanup_results.py       # Script don ket qua (xoa processed/features/reports/models + MongoDB)
├── main.py                  # Orchestrator: Scraping -> Cleaning -> MongoDB -> Features -> Train -> Viz
└── requirements.txt
```

---

## 9. Cleanup ket qua

Neu muon don sach cac ket qua da sinh ra (anh da resize, features, reports, models, du lieu MongoDB):

```bash
python cleanup_results.py
```

Script se hoi lai truoc khi:

- Xoa `data/processed/`
- Xoa `data/features/`
- Xoa cac thu muc con trong `reports/` (figures, models)
- Xoa `models/`
- Tuy chon xoa toan bo documents trong MongoDB `traffic_signs_db.images`.

