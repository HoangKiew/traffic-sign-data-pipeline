"""
Main Pipeline Orchestrator
Pipeline don gian: Scraping -> Cleaning -> Visualization
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Config cho modeling
SEED = 42
MODEL_NAME = 'efficientnetb0'  # 'efficientnetb0' hoac 'resnet50'
BASELINE_MODEL_TYPE = 'logreg'  # 'logreg' | 'svm' | 'rf' | 'cnn'
EPOCHS = 10
BATCH_SIZE = 32

from data_collection.scraper import TrafficSignScraper
from data_processing.cleaner import DataCleaner
from visualization.visualizer import DataVisualizer



def run_pipeline():
    """
    Chay pipeline:
    1. Web Scraping
    2. Data Cleaning (+ blur detect, split, preprocess)
    3. Feature Extraction (CNN pretrained)
    4. Train & Evaluate baseline model
    5. Visualization
    """
    print("\nTRAFFIC SIGN DATA PIPELINE")
    print("De tai: Thu thap va Phan tich Bien bao Giao thong")
    print("-" * 70)
    
    print("\n" + "="*70)
    print("BAT DAU PIPELINE")
    print("="*70)
    
    # STEP 1: Web Scraping
    print("\nSTEP 1: Web Scraping (Thu thap du lieu tu trinh duyet)")
    print("-"*70)
    
    scraper = TrafficSignScraper()
    
    # Kiem tra xem da co du lieu chua
    raw_dir = Path('data/raw')
    existing_images = list(raw_dir.glob('**/*.jpg')) + list(raw_dir.glob('**/*.png'))
    
    if len(existing_images) > 0:
        print(f"Da co {len(existing_images)} anh trong data/raw/")
        response = input("Ban co muon scrape them khong? (y/n): ").strip().lower()
        if response != 'y':
            print("Bo qua scraping, su dung du lieu hien co")
        else:
            print("Bat dau scraping...")
            # scraper.scrape_website(url, category)
    else:
        print("Bat dau scraping...")
        print("Luu y: Ban can chay scraper rieng hoac them URLs vao code")
        print("   Vi du: python src/data_collection/scraper.py")
    
    print("\nSTEP 1 HOAN TAT")
    print("   -> data/raw/ (anh goc)")
    
    # STEP 2: Data Cleaning
    print("\nSTEP 2: Data Cleaning (Lam sach du lieu)")
    print("-"*70)
    
    cleaner = DataCleaner()
    cleaner.create_metadata()
    cleaner.add_md5_hash()
    cleaner.add_perceptual_hash()
    cleaner.find_exact_duplicates()
    cleaner.find_similar_images(threshold=5)
    cleaner.analyze_data()            # EDA tong quan
    cleaner.check_missing_values()    # kiem tra missing values
    cleaner.detect_outliers()         # bao cao outliers
    
    # Detect & loai bo anh mo (blur) truoc khi clean
    cleaner.detect_and_remove_blurry(threshold=100.0)
    
    cleaner.clean_data(remove_outliers=False)
    # cleaner.save_metadata()

    # Data Integration -> MongoDB
    print("\nSTEP 2b: Push du lieu len MongoDB")
    cleaner.upload_to_mongodb(drop_existing=True, include_image=True)
    
    # Split + Preprocess (resize) cho training
    print("\nSTEP 2c: Split dataset & Preprocess images (resize)")
    cleaner.split_dataset()
    # Resize ve 224x224 de dung cho EfficientNet/ResNet
    cleaner.resize_and_save(target_size=(224, 224), output_dir='data/processed')
    
    print("\nSTEP 2 HOAN TAT")
    print("   -> Metadata da duoc luu tren MongoDB")
    print("   -> MongoDB: database 'traffic_signs_db', collection 'images'")
    print("   -> Anh da duoc split & resize: data/processed/")
    
    # STEP 3: Feature Extraction
    print("\nSTEP 3: Feature Extraction (EfficientNet/ResNet)")
    print("-"*70)
    
    feature_extractor = FeatureExtractor(
        base_model_name=MODEL_NAME,
        batch_size=BATCH_SIZE,
        seed=SEED,
        processed_dir='data/processed',
        output_dir='data/features'
    )
    feature_extractor.extract_and_save_all()
    
    print("\nSTEP 3 HOAN TAT")
    print(f"   -> Features: data/features/{MODEL_NAME}/features_*.npy")
    
    # STEP 4: Training & Evaluation
    print("\nSTEP 4: Train & Evaluate baseline model")
    print("-"*70)
    
    trainer = BaselineTrainer(
        model_type=BASELINE_MODEL_TYPE,
        base_model_name=MODEL_NAME,
        seed=SEED,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    if BASELINE_MODEL_TYPE == 'cnn':
        trainer.train_eval_cnn()
    else:
        trainer.train_eval_classical()
    
    print("\nSTEP 4 HOAN TAT")
    print("   -> Model va metrics: models/, reports/models/")
    
    # STEP 5: Visualization
    print("\nSTEP 5: Data Visualization (Truc quan hoa bang bieu do)")
    print("-"*70)
    
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()
    
    print("\nSTEP 5 HOAN TAT")
    print("   -> reports/figures/ (4 bieu do)")
    
    # SUMMARY
    print("\n" + "="*70)
    print("PIPELINE HOAN TAT")
    print("="*70)
    
    print("\nKet qua:")
    print("  - Raw data:         data/raw/ (anh goc)")
    print("  - Metadata:         MongoDB (traffic_signs_db.images)")
    print("  - Processed images: data/processed/ (train/val/test, 224x224)")
    print(f"  - Features:         data/features/{MODEL_NAME}/")
    print("  - Models & Metrics: models/, reports/models/")
    print("  - Visualizations:   reports/figures/ (4 bieu do)")
    
    print("\nBuoc tiep theo:")
    print("  1. Xem bieu do: explorer reports\\figures")
    print("  2. Xem metrics model: explorer reports\\models")
    print("  3. Dung model trong models/ de inference / deploy")


def main():
    """Main entry point"""
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\nPipeline bi huy boi nguoi dung")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nLoi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()