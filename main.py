import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_collection.scraper import TrafficSignScraper
from data_processing.cleaner import DataCleaner
from visualization.visualizer import DataVisualizer


def run_pipeline():
    print("\nTRAFFIC SIGN DATA PIPELINE")
    print("-" * 70)

    print("\n" + "=" * 70)
    print("BAT DAU PIPELINE")
    print("=" * 70)

    print("\nSTEP 1: Web Scraping")
    print("-" * 70)

    raw_dir = Path("data/raw")
    existing_images = list(raw_dir.glob("**/*.jpg")) + list(raw_dir.glob("**/*.png"))

    if len(existing_images) > 0:
        print(f"Da co {len(existing_images)} anh trong data/raw/")
        response = input("Ban co muon scrape them khong? (y/n): ").strip().lower()
        if response == "y":
            TrafficSignScraper()
            print("Bat dau scraping...")
        else:
            print("Bo qua scraping")
    else:
        print("Chua co du lieu, hay chay:")
        print("python src/data_collection/scraper.py")

    print("\nSTEP 1 HOAN TAT")

    print("\nSTEP 2: Data Cleaning + MongoDB")
    print("-" * 70)

    cleaner = DataCleaner()
    cleaner.create_metadata()
    cleaner.add_md5_hash()
    cleaner.add_perceptual_hash()
    cleaner.detect_and_remove_blurry(threshold=100.0)
    cleaner.clean_data()
    cleaner.upload_to_mongodb(drop_existing=True, include_image=True)
    cleaner.resize_and_save(target_size=(224, 224), output_dir="data/processed")

    print("\nSTEP 2 HOAN TAT")


    print("\nSTEP 3: Visualization")
    print("-" * 70)

    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()

    print("\nSTEP 3 HOAN TAT")

    print("\n" + "=" * 70)
    print("PIPELINE HOAN TAT")
    print("=" * 70)


def main():
    try:
        run_pipeline()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
