import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import cv2
import numpy as np

class VLMVerifier:
    def __init__(self, model_name="Salesforce/blip-vqa-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⏳ Loading VLM Model ({model_name}) on {self.device}...")
        try:
            self.processor = BlipProcessor.from_pretrained(model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(model_name).to(self.device)
            print("✅ VLM Ready.")
        except Exception as e:
            print(f"⚠️ VLM Error: {e}")
            self.model = None

    def verify(self, img_crop, label):
        """
        Hỏi VLM xem ảnh crop có phải là biển báo không.
        Trả về: (True/False, Lý do)
        """
        if not self.model: 
            return True, "No VLM Model (Bypass)"
        
        # Chuyển ảnh numpy (BGR) -> PIL (RGB)
        if isinstance(img_crop, np.ndarray):
            pil_img = Image.fromarray(cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB))
        else:
            pil_img = img_crop
        
        # Tạo câu hỏi Yes/No cho VQA
        # Hỏi xem đây có phải là biển báo giao thông không
        question = f"Is this a traffic sign or a street sign? Answer yes or no."
        
        inputs = self.processor(pil_img, question, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            out = self.model.generate(**inputs)
        
        ans = self.processor.decode(out[0], skip_special_tokens=True).lower()
        
        # Logic: Nếu câu trả lời chứa "yes" -> Đúng là biển báo
        is_valid = "yes" in ans
        
        return is_valid, f"VLM Answer: {ans}"