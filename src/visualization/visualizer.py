import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False
    print("pymongo chưa cài đặt. Chạy: pip install pymongo để visualize từ MongoDB")

# Luon dung config, khong fallback hard-code URI
from config import CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME


class DataVisualizer:
    # Visualize traffic sign dataset
    
    def __init__(self, metadata_path='data/metadata.csv'):
        self.output_dir = Path('reports/figures')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 6)

        # Luon doc metadata tu MongoDB (khong dung CSV nua)
        print("Đọc metadata từ MongoDB...")
        self.df = self._load_from_mongodb()
        
        if self.df is None or self.df.empty:
            raise ValueError("Không có metadata để vẽ biểu đồ (MongoDB rỗng).")

    def _load_from_mongodb(self) -> pd.DataFrame:
        """Đọc metadata (không gồm bytes ảnh) từ MongoDB và trả về DataFrame."""
        if not HAS_MONGO:
            print("Không thể đọc metadata từ MongoDB vì chưa cài pymongo.")
            return pd.DataFrame()
        client = MongoClient(CONNECTION_STRING)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        # Bỏ field image (rất nặng)
        cursor = collection.find({}, {"image": 0})
        docs = list(cursor)
        client.close()
        if not docs:
            print("MongoDB không có document nào trong collection metadata.")
            return pd.DataFrame()
        for d in docs:
            d.pop('_id', None)
        df = pd.DataFrame(docs)
        print(f"Đã load {len(df)} bản ghi metadata từ MongoDB ({DATABASE_NAME}.{COLLECTION_NAME})")
        return df
    
    def create_summary_table(self):
        """
        Tạo bảng mô tả dữ liệu theo slide:
        - Thống kê tổng quan
        """
        print("\n" + "="*60)
        print(" BẢNG MÔ TẢ DỮ LIỆU")
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
        Bar chart: Phan bo so luong theo category
        Theo slide: "Biểu đồ bar chart"
        """
        plt.figure(figsize=(10, 6))
        
        category_counts = self.df['category'].value_counts()
        
        ax = category_counts.plot(kind='bar', color='steelblue', edgecolor='black')
        plt.title('Phan bo so luong anh theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Số lượng ảnh', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Thêm số liệu trên mỗi cột
        for i, v in enumerate(category_counts):
            ax.text(i, v + 5, str(v), ha='center', fontweight='bold')
        
        plt.tight_layout()
        output_path = self.output_dir / 'phan_bo_category.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_size_histogram(self):
        """
        Histogram: Phân bố kích thước ảnh
        Theo slide: "Biểu đồ histogram"
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Width histogram
        axes[0].hist(self.df['width'], bins=30, color='skyblue', edgecolor='black')
        axes[0].set_title('Phan bo Width', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Width (pixels)', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].axvline(self.df['width'].mean(), color='red', linestyle='--', 
                       label=f'Mean: {self.df["width"].mean():.1f}')
        axes[0].legend()
        
        # Height histogram
        axes[1].hist(self.df['height'], bins=30, color='lightcoral', edgecolor='black')
        axes[1].set_title('Phan bo Height', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Height (pixels)', fontsize=11)
        axes[1].set_ylabel('Frequency', fontsize=11)
        axes[1].axvline(self.df['height'].mean(), color='red', linestyle='--',
                       label=f'Mean: {self.df["height"].mean():.1f}')
        axes[1].legend()
        
        plt.tight_layout()
        output_path = self.output_dir / 'histogram_kich_thuoc.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
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
        
        plt.title('Bieu do: Width vs Height', fontsize=16, fontweight='bold')
        plt.xlabel('Width (pixels)', fontsize=12)
        plt.ylabel('Height (pixels)', fontsize=12)
        plt.legend(title='Category')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'bieu_do_width_height.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_statistics(self):
        """
        Tạo 3 biểu đồ thống kê riêng biệt
        """
        # 1. Box plots cho Width và Height
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        axes[0].boxplot([self.df['width']], tick_labels=['Width'])
        axes[0].set_title('Box Plot - Width', fontweight='bold')
        axes[0].set_ylabel('Pixels')
        axes[0].grid(True, alpha=0.3)
        
        axes[1].boxplot([self.df['height']], tick_labels=['Height'])
        axes[1].set_title('Box Plot - Height', fontweight='bold')
        axes[1].set_ylabel('Pixels')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'box_plot_width_height.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
        
        # 2. Mean, Median, Std comparison
        stats_df = pd.DataFrame({
            'Width': [self.df['width'].mean(), self.df['width'].median(), self.df['width'].std()],
            'Height': [self.df['height'].mean(), self.df['height'].median(), self.df['height'].std()]
        }, index=['Mean', 'Median', 'Std'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = range(len(stats_df))
        width = 0.35
        ax.bar([i - width/2 for i in x], stats_df['Width'], width, label='Width', color='skyblue')
        ax.bar([i + width/2 for i in x], stats_df['Height'], width, label='Height', color='lightcoral')
        ax.set_title('Thong ke: Mean, Median, Std', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(stats_df.index)
        ax.set_ylabel('Pixels')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'thong_ke_mean_median_std.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
        
        # 3. File size distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(self.df['size_kb'], bins=30, color='mediumseagreen', edgecolor='black')
        ax.set_title('Phan bo kich thuoc file', fontweight='bold', fontsize=14)
        ax.set_xlabel('Size (KB)')
        ax.set_ylabel('Frequency')
        ax.axvline(self.df['size_kb'].mean(), color='red', linestyle='--',
                   label=f"Mean: {self.df['size_kb'].mean():.1f} KB")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'phan_bo_file_size.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()

    
    def plot_file_size_by_category(self):
        """Kích thước file theo category"""
        plt.figure(figsize=(12, 6))
        
        categories = self.df['category'].unique()
        data_to_plot = [self.df[self.df['category'] == cat]['size_kb'].values 
                        for cat in categories]
        
        bp = plt.boxplot(data_to_plot, labels=categories, patch_artist=True)
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        for patch, color in zip(bp['boxes'], colors[:len(categories)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        plt.title('Phân bố Kích thước File theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Kích thước File (KB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = self.output_dir / 'file_size_by_category.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_aspect_ratio_distribution(self):
        """Phân bố Aspect Ratio (tỷ lệ khung hình)"""
        # Tính aspect ratio
        self.df['aspect_ratio'] = self.df['width'] / self.df['height']
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram aspect ratio
        axes[0].hist(self.df['aspect_ratio'], bins=30, color='purple', edgecolor='black', alpha=0.7)
        axes[0].axvline(1.0, color='red', linestyle='--', linewidth=2, label='Vuông (1:1)')
        axes[0].axvline(16/9, color='orange', linestyle='--', linewidth=2, label='Ngang (16:9)')
        axes[0].axvline(9/16, color='green', linestyle='--', linewidth=2, label='Dọc (9:16)')
        axes[0].set_title('Phân bố Aspect Ratio', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Aspect Ratio (Width/Height)', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Aspect ratio theo category
        categories = self.df['category'].unique()
        data_to_plot = [self.df[self.df['category'] == cat]['aspect_ratio'].values 
                        for cat in categories]
        
        bp = axes[1].boxplot(data_to_plot, labels=categories, patch_artist=True)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        for patch, color in zip(bp['boxes'], colors[:len(categories)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        axes[1].axhline(1.0, color='red', linestyle='--', linewidth=2, alpha=0.5)
        axes[1].set_title('Aspect Ratio theo Category', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Category', fontsize=11)
        axes[1].set_ylabel('Aspect Ratio', fontsize=11)
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = self.output_dir / 'aspect_ratio_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_category_comparison(self):
        """So sánh các metrics theo category"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        categories = self.df['category'].unique()
        x = range(len(categories))
        width = 0.35
        
        # 1. Mean Width & Height theo category
        mean_width = [self.df[self.df['category'] == cat]['width'].mean() for cat in categories]
        mean_height = [self.df[self.df['category'] == cat]['height'].mean() for cat in categories]
        
        axes[0, 0].bar([i - width/2 for i in x], mean_width, width, label='Width', color='skyblue')
        axes[0, 0].bar([i + width/2 for i in x], mean_height, width, label='Height', color='lightcoral')
        axes[0, 0].set_title('Kích thước Trung bình theo Category', fontweight='bold')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(categories, rotation=45, ha='right')
        axes[0, 0].set_ylabel('Pixels')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # 2. Mean File Size theo category
        mean_size = [self.df[self.df['category'] == cat]['size_kb'].mean() for cat in categories]
        axes[0, 1].bar(categories, mean_size, color='mediumseagreen', alpha=0.7)
        axes[0, 1].set_title('Kích thước File Trung bình theo Category', fontweight='bold')
        axes[0, 1].set_ylabel('Size (KB)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # 3. Số lượng ảnh vs Kích thước TB
        counts = [len(self.df[self.df['category'] == cat]) for cat in categories]
        axes[1, 0].scatter(counts, mean_size, s=200, alpha=0.6, c=range(len(categories)), 
                          cmap='viridis')
        for i, cat in enumerate(categories):
            axes[1, 0].annotate(cat, (counts[i], mean_size[i]), 
                               fontsize=9, ha='center')
        axes[1, 0].set_title('Số lượng vs Kích thước File', fontweight='bold')
        axes[1, 0].set_xlabel('Số lượng ảnh')
        axes[1, 0].set_ylabel('Kích thước TB (KB)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Heatmap correlation
        numeric_cols = ['width', 'height', 'size_kb']
        if 'aspect_ratio' in self.df.columns:
            numeric_cols.append('aspect_ratio')
        
        corr_data = self.df[numeric_cols].corr()
        im = axes[1, 1].imshow(corr_data, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        axes[1, 1].set_xticks(range(len(corr_data.columns)))
        axes[1, 1].set_yticks(range(len(corr_data.columns)))
        axes[1, 1].set_xticklabels(corr_data.columns, rotation=45, ha='right')
        axes[1, 1].set_yticklabels(corr_data.columns)
        
        # Thêm giá trị vào heatmap
        for i in range(len(corr_data.columns)):
            for j in range(len(corr_data.columns)):
                text = axes[1, 1].text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                                     ha="center", va="center", color="black", fontweight='bold')
        
        axes[1, 1].set_title('Correlation Matrix', fontweight='bold')
        plt.colorbar(im, ax=axes[1, 1])
        
        plt.tight_layout()
        output_path = self.output_dir / 'category_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_category_pie_chart(self):
        """Pie chart phân bố số lượng theo category"""
        plt.figure(figsize=(10, 8))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        counts = [len(self.df[self.df['category'] == cat]) for cat in categories]
        
        plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90,
                colors=colors[:len(categories)], textprops={'fontsize': 12, 'fontweight': 'bold'})
        plt.title('Phân bố Số lượng theo Category', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        output_path = self.output_dir / 'category_pie_chart.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_average_area_by_category(self):
        """Bar chart diện tích trung bình theo category"""
        plt.figure(figsize=(10, 6))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        mean_area = [self.df[self.df['category'] == cat]['width'].mean() * 
                    self.df[self.df['category'] == cat]['height'].mean() 
                    for cat in categories]
        
        bars = plt.bar(categories, mean_area, color=colors[:len(categories)], alpha=0.7, edgecolor='black')
        plt.title('Diện tích Trung bình theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Diện tích (px²)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Thêm giá trị trên mỗi cột
        for bar, value in zip(bars, mean_area):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{value:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        output_path = self.output_dir / 'average_area_by_category.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_average_file_size_by_category(self):
        """Bar chart kích thước file trung bình theo category"""
        plt.figure(figsize=(10, 6))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        mean_size = [self.df[self.df['category'] == cat]['size_kb'].mean() for cat in categories]
        
        bars = plt.bar(categories, mean_size, color=colors[:len(categories)], alpha=0.7, edgecolor='black')
        plt.title('Kích thước File Trung bình theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Kích thước File (KB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Thêm giá trị trên mỗi cột
        for bar, value in zip(bars, mean_size):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{value:.1f}KB', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        output_path = self.output_dir / 'average_file_size_by_category.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_width_distribution_violin(self):
        """Violin plot phân bố width theo category"""
        plt.figure(figsize=(12, 6))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        data_to_plot = [self.df[self.df['category'] == cat]['width'].values 
                        for cat in categories]
        
        parts = plt.violinplot(data_to_plot, positions=range(len(categories)), 
                              showmeans=True, showmedians=True)
        
        # Tô màu cho violin plots
        for pc, color in zip(parts['bodies'], colors[:len(categories)]):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
        
        plt.xticks(range(len(categories)), categories, rotation=45, ha='right')
        plt.title('Phân bố Width theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Width (px)', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = self.output_dir / 'width_distribution_violin.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_height_distribution_violin(self):
        """Violin plot phân bố height theo category"""
        plt.figure(figsize=(12, 6))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        data_to_plot = [self.df[self.df['category'] == cat]['height'].values 
                        for cat in categories]
        
        parts = plt.violinplot(data_to_plot, positions=range(len(categories)), 
                              showmeans=True, showmedians=True)
        
        # Tô màu cho violin plots
        for pc, color in zip(parts['bodies'], colors[:len(categories)]):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
        
        plt.xticks(range(len(categories)), categories, rotation=45, ha='right')
        plt.title('Phân bố Height theo Category', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Height (px)', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = self.output_dir / 'height_distribution_violin.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_area_vs_file_size_scatter(self):
        """Scatter plot diện tích vs kích thước file"""
        plt.figure(figsize=(12, 8))
        
        categories = self.df['category'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        for i, cat in enumerate(categories):
            cat_data = self.df[self.df['category'] == cat]
            area = cat_data['width'] * cat_data['height']
            plt.scatter(area, cat_data['size_kb'], label=cat, 
                       alpha=0.6, s=80, color=colors[i], edgecolors='black', linewidth=0.5)
        
        plt.title('Diện tích vs Kích thước File', fontsize=16, fontweight='bold')
        plt.xlabel('Diện tích (px²)', fontsize=12)
        plt.ylabel('Kích thước File (KB)', fontsize=12)
        plt.legend(title='Category', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.xscale('log')  # Log scale để dễ nhìn hơn
        
        plt.tight_layout()
        output_path = self.output_dir / 'area_vs_file_size_scatter.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def plot_category_summary_table(self):
        """Bảng tóm tắt statistics theo category"""
        plt.figure(figsize=(10, 6))
        ax = plt.subplot(111)
        ax.axis('off')
        
        categories = self.df['category'].unique()
        summary_data = []
        for cat in categories:
            cat_df = self.df[self.df['category'] == cat]
            summary_data.append([
                cat,
                len(cat_df),
                f"{cat_df['width'].mean():.0f}",
                f"{cat_df['height'].mean():.0f}",
                f"{cat_df['size_kb'].mean():.1f}KB"
            ])
        
        columns = ['Category', 'Count', 'Mean W', 'Mean H', 'Mean Size']
        table = ax.table(cellText=summary_data, colLabels=columns,
                        cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # Tô màu header
        for i in range(len(columns)):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Tô màu xen kẽ các dòng
        colors = ['#F0F0F0', 'white']
        for i in range(1, len(summary_data) + 1):
            for j in range(len(columns)):
                table[(i, j)].set_facecolor(colors[i % 2])
        
        plt.title('Tóm tắt Statistics theo Category', fontsize=16, fontweight='bold', pad=20)
        
        output_path = self.output_dir / 'category_summary_table.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Da luu: {output_path}")
        plt.close()
    
    def generate_all_visualizations(self):
        """Tạo 4 biểu đồ cần thiết"""
        print("\nDang tao bieu do...")
        print("="*60)
        
        self.create_summary_table()
        
        # 4 biểu đồ cơ bản (theo yêu cầu slide)
        self.plot_category_distribution()  # 1. Bar chart
        self.plot_size_histogram()         # 2. Histogram
        self.plot_scatter()                # 3. Scatter plot
        self.plot_statistics()             # 4. Statistics summary
        
        print("\n" + "="*60)
        print(f"Da tao xong 4 bieu do. Thu muc: {self.output_dir}")
        print("="*60)


def main():
    """Main function"""
    print("Truc quan hoa du lieu")
    print("="*60)
    
    visualizer = DataVisualizer()
    visualizer.generate_all_visualizations()


if __name__ == '__main__':
    main()