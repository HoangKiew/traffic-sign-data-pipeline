"""
Improved Analytics Visualization - Individual Charts
Mỗi biểu đồ được lưu riêng biệt để dễ xem và sử dụng
"""
import os
import glob
import matplotlib
matplotlib.use('Agg')  # Thêm dòng này ngay sau import matplotlib để dùng non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from tqdm import tqdm

# --- CONFIG ---
LABEL_DIR = "datasets/labels"
OUTPUT_DIR = "analytics_charts"

# Class names
CLASS_NAMES = {
    0: "Cấm",
    1: "Nguy hiểm", 
    2: "Hiệu lệnh",
    3: "Chỉ dẫn",
    4: "Khác"
}

CLASS_COLORS = {
    0: '#e74c3c',  # Red
    1: '#f39c12',  # Orange
    2: '#3498db',  # Blue
    3: '#2ecc71',  # Green
    4: '#95a5a6'   # Gray
}

def get_size_category(area):
    """Phân loại kích thước"""
    if area < 0.01: return "Rất nhỏ"
    if area < 0.05: return "Nhỏ"
    if area < 0.15: return "Trung bình"
    return "Lớn"

def load_data():
    """Load dữ liệu từ YOLO labels"""
    print(" Đang tải dữ liệu từ labels...")
    txt_files = glob.glob(os.path.join(LABEL_DIR, "*.txt"))
    
    if not txt_files:
        print(f" Không tìm thấy file labels trong {LABEL_DIR}")
        return None, 0
    
    data = []
    for txt in tqdm(txt_files, desc="Đọc labels"):
        with open(txt, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                    
                    data.append({
                        "Class": CLASS_NAMES.get(cls, f"Class {cls}"),
                        "Class_ID": cls,
                        "Center_X": x,
                        "Center_Y": y,
                        "Width": w,
                        "Height": h,
                        "Area": w * h,
                        "Aspect_Ratio": w / h if h > 0 else 1.0,
                        "Size_Category": get_size_category(w * h)
                    })
    
    df = pd.DataFrame(data)
    print(f" Đã tải {len(df)} objects từ {len(txt_files)} files")
    return df, len(txt_files)

def create_visualizations(df, num_files):
    """Tạo các biểu đồ riêng biệt"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
    
    print("\n Đang tạo biểu đồ...")
    
    # Get class counts and colors
    class_counts = df['Class'].value_counts()
    colors = []
    for class_name in class_counts.index:
        for cls_id, name in CLASS_NAMES.items():
            if name == class_name:
                colors.append(CLASS_COLORS[cls_id])
                break
    
    # === CHART 1: Class Distribution (Bar) ===
    print("  → Chart 1: Phân bố số lượng theo loại")
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(class_counts)), class_counts.values, color=colors, 
                   edgecolor='black', linewidth=1.5)
    plt.xticks(range(len(class_counts)), class_counts.index, rotation=0)
    plt.ylabel('Số lượng', fontsize=12, fontweight='bold')
    plt.title('Phân bố số lượng biển báo theo loại', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/class_count.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 2: Class Distribution (Pie) ===
    print("  → Chart 2: Tỷ lệ phần trăm theo loại")
    plt.figure(figsize=(8, 8))
    explode = [0.05 if i == class_counts.values.argmax() else 0 for i in range(len(class_counts))]
    plt.pie(class_counts.values, labels=class_counts.index, autopct='%1.1f%%',
            colors=colors, explode=explode, startangle=90,
            textprops={'fontsize': 12, 'fontweight': 'bold'})
    plt.title('Tỷ lệ phần trăm theo loại biển báo', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/class_percentage.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 3: Size Category Distribution ===
    print("  → Chart 3: Phân bố theo kích thước")
    plt.figure(figsize=(10, 6))
    size_counts = df['Size_Category'].value_counts()
    size_order = ["Rất nhỏ", "Nhỏ", "Trung bình", "Lớn"]
    size_counts = size_counts.reindex([s for s in size_order if s in size_counts.index])
    
    plt.bar(range(len(size_counts)), size_counts.values, 
            color=sns.color_palette("YlOrRd", len(size_counts)), edgecolor='black')
    plt.xticks(range(len(size_counts)), size_counts.index)
    plt.ylabel('Số lượng', fontsize=12, fontweight='bold')
    plt.title('Phân bố theo kích thước biển báo', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/size_distribution.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 4: Area Distribution by Class ===
    print("  → Chart 4: Phân bố diện tích theo loại")
    plt.figure(figsize=(12, 6))
    for cls_id, cls_name in CLASS_NAMES.items():
        if cls_name in df['Class'].values:
            data_cls = df[df['Class'] == cls_name]['Area']
            plt.hist(data_cls, bins=30, alpha=0.5, label=cls_name, color=CLASS_COLORS[cls_id])
    plt.xlabel('Diện tích (normalized)', fontsize=12)
    plt.ylabel('Tần suất', fontsize=12)
    plt.title('Phân bố diện tích theo loại biển báo', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/area_by_class.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 5: Width vs Height Scatter ===
    print("  → Chart 5: Chiều rộng vs Chiều cao")
    plt.figure(figsize=(10, 10))
    for cls_id, cls_name in CLASS_NAMES.items():
        if cls_name in df['Class'].values:
            data_cls = df[df['Class'] == cls_name]
            plt.scatter(data_cls['Width'], data_cls['Height'], 
                       alpha=0.5, s=30, label=cls_name, color=CLASS_COLORS[cls_id])
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.3, linewidth=2, label='Vuông (1:1)')
    plt.xlabel('Chiều rộng', fontsize=12)
    plt.ylabel('Chiều cao', fontsize=12)
    plt.title('Chiều rộng vs Chiều cao', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/width_vs_height.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 6: Phân bố màu sắc biển báo theo loại (Color Distribution) ===
    print("  → Chart 6: Phân bố màu sắc biển báo theo loại")
    plt.figure(figsize=(10, 6))
    if "Class_ID" not in df.columns:
        class_id_map = {v: k for k, v in CLASS_NAMES.items()}
        df["Class_ID"] = df["Class"].map(class_id_map)
    color_counts = df["Class_ID"].value_counts().sort_index()
    color_labels = [CLASS_NAMES.get(i, str(i)) for i in color_counts.index]
    color_palette = [CLASS_COLORS.get(i, "#cccccc") for i in color_counts.index]
    plt.bar(color_labels, color_counts.values, color=color_palette, edgecolor='black')
    plt.ylabel('Số lượng', fontsize=12, fontweight='bold')
    plt.xlabel('Loại màu sắc biển báo', fontsize=12, fontweight='bold')
    plt.title('Phân bố màu sắc biển báo theo loại', fontsize=14, fontweight='bold')
    for i, v in enumerate(color_counts.values):
        plt.text(i, v, str(v), ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/color_distribution.png', dpi=200, bbox_inches='tight')
    plt.close()

    # === CHART 7: Tỷ lệ diện tích biển báo trên ảnh gốc (Relative Area) ===
    print("  → Chart 7: Tỷ lệ diện tích biển báo trên ảnh gốc (Relative Area)")
    plt.figure(figsize=(12, 6))
    if "Width_Img" in df.columns and "Height_Img" in df.columns:
        df["Relative_Area"] = (df["Width"] * df["Height"]) / (df["Width_Img"] * df["Height_Img"])
    else:
        df["Relative_Area"] = df["Area"]  # YOLO labels đã chuẩn hóa
    df_sorted = df.sort_values('Class_ID')
    sns.boxplot(data=df_sorted, x='Class', y='Relative_Area', hue='Class', legend=False,
                palette=[CLASS_COLORS[i] for i in sorted(df['Class_ID'].unique())])
    plt.ylabel('Tỷ lệ diện tích (biển báo/ảnh)', fontsize=12)
    plt.title('Tỷ lệ diện tích biển báo trên ảnh gốc theo loại', fontsize=14, fontweight='bold')
    plt.legend()
    plt.xticks(rotation=15)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/relative_area.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 8: Location Heatmap ===
    print("  → Chart 8: Bản đồ nhiệt vị trí")
    plt.figure(figsize=(10, 10))
    sns.kdeplot(data=df, x='Center_X', y='Center_Y', fill=True, 
                cmap="YlOrRd", thresh=0.05, levels=20)
    plt.gca().invert_yaxis()
    plt.xlim(0, 1)
    plt.ylim(1, 0)
    plt.xlabel('Vị trí ngang (0=Trái, 1=Phải)', fontsize=12)
    plt.ylabel('Vị trí dọc (0=Trên, 1=Dưới)', fontsize=12)
    plt.title('Bản đồ nhiệt vị trí biển báo', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/location_heatmap.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 9: Area Histogram ===
    print("  → Chart 9: Phân bố diện tích")
    plt.figure(figsize=(12, 6))
    area = df['Area']
    plt.hist(area, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    plt.axvline(area.mean(), color='red', linestyle='--', linewidth=2, label=f'Trung bình: {area.mean():.3f}')
    plt.axvline(area.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {area.median():.3f}')
    plt.xlabel('Diện tích (normalized)', fontsize=12)
    plt.ylabel('Tần suất', fontsize=12)
    plt.title('Phân bố diện tích biển báo', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/area_histogram.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # === CHART 10: Summary Statistics ===
    print("  → Chart 10: Bảng thống kê tổng quan")
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Add title at the very top
    fig.suptitle('Thống kê tổng quan Dataset Biển Báo Giao Thông', 
                fontsize=18, fontweight='bold', y=0.98)
    
    ax.axis('tight')
    ax.axis('off')
    
    # Create comprehensive summary table
    summary_data = []
    
    # Header
    summary_data.append(['CHỈ TIÊU', 'GIÁ TRỊ'])
    summary_data.append(['', ''])
    
    # Section 1: General Info
    summary_data.append(['TỔNG QUAN', ''])
    summary_data.append(['Tổng số biển báo', f'{len(df):,}'])
    summary_data.append(['Số file labels', f'{num_files:,}'])
    summary_data.append(['Trung bình/file', f'{len(df)/num_files:.1f}'])
    summary_data.append(['', ''])
    
    # Section 2: Area Statistics
    summary_data.append([' DIỆN TÍCH ', ''])
    summary_data.append(['Trung bình', f'{df["Area"].mean():.4f}'])
    summary_data.append(['Median', f'{df["Area"].median():.4f}'])
    summary_data.append(['Nhỏ nhất', f'{df["Area"].min():.4f}'])
    summary_data.append(['Lớn nhất', f'{df["Area"].max():.4f}'])
    summary_data.append(['Độ lệch chuẩn', f'{df["Area"].std():.4f}'])
    summary_data.append(['', ''])
    
    # Section 3: Aspect Ratio
    summary_data.append(['TỶ LỆ KHUNG HÌNH ', ''])
    summary_data.append(['Trung bình', f'{df["Aspect_Ratio"].mean():.2f}'])
    summary_data.append(['Median', f'{df["Aspect_Ratio"].median():.2f}'])
    summary_data.append(['Nhỏ nhất', f'{df["Aspect_Ratio"].min():.2f}'])
    summary_data.append(['Lớn nhất', f'{df["Aspect_Ratio"].max():.2f}'])
    summary_data.append(['', ''])
    
    # Section 4: Class Distribution
    summary_data.append([' PHÂN BỐ THEO LOẠI ', ''])
    for cls_name in class_counts.index:
        percentage = (class_counts[cls_name] / len(df)) * 100
        summary_data.append([cls_name, f'{class_counts[cls_name]:,} ({percentage:.1f}%)'])
    
    # Create table
    table = ax.table(cellText=summary_data, cellLoc='left', loc='center',
                    colWidths=[0.55, 0.45])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.2)
    
    # Style the table
    # Header row
    table[(0, 0)].set_facecolor('#2c3e50')
    table[(0, 0)].set_text_props(weight='bold', color='white', fontsize=13)
    table[(0, 1)].set_facecolor('#2c3e50')
    table[(0, 1)].set_text_props(weight='bold', color='white', fontsize=13)
    
    # Section headers
    section_rows = [2, 8, 15, 21]  # Rows with section headers
    for row in section_rows:
        if row < len(summary_data):
            table[(row, 0)].set_facecolor('#3498db')
            table[(row, 0)].set_text_props(weight='bold', color='white', fontsize=12)
            table[(row, 1)].set_facecolor('#3498db')
            table[(row, 1)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors for better readability
    for i in range(len(summary_data)):
        if i not in [0] + section_rows and i not in [1, 7, 14, 20]:  # Skip header and empty rows
            if i % 2 == 0:
                table[(i, 0)].set_facecolor('#ecf0f1')
                table[(i, 1)].set_facecolor('#ecf0f1')
    
    # Add borders
    for key, cell in table.get_celld().items():
        cell.set_linewidth(1.5)
        cell.set_edgecolor('#bdc3c7')
    
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle at top
    plt.savefig(f'{OUTPUT_DIR}/summary_statistics.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Đã lưu tất cả biểu đồ vào thư mục '{OUTPUT_DIR}/'")

def main():
    df, num_files = load_data()
    if df is None or df.empty:
        print(" Không có dữ liệu để visualize!")
        return
    
    create_visualizations(df, num_files)
    
    print("\n" + "="*60)
    print("📊 HOÀN THÀNH TẠO BIỂU ĐỒ")
    print("="*60)
    print(f"Thư mục output: {OUTPUT_DIR}/")
    print("\nCác file đã tạo:")
    print("  01. 01_class_count.png - Số lượng theo loại (Bar)")
    print("  02. 02_class_percentage.png - Tỷ lệ % theo loại (Pie)")
    print("  03. 03_size_distribution.png - Phân bố kích thước")
    print("  04. 04_area_by_class.png - Diện tích theo loại")
    print("  05. 05_width_vs_height.png - Chiều rộng vs cao")
    print("  06. 06_aspect_ratio.png - Tỷ lệ khung hình")
    print("  07. 07_location_heatmap.png - Bản đồ nhiệt vị trí")
    print("  08. 08_location_by_class.png - Vị trí theo loại")
    print("  09. 09_area_histogram.png - Histogram diện tích")
    print("  10. 10_summary_statistics.png - Bảng thống kê")
    print("="*60)

if __name__ == "__main__":
    main()