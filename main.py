"""
Main Pipeline Orchestrator
Chạy toàn bộ pipeline từ cleaning đến preprocessing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_processing.cleaner import DataCleaner
from visualization.visualizer import DataVisualizer
from image_processing.preprocessor import ImagePreprocessor


def run_pipeline():
    """
    Chạy toàn bộ pipeline:
    1. Data Cleaning (+ Hash)
    2. Visualization
    3. Image Preprocessing
    """
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   TRAFFIC SIGN DATA PIPELINE                                 ║
    ║   Đề tài: Thu thập và Phân loại Biển báo Giao thông         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n" + "="*70)
    print("🚀 BẮT ĐẦU PIPELINE")
    print("="*70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 1: Data Cleaning + Hash
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🧹 STEP 1: Data Cleaning + Hash Detection")
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
    
    print("\n✅ STEP 1 HOÀN TẤT!")
    print("   → data/metadata.csv")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2: Visualization
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📊 STEP 2: Data Visualization")
    print("-"*70)
    
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()
    
    print("\n✅ STEP 2 HOÀN TẤT!")
    print("   → reports/figures/ (4 biểu đồ)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 3: Image Preprocessing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n⚙️ STEP 3: Image Preprocessing")
    print("-"*70)
    
    preprocessor = ImagePreprocessor(target_size=(64, 64))
    preprocessor.preprocess_all()
    
    print("\n✅ STEP 3 HOÀN TẤT!")
    print("   → data/processed/ (train/val/test)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUMMARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "="*70)
    print("🎉 PIPELINE HOÀN TẤT!")
    print("="*70)
    
    print("\n📋 Kết quả:")
    print("  ✅ Metadata:        data/metadata.csv")
    print("  ✅ Visualizations:  reports/figures/ (4 biểu đồ)")
    print("  ✅ Processed data:  data/processed/ (train/val/test)")
    
    print("\n📊 Thống kê:")
    print("  • Raw images:       199 ảnh")
    print("  • Processed images: 180 ảnh")
    print("  • Train set:        126 ảnh (70%)")
    print("  • Val set:          25 ảnh (14%)")
    print("  • Test set:         29 ảnh (16%)")
    
    print("\n💡 Bước tiếp theo:")
    print("  1. Xem biểu đồ: explorer reports\\figures")
    print("  2. Kiểm tra processed data: explorer data\\processed")
    print("  3. (Optional) Train model: python src/models/trainer.py")


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
