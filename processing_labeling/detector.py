from ultralytics import YOLO
import numpy as np
from typing import List, Dict
import torch

try:
    from utils.logger import get_logger
    from config.optimization_config import (
        YOLO_BATCH_SIZE, YOLO_WARMUP_ITERATIONS,
        YOLO_HALF_PRECISION, YOLO_DEVICE
    )
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    YOLO_BATCH_SIZE = 16
    YOLO_WARMUP_ITERATIONS = 3
    YOLO_HALF_PRECISION = False
    YOLO_DEVICE = "cpu"


class TrafficSignDetector:
    """Optimized YOLO detector with batch processing and caching"""
    
    _instance = None
    _model = None
    
    def __new__(cls, model_path="yolov8n.pt"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_path="yolov8n.pt"):
        if self._initialized:
            return
            
        self._initialized = True
        self.model_path = model_path
        self.device = YOLO_DEVICE
        
        # Load model (singleton pattern - load once)
        if TrafficSignDetector._model is None:
            logger.info(f"Loading YOLO model: {model_path} on {self.device}")
            TrafficSignDetector._model = YOLO(model_path)
            
            # Move to GPU if available
            if self.device == "cuda" and torch.cuda.is_available():
                TrafficSignDetector._model.to(self.device)
                logger.info(f"[OK] YOLO on GPU: {torch.cuda.get_device_name(0)}")
                
                # Enable half precision for faster inference
                if YOLO_HALF_PRECISION:
                    TrafficSignDetector._model.half()
                    logger.info("[OK] Half precision (FP16) enabled")
            else:
                logger.info("[OK] YOLO on CPU")
            
            # Warmup model
            self._warmup()
        
        self.model = TrafficSignDetector._model
    
    def _warmup(self):
        """Warmup model for consistent performance"""
        logger.info(f"Warming up model ({YOLO_WARMUP_ITERATIONS} iterations)...")
        dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        for i in range(YOLO_WARMUP_ITERATIONS):
            _ = TrafficSignDetector._model(dummy_img, verbose=False, conf=0.25)
        
        logger.info("Model warmed up")
    
    def detect(self, image):
        """
        Detect objects in a single image
        
        Args:
            image: Single image (numpy array)
            
        Returns:
            List of detections with bbox, confidence, label
        """
        results = self.model(image, conf=0.15, verbose=False)
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                detections.append({
                    "bbox": box.xyxy[0].cpu().numpy(),  # [x1, y1, x2, y2]
                    "confidence": float(box.conf[0]),
                    "label": self.model.names[int(box.cls[0])]
                })
        return detections
    
    def detect_batch(self, images: List[np.ndarray], conf_threshold: float = 0.15) -> List[List[Dict]]:
        """
        Batch detection for multiple images (10-20x faster than single detection)
        
        Args:
            images: List of images (numpy arrays)
            conf_threshold: Confidence threshold
            
        Returns:
            List of detection lists (one per image)
        """
        if not images:
            return []
        
        # Run batch inference
        results = self.model(images, conf=conf_threshold, verbose=False)
        
        # Parse results for each image
        all_detections = []
        for r in results:
            detections = []
            boxes = r.boxes
            for box in boxes:
                detections.append({
                    "bbox": box.xyxy[0].cpu().numpy(),
                    "confidence": float(box.conf[0]),
                    "label": self.model.names[int(box.cls[0])]
                })
            all_detections.append(detections)
        
        return all_detections
    
    def detect_batch_generator(self, images: List[np.ndarray], batch_size: int = YOLO_BATCH_SIZE, 
                               conf_threshold: float = 0.15):
        """
        Generator for processing large image lists in batches
        
        Args:
            images: List of images
            batch_size: Batch size for inference
            conf_threshold: Confidence threshold
            
        Yields:
            (batch_start_idx, batch_detections)
        """
        total = len(images)
        
        for i in range(0, total, batch_size):
            batch = images[i:min(i + batch_size, total)]
            batch_detections = self.detect_batch(batch, conf_threshold)
            yield (i, batch_detections)
