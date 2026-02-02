import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_collection.web_scraper import HighVolumeScraper

# DANH SÁCH TỪ KHÓA TỐI ƯU (Bao gồm cả ngữ cảnh đường phố)
KEYWORDS = [
    # --- Nhóm 1: Biển báo cụ thể (Specific) ---
    "No U-turn sign", "Stop sign","No left turn sign", "No right turn sign",
    "50 km/h speed limit sign", "60 km/h speed limit sign",
    "Construction site sign", "Danger sign",
    "Vietnam traffic signs street", "One-way street sign",
    "Pedestrian crossing sign", "Intersection with priority road sign",
    
    # --- Nhóm 2: Từ khóa Tiếng Anh (Mở rộng nguồn) ---
    "Vietnam traffic signs", "Traffic signs Hanoi", "Traffic signs Saigon",
    "Vietnamese road signs", "Vietnam highway signs", "Street signs Vietnam",
    
    # --- Nhóm 3: NGỮ CẢNH ĐƯỜNG PHỐ (QUAN TRỌNG ĐỂ TĂNG SỐ LƯỢNG) ---
    # Những từ khóa này sẽ ra ảnh đường phố chứa nhiều biển báo nhỏ
    "Giao thông Việt Nam", "Đường phố Hà Nội", "Đường phố Sài Gòn",
    "Ngã tư đường phố Việt Nam", "Vietnam street view", "Driving in Vietnam",
    "Vietnam road trip", "Vietnam traffic jam", "Quốc lộ 1A Việt Nam",
    "Đường cao tốc Việt Nam", "Xe cộ Việt Nam", "Cảnh sát giao thông Việt Nam"
]

if __name__ == "__main__":
    print(f"=== CHIẾN DỊCH TẢI ẢNH QUY MÔ LỚN ({len(KEYWORDS)} từ khóa) ===")
    
    scraper = HighVolumeScraper(save_to_minio=True)
    
    # Đổi max_num hoặc thêm các tham số khác nếu muốn
    # Đổi đường dẫn lưu ảnh nếu cần (ví dụ: lưu vào bucket khác)
    # Ví dụ: lưu vào bucket 'my-traffic-signs'
    # scraper.crawl(KEYWORDS, max_num=300, bucket="my-traffic-signs")

    # Nếu chỉ muốn đổi số lượng ảnh/từ khóa:
    scraper.crawl(KEYWORDS, max_num=150)