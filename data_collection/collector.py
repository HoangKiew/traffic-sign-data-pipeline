"""
Module thu thập dữ liệu: Kết nối ảnh từ MinIO/Web với Metadata từ MongoDB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import MinIOClient, MongoDBClient
from config.config import MONGODB_COLLECTION_METADATA
from typing import List, Dict, Any, Optional
import cv2
import numpy as np


class DataCollector:
    """Thu thập và tích hợp dữ liệu từ MinIO và MongoDB"""
    
    def __init__(self, use_web_sources: bool = False):
        """
        Args:
            use_web_sources: Nếu True, sẽ tải ảnh từ web. Nếu False, chỉ lấy từ MinIO
        """
        self.minio_client = MinIOClient()
        self.mongodb_client = MongoDBClient()
        self.use_web_sources = use_web_sources
    
    def integrate_image_with_metadata(self, image_name: str) -> Dict[str, Any]:
        """
        Tích hợp ảnh từ MinIO với metadata từ MongoDB
        
        Args:
            image_name: Tên file ảnh trong MinIO
            
        Returns:
            Dict chứa image_data (bytes) và metadata
        """
        # Download ảnh từ MinIO
        image_data = self.minio_client.download_image(image_name)
        if image_data is None:
            return None
        
        # Lấy metadata từ MongoDB (giả sử image_name là key để tìm metadata)
        metadata = self.mongodb_client.db[MONGODB_COLLECTION_METADATA].find_one(
            {"image_name": image_name}
        )
        
        if metadata is None:
            # Nếu chưa có metadata, tạo metadata mặc định
            metadata = {
                "image_name": image_name,
                "location": "unknown",
                "road_type": "unknown",
                "weather": "unknown"
            }
        
        return {
            "image_name": image_name,
            "image_data": image_data,
            "metadata": metadata
        }
    
    def get_all_images(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả ảnh kèm metadata từ MinIO hoặc local storage
        
        Returns:
            List các dict chứa image_data và metadata
        """
        # Lấy danh sách ảnh từ MinIO
        image_names = self.minio_client.list_images()
        
        integrated_data = []
        for image_name in image_names:
            integrated = self.integrate_image_with_metadata(image_name)
            if integrated:
                integrated_data.append(integrated)
        
        return integrated_data
    
    def get_all_images_including_local(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả ảnh từ cả MinIO và local storage (raw_images/)
        
        Returns:
            List các dict chứa image_data và metadata
        """
        integrated_data = self.get_all_images()  # Từ MinIO
        
        # Nếu có local images, thêm vào
        raw_images_dir = "raw_images"
        if os.path.exists(raw_images_dir):
            for filename in os.listdir(raw_images_dir):
                file_path = os.path.join(raw_images_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            image_data = f.read()
                        
                        # Lấy metadata từ MongoDB
                        metadata = self.mongodb_client.db[MONGODB_COLLECTION_METADATA].find_one(
                            {"image_name": filename}
                        )
                        
                        if metadata is None:
                            metadata = {
                                "image_name": filename,
                                "location": "Vietnam",
                                "road_type": "unknown",
                                "weather": "unknown",
                                "source": "local"
                            }
                        
                        integrated_data.append({
                            "image_name": filename,
                            "image_data": image_data,
                            "metadata": metadata
                        })
                    except Exception as e:
                        print(f"⚠️  Lỗi đọc {file_path}: {str(e)}")
        
        return integrated_data
    
    def add_sample_metadata(self, image_name: str, location: str = None, 
                           road_type: str = None, weather: str = None):
        """
        Thêm metadata mẫu cho ảnh (dùng để test)
        
        Args:
            image_name: Tên file ảnh
            location: Vị trí chụp
            road_type: Loại đường
            weather: Điều kiện thời tiết
        """
        metadata = {
            "image_name": image_name,
            "location": location or "unknown",
            "road_type": road_type or "unknown",
            "weather": weather or "unknown"
        }
        
        # Kiểm tra xem đã có metadata chưa
        existing = self.mongodb_client.db[MONGODB_COLLECTION_METADATA].find_one(
            {"image_name": image_name}
        )
        
        if existing:
            # Cập nhật
            self.mongodb_client.update_metadata(
                MONGODB_COLLECTION_METADATA,
                {"image_name": image_name},
                metadata
            )
        else:
            # Thêm mới
            self.mongodb_client.insert_metadata(MONGODB_COLLECTION_METADATA, metadata)
