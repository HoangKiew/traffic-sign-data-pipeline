"""
Cấu hình các nguồn web để tải ảnh biển báo giao thông
"""

# Danh sách các URL trực tiếp từ các trang web khác nhau
DIRECT_IMAGE_URLS = {
    "wikimedia_commons": [
        "https://commons.wikimedia.org/wiki/Vietnam_traffic_signs",
        # Các URL ảnh trực tiếp có thể thêm ở đây
    ],
    
    "google_images": {
        "query": "Vietnam traffic sign",
        "note": "Sử dụng Google Images API hoặc Selenium để crawl"
    },
    
    "other_sources": []
}

# Cấu hình Wikimedia Commons
WIKIMEDIA_CONFIG = {
    "base_url": "https://commons.wikimedia.org/w/api.php",
    "search_queries": [
        "Vietnam traffic sign",
        "stop sign Vietnam",
        "warning sign Vietnam",
        "speed limit sign Vietnam",
        "no entry sign Vietnam",
        "yield sign Vietnam"
    ],
    "images_per_query": 15,
    "timeout": 15
}

# Cấu hình Google Images (nếu muốn dùng)
GOOGLE_IMAGES_CONFIG = {
    "enabled": False,  # Cần cài đặt thêm selenium
    "search_queries": [
        "biển báo giao thông Việt Nam",
        "Vietnam traffic signs",
        "dấu hiệu giao thông"
    ]
}

# Cấu hình các trang web khác
OTHER_SOURCES = [
    # Có thể thêm các trang web khác như: Flickr, Pixabay, v.v.
    # {
    #     "name": "flickr",
    #     "api_key": "your_api_key",
    #     "search_query": "Vietnam traffic sign"
    # }
]

# Thông tin metadata mặc định
DEFAULT_METADATA = {
    "location": "Vietnam",
    "road_type": "urban",
    "weather": "clear",
    "collection_method": "web_scraping"
}
