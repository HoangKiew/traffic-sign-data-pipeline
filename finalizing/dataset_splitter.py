import os
import cv2
import yaml
import shutil
import numpy as np

class DatasetSplitter:
    def __init__(self, output_dir="output_dataset", viz_dir="output_categorized"):
        self.output_dir = output_dir
        self.viz_dir = viz_dir  # Thư mục chứa ảnh đã phân loại
        
        # Tạo thư mục YOLO standard
        for split in ['train', 'val']:
            os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)

    def save_categorized_images(self, dataset):
        """
        Lưu ảnh CẮT (Crop) vào từng folder theo tên class để trực quan hóa
        Ví dụ: output_categorized/stop_sign/img1.jpg
        """
        print(f"\n📂 Đang phân loại ảnh vào thư mục '{self.viz_dir}'...")
        
        if os.path.exists(self.viz_dir):
            shutil.rmtree(self.viz_dir) # Xóa cũ tạo mới
            
        count_dict = {}

        for item in dataset:
            img = item['original_image']
            
            for i, obj in enumerate(item['objects']):
                label = obj['label'] # Tên class (VD: stop sign)
                bbox = obj['bbox']
                
                # Tạo folder cho class đó nếu chưa có
                class_dir = os.path.join(self.viz_dir, label.replace(" ", "_"))
                os.makedirs(class_dir, exist_ok=True)
                
                # Cắt ảnh (Crop)
                x1, y1, x2, y2 = map(int, bbox)
                h, w = img.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                crop = img[y1:y2, x1:x2]
                
                # Lưu ảnh crop
                save_name = f"{item['image_name'].split('.')[0]}_obj{i}.jpg"
                cv2.imwrite(os.path.join(class_dir, save_name), crop)
                
                # Đếm số lượng
                count_dict[label] = count_dict.get(label, 0) + 1
                
        print(f"✅ Đã phân loại xong! Bạn có thể vào '{self.viz_dir}' để xem.")
        return count_dict

    def save_yolo_format(self, dataset, train_ratio=0.8):
        # (Giữ nguyên code cũ của hàm này)
        print(f"💾 Đang lưu {len(dataset)} ảnh vào '{self.output_dir}' chuẩn YOLO...")
        
        yaml_data = {
            'train': os.path.abspath(os.path.join(self.output_dir, "train")),
            'val': os.path.abspath(os.path.join(self.output_dir, "val")),
            'nc': 1,
            'names': ['traffic_sign']
        }
        with open(os.path.join(self.output_dir, "data.yaml"), 'w') as f:
            yaml.dump(yaml_data, f)

        np.random.shuffle(dataset)
        split_idx = int(len(dataset) * train_ratio)
        
        for i, item in enumerate(dataset):
            split = 'train' if i < split_idx else 'val'
            img_name = item['image_name']
            img = item['original_image']
            h, w = img.shape[:2]
            
            img_path = os.path.join(self.output_dir, split, "images", img_name)
            txt_path = os.path.join(self.output_dir, split, "labels", img_name.replace('.jpg', '.txt').replace('.png', '.txt'))
            
            cv2.imwrite(img_path, img)
            
            txt_lines = []
            for obj in item['objects']:
                x1, y1, x2, y2 = obj['bbox']
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                xc = (x1 + x2) / 2 / w
                yc = (y1 + y2) / 2 / h
                txt_lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
            
            with open(txt_path, 'w') as f:
                f.write("\n".join(txt_lines))