import matplotlib.pyplot as plt
import cv2
import numpy as np

class DataVisualizer:
    # (Giữ nguyên các hàm cũ visualize_preprocessing...)

    def plot_class_distribution(self, count_dict):
        """
        Vẽ biểu đồ phân bố số lượng các loại biển báo
        """
        if not count_dict:
            print("⚠️ Không có dữ liệu để vẽ biểu đồ.")
            return

        classes = list(count_dict.keys())
        counts = list(count_dict.values())

        plt.figure(figsize=(12, 6))
        bars = plt.bar(classes, counts, color='skyblue')
        
        plt.xlabel('Loại biển báo')
        plt.ylabel('Số lượng (Objects)')
        plt.title('Thống kê số lượng biển báo sau khi lọc')
        plt.xticks(rotation=45, ha='right')
        
        # Hiển thị số trên đầu cột
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig("distribution_chart.png") # Lưu biểu đồ thành file ảnh
        print("📊 Đã lưu biểu đồ thống kê tại 'distribution_chart.png'")
        # plt.show() # Bật dòng này nếu chạy trên máy có màn hình   