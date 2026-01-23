"""
Module chính cho quy trình xử lý và gán nhãn
"""
import cv2
import numpy as np
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing_labeling.detector import TrafficSignDetector
from processing_labeling.cropper import ImageCropper
from processing_labeling.vlm_verifier import VLMVerifier


class TrafficSignLabeler:
    """Quy trình xử lý và gán nhãn tự động cho biển báo"""
    
    def __init__(self):
        self.detector = TrafficSignDetector()
        self.cropper = ImageCropper()
        self.verifier = VLMVerifier()
    
    def process_image(self, image: np.ndarray, image_name: str = None) -> List[Dict]:
        """
        Xử lý một ảnh: Detect -> Crop -> Verify -> Label
        
        Args:
            image: Ảnh đầu vào (BGR)
            image_name: Tên ảnh (để tracking)
            
        Returns:
            List các dict chứa thông tin biển báo đã được xác thực:
            {
                "image_name": str,
                "cropped_image": np.ndarray,
                "label": str,
                "confidence": float,
                "bbox": [x1, y1, x2, y2],
                "verified": bool,
                "verification_reason": str
            }
        """
        results = []
        
        # 1. Detect objects
        detections = self.detector.detect(image)
        
        # 2. Filter chỉ lấy biển báo
        traffic_signs = self.detector.filter_traffic_signs(detections)
        
        if len(traffic_signs) == 0:
            return results
        
        # 3. Crop biển báo
        cropped_results = self.cropper.crop_multiple(image, traffic_signs)
        
        # 4. Verify từng biển báo
        for cropped_result in cropped_results:
            cropped_image = cropped_result["cropped_image"]
            predicted_label = cropped_result["class_name"]
            
            # Verify bằng VLM
            is_valid, reason = self.verifier.verify(cropped_image, predicted_label)
            
            if is_valid:
                # Chỉ thêm vào kết quả nếu được verify
                result = {
                    "image_name": image_name or "unknown",
                    "cropped_image": cropped_image,
                    "label": predicted_label,
                    "confidence": cropped_result["confidence"],
                    "bbox": cropped_result["bbox"],
                    "verified": True,
                    "verification_reason": reason
                }
                results.append(result)
            else:
                print(f"Bỏ qua biển báo không được verify: {reason}")
        
        return results
    
    def process_batch(self, images: List[np.ndarray], image_names: List[str] = None) -> List[Dict]:
        """
        Xử lý nhiều ảnh
        
        Args:
            images: List các ảnh
            image_names: List tên ảnh tương ứng
            
        Returns:
            List tất cả các biển báo đã được xác thực
        """
        all_results = []
        
        if image_names is None:
            image_names = [f"image_{i}" for i in range(len(images))]
        
        for image, image_name in zip(images, image_names):
            results = self.process_image(image, image_name)
            all_results.extend(results)
        
        return all_results
