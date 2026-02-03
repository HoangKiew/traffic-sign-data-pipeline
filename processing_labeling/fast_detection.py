"""
Fast Detection Pipeline - Skip preprocessing, detect directly from MinIO
"""
import os
import cv2
import glob
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

try:
    from utils.database import MinIOClient
    from utils.logger import get_logger
    logger = get_logger()
except:
    from utils.database import MinIOClient
    import logging
    logger = logging.getLogger(__name__)

# --- CONFIG ---
LABEL_DIR = "datasets/labels"
MODEL_PATH = "yolov8n.pt"
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.65
MAX_BOXES = 5
BATCH_SIZE = 16  # Process 16 images at once

# --- COLOR RANGES (HSV) ---
LOWER_RED1 = np.array([0, 50, 50]); UPPER_RED1 = np.array([15, 255, 255])
LOWER_RED2 = np.array([160, 50, 50]); UPPER_RED2 = np.array([180, 255, 255])
LOWER_BLUE = np.array([90, 50, 50]); UPPER_BLUE = np.array([150, 255, 255])
LOWER_YELLOW = np.array([15, 50, 50]); UPPER_YELLOW = np.array([35, 255, 255])

def get_class_v2(img_crop):
    """Color-based classification"""
    h, w = img_crop.shape[:2]
    area = h * w
    if area == 0: return 4
    
    hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
    mask_r = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1) + cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    mask_b = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
    mask_y = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
    
    r = cv2.countNonZero(mask_r)
    b = cv2.countNonZero(mask_b)
    y = cv2.countNonZero(mask_y)
    thr = area * 0.05
    
    if y > thr and y > b: return 1  # Warning
    if r > thr and r > b: return 1 if (r/area < 0.35) else 0  # Prohibition/Warning
    if b > thr: return 3 if (b/area > 0.80) else 2  # Instruction/Command
    return 4

def compute_iou(box1, box2):
    """Calculate IoU"""
    b1 = box1['xyxy']; b2 = box2['xyxy']
    xi1 = max(b1[0], b2[0]); yi1 = max(b1[1], b2[1])
    xi2 = min(b1[2], b2[2]); yi2 = min(b1[3], b2[3])
    inter = max(0, xi2-xi1) * max(0, yi2-yi1)
    union = box1['area'] + box2['area'] - inter
    return inter/union if union > 0 else 0

def run_fast_detection():
    """Fast detection directly from MinIO"""
    
    # 1. Setup
    os.makedirs(LABEL_DIR, exist_ok=True)
    logger.section("Fast Detection Pipeline")
    logger.info("Loading YOLO model...")
    model = YOLO(MODEL_PATH)
    
    # 2. Get images from MinIO
    logger.info("Connecting to MinIO...")
    minio = MinIOClient()
    all_images = minio.list_images()
    
    logger.info(f"Found {len(all_images)} images in MinIO")
    logger.info(f"Starting detection (batch size: {BATCH_SIZE})...")
    
    stats = {0:0, 1:0, 2:0, 3:0, 4:0}
    processed_count = 0
    
    # 3. Process in batches
    for i in tqdm(range(0, len(all_images), BATCH_SIZE), desc="Batches"):
        batch_names = all_images[i:i+BATCH_SIZE]
        batch_images = []
        valid_names = []
        
        # Download batch
        for img_name in batch_names:
            data = minio.download_image(img_name)
            if data:
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    batch_images.append(img)
                    valid_names.append(img_name)
        
        if not batch_images:
            continue
        
        # Batch detection
        results = model(batch_images, verbose=False, conf=CONF_THRESHOLD)
        
        # Process each image in batch
        for img, img_name, r in zip(batch_images, valid_names, results):
            h_img, w_img = img.shape[:2]
            
            candidates = []
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                
                cls_id = get_class_v2(crop)
                area = (x2-x1)*(y2-y1)
                score = area * (0.1 if cls_id == 4 else 1.0)
                
                candidates.append({
                    'cls': cls_id,
                    'xyxy': [x1, y1, x2, y2],
                    'area': area,
                    'score': score
                })
            
            # NMS
            candidates.sort(key=lambda x: x['score'], reverse=True)
            final_boxes = []
            while candidates:
                curr = candidates.pop(0)
                is_dup = False
                for kept in final_boxes:
                    if compute_iou(curr, kept) > IOU_THRESHOLD:
                        is_dup = True
                        break
                if not is_dup:
                    final_boxes.append(curr)
            
            if len(final_boxes) > MAX_BOXES:
                final_boxes = final_boxes[:MAX_BOXES]
            
            # Save labels
            if final_boxes:
                base_name = os.path.splitext(img_name)[0]
                txt_path = os.path.join(LABEL_DIR, base_name + ".txt")
                
                with open(txt_path, "w") as f:
                    for b in final_boxes:
                        x1, y1, x2, y2 = b['xyxy']
                        xc = ((x1+x2)/2) / w_img
                        yc = ((y1+y2)/2) / h_img
                        w = (x2-x1) / w_img
                        h = (y2-y1) / h_img
                        
                        f.write(f"{b['cls']} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                        stats[b['cls']] += 1
                
                processed_count += 1
    
    # Print summary
    logger.section("Detection Complete")
    logger.info(f"Processed images: {processed_count}")
    logger.info("Class distribution:")
    logger.info(f"  0 - Prohibition: {stats[0]}")
    logger.info(f"  1 - Warning:     {stats[1]}")
    logger.info(f"  2 - Command:     {stats[2]}")
    logger.info(f"  3 - Instruction: {stats[3]}")
    logger.info(f"  4 - Other:       {stats[4]}")
    logger.info(f"Total objects: {sum(stats.values())}")
    logger.info(f"Labels saved to: {LABEL_DIR}/")

if __name__ == "__main__":
    run_fast_detection()
