"""
Multi-Source Scraper - Scrape từ nhiều nguồn để tránh rate limit
Tự động scrape từ danh sách URLs với delay cao
"""

import time
from interactive_scraper import InteractiveScraper


def main():
    """
    Scrape tự động từ nhiều nguồn
    Tập trung vào Warning và Prohibitory (đang thiếu)
    """
    
    print("🚀 MULTI-SOURCE SCRAPER")
    print("="*70)
    print("Chiến lược: Scrape ít từ nhiều nguồn → Tránh rate limit")
    print("="*70)
    
    scraper = InteractiveScraper()
    
    # Danh sách URLs để scrape (ưu tiên Warning và Prohibitory)
    sources = [
        # WARNING - Cần nhiều nhất!
        ("https://vi.wikipedia.org/wiki/Biển_cảnh_báo", "warning"),
        ("https://commons.wikimedia.org/wiki/Category:Warning_road_signs_in_Vietnam", "warning"),
        ("https://vophutoan.com/bien-bao-canh-bao/", "warning"),
        
        # PROHIBITORY - Cần thêm
        ("https://vi.wikipedia.org/wiki/Biển_cấm", "prohibitory"),
        ("https://commons.wikimedia.org/wiki/Category:Prohibitory_road_signs_in_Vietnam", "prohibitory"),
        ("https://vophutoan.com/bien-bao-cam/", "prohibitory"),
        
        # MANDATORY - Đủ rồi nhưng scrape thêm ít
        ("https://vi.wikipedia.org/wiki/Biển_hiệu_lệnh", "mandatory"),
        
        # INFORMATIVE - Đủ rồi, skip
    ]
    
    total_scraped = 0
    
    for i, (url, category) in enumerate(sources, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(sources)}] Nguồn: {url[:50]}...")
        print(f"Category: {category}")
        print(f"{'='*70}")
        
        try:
            count = scraper.scrape_page(url, category)
            total_scraped += count
            
            # Delay dài giữa các nguồn
            if i < len(sources):
                delay = 30
                print(f"\n⏳ Đợi {delay}s trước khi scrape nguồn tiếp theo...")
                time.sleep(delay)
        
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            print("⏭️  Bỏ qua nguồn này, chuyển sang nguồn tiếp theo...")
            time.sleep(10)
            continue
    
    # Tổng kết
    print("\n" + "="*70)
    print("✅ HOÀN TẤT SCRAPING TỪ NHIỀU NGUỒN!")
    print("="*70)
    print(f"📊 Tổng số ảnh đã scrape: {total_scraped}")
    
    # Show statistics
    scraper.show_stats()
    
    print("\n💡 Bước tiếp theo:")
    print("   1. Kiểm tra chất lượng ảnh: explorer data\\raw")
    print("   2. Chạy data cleaning: python src/data_processing/cleaner.py")
    print("   3. Tạo visualizations: python src/visualization/visualizer.py")


if __name__ == '__main__':
    main()
