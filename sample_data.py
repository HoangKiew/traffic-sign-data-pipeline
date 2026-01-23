"""
Script tạo dữ liệu mẫu để test pipeline
"""
import cv2
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import MinIOClient, MongoDBClient
from config.config import MONGODB_COLLECTION_METADATA


def create_sample_traffic_sign_image():
    """Tạo ảnh mẫu biển báo stop sign đơn giản"""
    # Tạo ảnh nền
    image = np.ones((640, 640, 3), dtype=np.uint8) * 255
    
    # Vẽ biển báo stop (hình bát giác đỏ với chữ STOP trắng)
    center = (320, 320)
    radius = 100
    
    # Vẽ hình bát giác đỏ
    points = []
    for i in range(8):
        angle = np.pi * i / 4
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        points.append([x, y])
    
    points = np.array(points, np.int32)
    cv2.fillPoly(image, [points], (0, 0, 255))  # Màu đỏ
    
    # Vẽ chữ STOP
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = "STOP"
    text_size = cv2.getTextSize(text, font, 2, 5)[0]
    text_x = center[0] - text_size[0] // 2
    text_y = center[1] + text_size[1] // 2
    cv2.putText(image, text, (text_x, text_y), font, 2, (255, 255, 255), 5)
    
    return image


def upload_sample_data(num_samples: int = 5):
    """Upload dữ liệu mẫu lên MinIO và MongoDB"""
    print(f"Đang tạo {num_samples} ảnh mẫu...")
    
    minio_client = MinIOClient()
    mongodb_client = MongoDBClient()
    
    for i in range(num_samples):
        # Tạo ảnh mẫu
        image = create_sample_traffic_sign_image()
        
        # Encode ảnh thành bytes
        _, encoded = cv2.imencode('.jpg', image)
        image_bytes = encoded.tobytes()
        
        # Upload lên MinIO
        image_name = f"sample_traffic_sign_{i:03d}.jpg"
        success = minio_client.upload_image(image_bytes, image_name)
        
        if success:
            print(f"✓ Đã upload: {image_name}")
            
            # Thêm metadata vào MongoDB
            metadata = {
                "image_name": image_name,
                "location": f"sample_location_{i}",
                "road_type": "highway" if i % 2 == 0 else "city_street",
                "weather": "sunny" if i % 3 == 0 else "cloudy"
            }
            mongodb_client.insert_metadata(MONGODB_COLLECTION_METADATA, metadata)
        else:
            print(f"✗ Lỗi upload: {image_name}")
    
    print(f"\n✓ Đã tạo {num_samples} ảnh mẫu")
    print("Bây giờ bạn có thể chạy main.py để xử lý dữ liệu")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo dữ liệu mẫu")
    parser.add_argument("--num", type=int, default=5, help="Số lượng ảnh mẫu")
    args = parser.parse_args()
    
    upload_sample_data(args.num)
