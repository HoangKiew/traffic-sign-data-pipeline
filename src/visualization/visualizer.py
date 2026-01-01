"""
Visualization Module
Tạo các biểu đồ và báo cáo thống kê theo workflow trong slide
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class DataVisualizer:
    """Visualize traffic sign dataset"""
    
    def __init__(self, metadata_path='data/metadata.csv'):
        self.df = pd.read_csv(metadata_path)
        self.output_dir = Path('reports/figures')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 6)
    
    def create_summary_table(self):
        """
        Tạo bảng mô tả dữ liệu theo slide:
        - Thống kê tổng quan
        """
        print("\n" + "="*60)
        print("📊 BẢNG MÔ TẢ DỮ LIỆU")
        print("="*60)
        
        summary = {
            'Tổng số ảnh': len(self.df),
            'Số categories': self.df['category'].nunique(),
            'Width trung bình': f"{self.df['width'].mean():.1f}px",
            'Height trung bình': f"{self.df['height'].mean():.1f}px",
            'Kích thước file TB': f"{self.df['size_kb'].mean():.1f}KB",
            'Format phổ biến': self.df['format'].mode()[0] if len(self.df) > 0 else 'N/A'
        }
        
        for key, value in summary.items():
            print(f"  {key:.<30} {value}")
        
        return summary
    
    def plot_category_distribution(self):
        """
        Bar chart: Phân bố số lượng theo category
        Theo slide: "Biểu đồ bar chart"
        """
        plt.figure(figsize=(10, 6))
        
        category_counts = self.df['category'].value_counts()
        
        ax = category_counts.plot(kind='bar', color='steelblue', edgecolor='black')
        plt.title('Phân bố số lượng ảnh theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Số lượng ảnh', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Thêm số liệu trên mỗi cột
        for i, v in enumerate(category_counts):
            ax.text(i, v + 5, str(v), ha='center', fontweight='bold')
        
        plt.tight_layout()
        output_path = self.output_dir / 'category_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Đã lưu: {output_path}")
        plt.close()
    
    def plot_size_histogram(self):
        """
        Histogram: Phân bố kích thước ảnh
        Theo slide: "Biểu đồ histogram"
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Width histogram
        axes[0].hist(self.df['width'], bins=30, color='skyblue', edgecolor='black')
        axes[0].set_title('Phân bố Width', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Width (pixels)', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].axvline(self.df['width'].mean(), color='red', linestyle='--', 
                       label=f'Mean: {self.df["width"].mean():.1f}')
        axes[0].legend()
        
        # Height histogram
        axes[1].hist(self.df['height'], bins=30, color='lightcoral', edgecolor='black')
        axes[1].set_title('Phân bố Height', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Height (pixels)', fontsize=11)
        axes[1].set_ylabel('Frequency', fontsize=11)
        axes[1].axvline(self.df['height'].mean(), color='red', linestyle='--',
                       label=f'Mean: {self.df["height"].mean():.1f}')
        axes[1].legend()
        
        plt.tight_layout()
        output_path = self.output_dir / 'size_histogram.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Đã lưu: {output_path}")
        plt.close()
    
    def plot_scatter(self):
        """
        Scatter plot: Width vs Height
        Theo slide: "scatter plot"
        """
        plt.figure(figsize=(10, 8))
        
        # Color by category
        categories = self.df['category'].unique()
        colors = plt.cm.Set3(range(len(categories)))
        
        for i, category in enumerate(categories):
            data = self.df[self.df['category'] == category]
            plt.scatter(data['width'], data['height'], 
                       label=category, alpha=0.6, s=50, color=colors[i])
        
        plt.title('Scatter Plot: Width vs Height', fontsize=16, fontweight='bold')
        plt.xlabel('Width (pixels)', fontsize=12)
        plt.ylabel('Height (pixels)', fontsize=12)
        plt.legend(title='Category')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'scatter_width_height.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Đã lưu: {output_path}")
        plt.close()
    
    def plot_statistics(self):
        """
        Biểu đồ thống kê: mean, median, std
        Theo slide: "Báo cáo thống kê tổng quan (mean, median, std)"
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Box plot - Width
        axes[0, 0].boxplot([self.df['width']], labels=['Width'])
        axes[0, 0].set_title('Box Plot - Width', fontweight='bold')
        axes[0, 0].set_ylabel('Pixels')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Box plot - Height
        axes[0, 1].boxplot([self.df['height']], labels=['Height'])
        axes[0, 1].set_title('Box Plot - Height', fontweight='bold')
        axes[0, 1].set_ylabel('Pixels')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Statistics comparison
        stats_data = {
            'Width': [self.df['width'].mean(), self.df['width'].median(), self.df['width'].std()],
            'Height': [self.df['height'].mean(), self.df['height'].median(), self.df['height'].std()]
        }
        stats_df = pd.DataFrame(stats_data, index=['Mean', 'Median', 'Std'])
        
        x = range(len(stats_df.index))
        width = 0.35
        axes[1, 0].bar([i - width/2 for i in x], stats_df['Width'], width, label='Width', color='skyblue')
        axes[1, 0].bar([i + width/2 for i in x], stats_df['Height'], width, label='Height', color='lightcoral')
        axes[1, 0].set_title('Thống kê: Mean, Median, Std', fontweight='bold')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(stats_df.index)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # 4. File size distribution
        axes[1, 1].hist(self.df['size_kb'], bins=30, color='mediumseagreen', edgecolor='black')
        axes[1, 1].set_title('Phân bố kích thước file', fontweight='bold')
        axes[1, 1].set_xlabel('Size (KB)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].axvline(self.df['size_kb'].mean(), color='red', linestyle='--',
                          label=f'Mean: {self.df["size_kb"].mean():.1f}KB')
        axes[1, 1].legend()
        
        plt.tight_layout()
        output_path = self.output_dir / 'statistics_summary.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Đã lưu: {output_path}")
        plt.close()
    
    def generate_all_visualizations(self):
        """Tạo tất cả visualizations"""
        print("\n🎨 Đang tạo visualizations...")
        print("="*60)
        
        self.create_summary_table()
        self.plot_category_distribution()
        self.plot_size_histogram()
        self.plot_scatter()
        self.plot_statistics()
        
        print("\n" + "="*60)
        print(f"✅ Đã tạo xong! Kiểm tra thư mục: {self.output_dir}")
        print("="*60)


def main():
    """Main function"""
    print("🚀 Data Visualization Pipeline")
    print("="*60)
    
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()


if __name__ == '__main__':
    main()
