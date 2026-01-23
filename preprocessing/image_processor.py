"""
Module tiền xử lý ảnh: Làm sạch và chuẩn hóa ảnh biển báo
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    IMAGE_TARGET_SIZE, PADDING_COLOR,
    BILATERAL_D, BILATERAL_SIGMA_COLOR, BILATERAL_SIGMA_SPACE,
    CLAHE_CLIP_LIMIT, CLAHE_TILE_GRID_SIZE,
    SHARPNESS_THRESHOLD, UNSHARP_AMOUNT, UNSHARP_SIGMA
)


class ImagePreprocessor:
    """Xử lý tiền xử lý ảnh biển báo"""
    
    def __init__(self):
        self.clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_TILE_GRID_SIZE
        )
    
    def denoise(self, image: np.ndarray, method: str = "bilateral") -> np.ndarray:
        """
        Khử nhiễu ảnh
        
        Args:
            image: Ảnh đầu vào (BGR)
            method: "bilateral" hoặc "median"
            
        Returns:
            Ảnh đã khử nhiễu
        """
        if method == "bilateral":
            # Bilateral Filter: Giữ được edge nhưng làm mịn bề mặt
            denoised = cv2.bilateralFilter(
                image,
                d=BILATERAL_D,
                sigmaColor=BILATERAL_SIGMA_COLOR,
                sigmaSpace=BILATERAL_SIGMA_SPACE
            )
        elif method == "median":
            # Median Filter: Tốt cho nhiễu muối tiêu
            denoised = cv2.medianBlur(image, 5)
        else:
            denoised = image
        
        return denoised
    
    def correct_lighting(self, image: np.ndarray) -> np.ndarray:
        """
        Cân bằng sáng bằng CLAHE trong không gian màu LAB
        
        Args:
            image: Ảnh đầu vào (BGR)
            
        Returns:
            Ảnh đã cân bằng sáng
        """
        # Chuyển sang LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Áp dụng CLAHE lên kênh L (độ sáng)
        l_clahe = self.clahe.apply(l)
        
        # Gộp lại và chuyển về BGR
        lab_clahe = cv2.merge([l_clahe, a, b])
        corrected = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        
        return corrected
    
    def measure_sharpness(self, image: np.ndarray) -> float:
        """
        Đo độ sắc nét bằng Laplacian Variance
        
        Args:
            image: Ảnh đầu vào (grayscale hoặc BGR)
            
        Returns:
            Giá trị variance (càng cao càng sắc nét)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return variance
    
    def enhance_sharpness(self, image: np.ndarray) -> np.ndarray:
        """
        Tăng cường độ sắc nét bằng Unsharp Masking
        
        Args:
            image: Ảnh đầu vào (BGR)
            
        Returns:
            Ảnh đã tăng cường độ sắc nét
        """
        # Tạo Gaussian blur
        gaussian = cv2.GaussianBlur(image, (0, 0), UNSHARP_SIGMA)
        
        # Unsharp masking
        sharpened = cv2.addWeighted(image, 1.0 + UNSHARP_AMOUNT, gaussian, -UNSHARP_AMOUNT, 0)
        
        return sharpened
    
    def resize_with_padding(self, image: np.ndarray, target_size: Tuple[int, int] = None) -> Tuple[np.ndarray, Tuple[float, float]]:
        """
        Resize ảnh về kích thước chuẩn với padding để giữ tỷ lệ khung hình
        
        Args:
            image: Ảnh đầu vào
            target_size: Kích thước đích (width, height)
            
        Returns:
            (Ảnh đã resize với padding, (scale_x, scale_y))
        """
        if target_size is None:
            target_size = IMAGE_TARGET_SIZE
        
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # Tính tỷ lệ scale
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize ảnh
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Tạo ảnh mới với padding
        padded = np.full((target_h, target_w, 3), PADDING_COLOR, dtype=np.uint8)
        
        # Tính vị trí để đặt ảnh vào giữa
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        
        # Đặt ảnh vào giữa
        padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        scale_x = scale
        scale_y = scale
        
        return padded, (scale_x, scale_y)
    
    def process_image(self, image: np.ndarray, check_sharpness: bool = True) -> Tuple[np.ndarray, dict]:
        """
        Xử lý toàn bộ pipeline tiền xử lý
        
        Args:
            image: Ảnh đầu vào (BGR)
            check_sharpness: Có kiểm tra độ sắc nét không
            
        Returns:
            (Ảnh đã xử lý, dict thông tin xử lý)
        """
        processing_info = {}
        
        # 1. Khử nhiễu
        denoised = self.denoise(image, method="bilateral")
        processing_info["denoised"] = True
        
        # 2. Cân bằng sáng
        light_corrected = self.correct_lighting(denoised)
        processing_info["light_corrected"] = True
        
        # 3. Kiểm tra và tăng cường độ sắc nét
        sharpness = self.measure_sharpness(light_corrected)
        processing_info["sharpness"] = sharpness
        
        if check_sharpness and sharpness < SHARPNESS_THRESHOLD:
            # Ảnh bị mờ, tăng cường độ sắc nét
            sharpened = self.enhance_sharpness(light_corrected)
            processing_info["sharpness_enhanced"] = True
        else:
            sharpened = light_corrected
            processing_info["sharpness_enhanced"] = False
        
        # 4. Resize với padding
        final_image, scales = self.resize_with_padding(sharpened)
        processing_info["resized"] = True
        processing_info["scale"] = scales
        
        return final_image, processing_info
