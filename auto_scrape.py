"""
Script tự động scrape biển báo giao thông
Chạy file này để thu thập dữ liệu tự động
"""

from src.data_collection.selenium_scraper import SeleniumScraper
import time


def main():
    """
    Script tự động scrape từ Google Images
    """
    print("🚀 BẮT ĐẦU THU THẬP DỮ LIỆU TỰ ĐỘNG")
    print("="*70)
    
    # Khởi tạo scraper
    scraper = SeleniumScraper(headless=True)  # headless=True để chạy nền
    
    try:
        scraper.start_driver()
        
        # Danh sách queries để scrape
        queries = [
            # Biển cấm
            ('biển cấm đường Việt Nam', 'prohibitory', 50),
            ('biển cấm rẽ giao thông', 'prohibitory', 30),
            ('biển cấm dừng đỗ', 'prohibitory', 30),
            
            # Biển cảnh báo
            ('biển cảnh báo giao thông Việt Nam', 'warning', 50),
            ('biển báo nguy hiểm đường bộ', 'warning', 30),
            ('biển cảnh báo khúc cua', 'warning', 30),
            
            # Biển hiệu lệnh
            ('biển hiệu lệnh giao thông', 'mandatory', 40),
            ('biển bắt buộc rẽ', 'mandatory', 30),
            
            # Biển chỉ dẫn
            ('biển chỉ dẫn đường bộ', 'informative', 40),
            ('biển chỉ dẫn địa điểm', 'informative', 30),
        ]
        
        total_images = 0
        
        for i, (query, category, max_imgs) in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"[{i}/{len(queries)}] Đang scrape: {query}")
            print(f"Category: {category} | Target: {max_imgs} ảnh")
            print(f"{'='*70}")
            
            count = scraper.scrape_google_images_advanced(query, category, max_imgs)
            total_images += count
            
            print(f"✓ Đã thu thập {count} ảnh")
            
            # Delay giữa các queries để tránh bị block
            if i < len(queries):
                print(f"\n⏳ Đợi 10 giây trước khi scrape tiếp...")
                time.sleep(10)
        
        # Lưu metadata
        scraper.save_metadata()
        
        print("\n" + "="*70)
        print("✅ HOÀN TẤT THU THẬP DỮ LIỆU!")
        print("="*70)
        print(f"📊 Tổng số ảnh đã thu thập: {total_images}")
        print(f"📁 Dữ liệu lưu tại: data/raw/")
        print(f"📋 Metadata: data/raw/selenium_scraping_metadata.json")
        
        print("\n🎯 Bước tiếp theo:")
        print("   1. Kiểm tra chất lượng ảnh đã scrape")
        print("   2. Chạy data cleaning: python src/data_processing/cleaner.py")
        print("   3. Tạo visualizations: python src/visualization/visualizer.py")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        print("\n💡 Kiểm tra:")
        print("   - ChromeDriver đã cài chưa?")
        print("   - Kết nối internet ổn định không?")
        
    finally:
        scraper.close_driver()


if __name__ == '__main__':
    main()
