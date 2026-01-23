import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import cv2
import numpy as np
import sys
import os
import random
from tqdm import tqdm

# Import kết nối
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import MinIOClient

def get_source_from_name(filename):
    """
    Phân loại nguồn dựa trên tiền tố file
    """
    name = filename.lower()
    
    # 1. Nhóm Search Engine (Do HighVolumeScraper tạo ra)
    if name.startswith("crawl_"): 
        return "Search Engines (Google/Bing)"
        
    # 2. Nhóm Camera hành trình
    if name.startswith("frame_") or "dashcam" in name: 
        return "Camera Hành Trình"
        
    # 3. Nhóm Wikimedia
    if name.startswith("wiki_") or "wikimedia" in name: 
        return "Wikimedia Commons"

    # 4. Các trường hợp cũ (Fallback)
    if "google" in name: return "Google Images"
    if "bing" in name: return "Bing Images"

    return "Khác"

def visualize_separate():
    print("="*60)
    print("TẠO 5 BIỂU ĐỒ (ĐÃ LOẠI BỎ 'DỮ LIỆU MẪU')")
    print("="*60)
    
    minio = MinIOClient()
    all_images = minio.list_images()
    
    if not all_images:
        print("⚠️ Kho ảnh trống!")
        return

    # Lấy mẫu tối đa 2000 ảnh
    SAMPLE_NUM = 4000
    sample_list = random.sample(all_images, min(SAMPLE_NUM, len(all_images)))
    
    print(f"⏳ Đang tải và phân tích {len(sample_list)} ảnh mẫu...")
    
    data = []
    
    # Vòng lặp xử lý
    for img_name in tqdm(sample_list):
        try:
            # --- MỚI: BỎ QUA NẾU LÀ DỮ LIỆU MẪU ---
            if "sample" in img_name.lower():
                continue 
            # --------------------------------------

            source = get_source_from_name(img_name)
            
            # Tải ảnh
            blob = minio.download_image(img_name)
            if not blob: continue
            
            size_kb = len(blob) / 1024
            nparr = np.frombuffer(blob, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                h, w, _ = img.shape
                ratio = w / h
                
                data.append({
                    "source": source,
                    "size_kb": size_kb,
                    "width": w,
                    "height": h,
                    "ratio": ratio
                })
        except Exception:
            continue

    if not data:
        print("❌ Không có dữ liệu hợp lệ (hoặc toàn bộ là sample data).")
        return

    df = pd.DataFrame(data)
    print(f"✅ Đã xử lý xong {len(df)} ảnh sạch. Đang vẽ biểu đồ...")

    # --- BIỂU ĐỒ 1: BOX PLOT ---
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='source', y='size_kb', data=df, palette="Set2")
    plt.title(' So sánh Chất lượng Nguồn (Box Plot)', fontsize=14, weight='bold')
    plt.ylabel('Kích thước file (KB)')
    plt.xlabel('Nguồn dữ liệu')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('1_source_quality_boxplot.png', dpi=150)
    print("   -> Đã lưu: '1_source_quality_boxplot.png'")
    plt.close()

    # --- BIỂU ĐỒ 2: HISTOGRAM (SIZE) ---
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='size_kb', bins=40, kde=True, color='#e74c3c')
    plt.title('Thống kê Kích thước file', fontsize=14, weight='bold')
    plt.xlabel('Kích thước (KB)')
    plt.axvline(10, color='black', linestyle='--', linewidth=2, label='Ngưỡng rác (<10KB)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('2_file_size_dist.png', dpi=150)
    print("   -> Đã lưu: '2_file_size_dist.png'")
    plt.close()

    # --- BIỂU ĐỒ 3: SCATTER PLOT (RES) ---
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='width', y='height', data=df, hue='source', style='source', s=80, alpha=0.7)
    plt.title('Phân bố Độ phân giải (Resolution)', fontsize=14, weight='bold')
    plt.xlabel('Chiều rộng (px)')
    plt.ylabel('Chiều cao (px)')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.axvline(100, color='red', linestyle=':')
    plt.axhline(100, color='red', linestyle=':')
    plt.tight_layout()
    plt.savefig('3_resolution_scatter.png', dpi=150)
    print("   -> Đã lưu: '3_resolution_scatter.png'")
    plt.close()

    # --- BIỂU ĐỒ 4: HISTOGRAM (RATIO) ---
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='ratio', bins=30, color='#8e44ad', kde=True)
    plt.title('Tỷ lệ khung hình (Aspect Ratio)', fontsize=14, weight='bold')
    plt.xlabel('Tỷ lệ (Rộng / Cao)')
    plt.axvline(1.0, color='green', linestyle='--', label='Vuông')
    plt.legend()
    plt.tight_layout()
    plt.savefig('4_aspect_ratio_dist.png', dpi=150)
    print("   -> Đã lưu: '4_aspect_ratio_dist.png'")
    plt.close()

    # --- BIỂU ĐỒ 5: PIE CHART (NGUỒN) - ĐÃ BỎ SAMPLE ---
    plt.figure(figsize=(9, 9))
    source_counts = df['source'].value_counts()
    
    colors = sns.color_palette("pastel")
    wedges, texts, autotexts = plt.pie(
        source_counts, 
        labels=source_counts.index, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=colors,
        explode=[0.05] * len(source_counts),
        shadow=True
    )
    plt.setp(autotexts, size=11, weight="bold")
    plt.title('Cơ cấu Nguồn dữ liệu (Source Distribution)', fontsize=14, weight='bold')
    plt.tight_layout()
    plt.savefig('5_source_distribution_pie.png', dpi=150)
    print("   -> Đã lưu: '5_source_distribution_pie.png'")
    plt.close()

    print("\n HOÀN THÀNH! Đã vẽ xong 5 biểu đồ (Không bao gồm Sample Data).")

if __name__ == "__main__":
    visualize_separate()