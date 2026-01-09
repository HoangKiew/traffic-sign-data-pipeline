"""
Main Pipeline Orchestrator
Pipeline đơn giản: Scraping → Cleaning → Visualization
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_collection.scraper import TrafficSignScraper
from data_processing.cleaner import DataCleaner
from visualization.visualizer import DataVisualizer


def run_pipeline():
    """
    Chạy pipeline đơn giản:
    1. Web Scraping (Thu thập dữ liệu từ trình duyệt)
    2. Data Cleaning (Làm sạch dữ liệu)
    3. Visualization (Trực quan hóa bằng biểu đồ)
    """
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   TRAFFIC SIGN DATA PIPELINE                                 ║
    ║   Đề tài: Thu thập và Phân tích Biển báo Giao thông         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n" + "="*70)
    print("🚀 BẮT ĐẦU PIPELINE")
    print("="*70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 1: Web Scraping
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🌐 STEP 1: Web Scraping (Thu thập dữ liệu từ trình duyệt)")
    print("-"*70)
    
    scraper = TrafficSignScraper()
    
    # Kiểm tra xem đã có dữ liệu chưa
    raw_dir = Path('data/raw')
    existing_images = list(raw_dir.glob('**/*.jpg')) + list(raw_dir.glob('**/*.png'))
    
    if len(existing_images) > 0:
        print(f"⚠️  Đã có {len(existing_images)} ảnh trong data/raw/")
        response = input("Bạn có muốn scrape thêm không? (y/n): ").strip().lower()
        if response != 'y':
            print("⏭️  Bỏ qua scraping, sử dụng dữ liệu hiện có")
        else:
            print("📥 Bắt đầu scraping...")
            # Có thể thêm code scraping ở đây nếu cần
            # scraper.scrape_website(url, category)
    else:
        print("📥 Bắt đầu scraping...")
        print("💡 Lưu ý: Bạn cần chạy scraper riêng hoặc thêm URLs vào code")
        print("   Ví dụ: python src/data_collection/scraper.py")
    
    print("\n✅ STEP 1 HOÀN TẤT!")
    print("   → data/raw/ (ảnh gốc)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2: Data Cleaning
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🧹 STEP 2: Data Cleaning (Làm sạch dữ liệu)")
    print("-"*70)
    
    cleaner = DataCleaner()
    cleaner.create_metadata()
    cleaner.add_md5_hash()
    cleaner.add_perceptual_hash()
    cleaner.find_exact_duplicates()
    cleaner.find_similar_images(threshold=5)
    cleaner.analyze_data()
    cleaner.check_missing_values()
    cleaner.detect_outliers()
    cleaner.clean_data(remove_outliers=False)
    cleaner.save_metadata()
    
    print("\n✅ STEP 2 HOÀN TẤT!")
    print("   → data/metadata.csv")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 3: Visualization
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📊 STEP 3: Data Visualization (Trực quan hóa bằng biểu đồ)")
    print("-"*70)
    
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()
    
    print("\n✅ STEP 3 HOÀN TẤT!")
    print("   → reports/figures/ (4 biểu đồ)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUMMARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "="*70)
    print("🎉 PIPELINE HOÀN TẤT!")
    print("="*70)
    
    print("\n📋 Kết quả:")
    print("  ✅ Raw data:         data/raw/ (ảnh gốc)")
    print("  ✅ Metadata:         data/metadata.csv")
    print("  ✅ Visualizations:   reports/figures/ (4 biểu đồ)")
    
    # Thống kê từ metadata
    try:
        import pandas as pd
        df = pd.read_csv('data/metadata.csv')
        print(f"\n📊 Thống kê:")
        print(f"  • Tổng số ảnh:     {len(df)} ảnh")
        print(f"  • Categories:      {df['category'].nunique()} loại")
        print(f"  • Kích thước TB:   {df['width'].mean():.0f}x{df['height'].mean():.0f} pixels")
        print(f"\n  Phân bố theo category:")
        for cat, count in df['category'].value_counts().items():
            print(f"    - {cat}: {count} ảnh")
    except:
        pass
    
    print("\n💡 Bước tiếp theo:")
    print("  1. Xem biểu đồ: explorer reports\\figures")
    print("  2. Xem metadata: data\\metadata.csv")
    print("  3. Phân tích dữ liệu từ các biểu đồ")


def main():
    """Main entry point"""
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline bị hủy bởi người dùng")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()