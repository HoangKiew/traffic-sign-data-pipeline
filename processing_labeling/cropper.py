"""
Module cắt ảnh biển báo từ ảnh gốc
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional


class ImageCropper:
    """Cắt ảnh biển báo dựa trên bounding box"""
    
    def crop(self, image: np.ndarray, bbox: List[float], 
             padding_ratio: float = 0.1) -> np.ndarray:
        """
        Cắt ảnh biển báo từ ảnh gốc
        
        Args:
            image: Ảnh gốc
            bbox: Bounding box [x1, y1, x2, y2]
            padding_ratio: Tỷ lệ padding thêm xung quanh (0.1 = 10%)
            
        Returns:
            Ảnh đã cắt
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        
        # Chuyển về int
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Tính padding
        width = x2 - x1
        height = y2 - y1
        pad_w = int(width * padding_ratio)
        pad_h = int(height * padding_ratio)
        
        # Mở rộng bbox với padding
        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)
        x2 = min(w, x2 + pad_w)
        y2 = min(h, y2 + pad_h)
        
        # Cắt ảnh
        cropped = image[y1:y2, x1:x2]
        
        return cropped
    
    def crop_multiple(self, image: np.ndarray, detections: List[Dict],
                     padding_ratio: float = 0.1) -> List[Dict]:
        """
        Cắt nhiều biển báo từ một ảnh
        
        Args:
            image: Ảnh gốc
            detections: List các detection với bbox
            padding_ratio: Tỷ lệ padding
            
        Returns:
            List các dict chứa ảnh đã cắt và thông tin:
            {
                "cropped_image": np.ndarray,
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_name": str
            }
        """
        cropped_results = []
        
        for det in detections:
            cropped_image = self.crop(image, det["bbox"], padding_ratio)
            
            cropped_results.append({
                "cropped_image": cropped_image,
                "bbox": det["bbox"],
                "confidence": det["confidence"],
                "class_name": det["class_name"],
                "class_id": det.get("class_id", -1)
            })
        
        return cropped_results
