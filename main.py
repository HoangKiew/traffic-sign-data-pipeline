"""
Main Pipeline Orchestrator
Chạy toàn bộ pipeline từ collection đến visualization
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_collection.dataset_downloader import DatasetDownloader
from data_processing.cleaner import DataCleaner
from visualization.visualizer import DataVisualizer


def run_data_collection_pipeline():
    """
    Pipeline 1: Data Collection & Visualization
    Theo workflow trong slide
    """
    print("\n" + "="*70)
    print("🚀 PIPELINE 1: DATA COLLECTION & VISUALIZATION")
    print("="*70)
    
    # Step 1: Collect Data
    print("\n📥 STEP 1: Data Collection")
    print("-"*70)
    downloader = DatasetDownloader()
    downloader.download_sample_dataset()
    
    # Step 2: Clean Data
    print("\n🧹 STEP 2: Data Cleaning")
    print("-"*70)
    cleaner = DataCleaner()
    cleaner.create_metadata()
    cleaner.analyze_data()
    cleaner.check_missing_values()
    cleaner.detect_outliers()
    cleaner.clean_data(remove_outliers=False)
    cleaner.save_metadata()
    
    # Step 3: Load vào DataFrame (đã làm ở step 2)
    print("\n✓ STEP 3: Loaded vào DataFrame")
    
    # Step 4: Visualization
    print("\n📊 STEP 4: Visualization")
    print("-"*70)
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()
    
    print("\n" + "="*70)
    print("✅ HOÀN TẤT PIPELINE 1!")
    print("="*70)
    print("\n📋 Kết quả:")
    print("  ✓ Metadata: data/metadata.csv")
    print("  ✓ Visualizations: reports/figures/")
    print("\n💡 Tiếp theo:")
    print("  1. Thêm images vào data/raw/[category]/")
    print("  2. Chạy lại pipeline để update")
    print("  3. Chuyển sang Image Processing & Model Training")


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   TRAFFIC SIGN DATA PIPELINE                                 ║
    ║   Đề tài: Thu thập và Phân loại Biển báo Giao thông         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run Pipeline 1
    run_data_collection_pipeline()
    
    print("\n" + "="*70)
    print("🎉 PIPELINE COMPLETED!")
    print("="*70)


if __name__ == '__main__':
    main()
