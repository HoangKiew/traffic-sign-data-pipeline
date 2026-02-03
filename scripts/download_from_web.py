import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_collection.web_scraper import HighVolumeScraper

# DANH SÁCH TỪ KHÓA TỐI ƯU (Bao gồm cả ngữ cảnh đường phố)
KEYWORDS = [
    # --- Nhóm 1: Biển báo quốc tế & phổ biến ---
    "International road sign", "European traffic sign", "US traffic sign",
    "Japanese road sign", "Australian traffic sign", "UK road sign",
    "German traffic sign", "French road sign", "Canadian traffic sign",
    "Korean road sign", "Chinese traffic sign", "Thailand traffic sign",

    # --- Nhóm 2: Biển báo cảnh báo & chỉ dẫn ---
    "Warning road sign", "Guide road sign", "Mandatory road sign",
    "Yield road sign", "Stop road sign", "No entry road sign",
    "Speed limit road sign", "Pedestrian crossing road sign",
    "Roundabout road sign", "School zone road sign", "Hospital zone road sign",

    # --- Nhóm 3: Ngữ cảnh thực tế ---
    "Street view with traffic signs", "Urban intersection traffic signs",
    "Highway traffic signs", "Rural road traffic signs",
    "Traffic signs at night", "Traffic signs in rain", "Traffic signs in fog",

    # --- Nhóm 4: Biển báo đặc biệt ---
    "Animal crossing road sign", "Slippery road sign", "Road work sign",
    "Children crossing road sign", "No parking road sign", "No stopping road sign",
    "Truck prohibited road sign", "Motorbike prohibited road sign",

    # --- Nhóm 5: Biển báo Việt Nam (giữ lại một số) ---
    "Biển báo giao thông Việt Nam", "Biển báo nguy hiểm Việt Nam",
    "Biển báo chỉ dẫn Việt Nam", "Biển báo cấm Việt Nam",
    "Đường phố Việt Nam có biển báo", "Ngã tư giao thông Việt Nam",

    # --- BỔ SUNG KEYWORD MỚI ---
    "Highway traffic signs",
    "No parking sign",
    "No stopping sign",
    "Urban area traffic sign",
    "School zone traffic sign",
    "Hospital zone traffic sign",
    "Roundabout sign",
    "Yield sign",
    "Children crossing sign",
    "Speed bump sign",
    "Slippery road sign",
    "Animal crossing sign",
    "Road work sign",
    "Dead end sign",
    "One way sign",
    "No entry sign",
    "Residential area traffic sign",
    "Expressway sign",
    "Motorbike prohibited sign",
    "Truck prohibited sign",

    # --- BỔ SUNG: BIỂN CHỈ DẪN & BIỂN CẤM ---
    "Guide sign",
    "Direction sign",
    "Blue guide sign",
    "Green direction sign",
    "Vietnam guide traffic sign",
    "Vietnam direction traffic sign",
    "Biển chỉ dẫn giao thông",
    "Biển chỉ dẫn đường bộ",
    "Biển chỉ dẫn màu xanh",
    "Biển chỉ dẫn đường cao tốc",
    "Prohibition sign",
    "Red prohibition sign",
    "Vietnam prohibition traffic sign",
    "Biển cấm giao thông",
    "Biển cấm đường bộ",
    "Biển cấm màu đỏ",
    "No entry traffic sign",
    "No horn sign",
    "No overtaking sign"
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