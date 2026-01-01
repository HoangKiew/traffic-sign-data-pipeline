import pandas as pd
import matplotlib.pyplot as plt

# Đọc file metadata.csv
metadata = pd.read_csv('data/metadata.csv')

# Đếm số lượng mỗi category
category_counts = metadata['category'].value_counts()

# Vẽ bar chart
plt.figure(figsize=(8, 6))
category_counts.plot(kind='bar', color='skyblue')
plt.title('Phân bố Category')
plt.xlabel('Category')
plt.ylabel('Số lượng')
plt.xticks(rotation=15)
plt.tight_layout()
plt.show()
