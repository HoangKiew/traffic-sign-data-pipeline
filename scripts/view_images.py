"""
Script để xem và download ảnh đã xử lý từ MinIO
"""
import os
from utils.database import MinIOClient
from PIL import Image
import io

def view_processed_images(num_images=10, download=False, output_dir="sample_images"):
    """
    Xem và download ảnh đã xử lý từ MinIO
    
    Args:
        num_images: Số lượng ảnh muốn xem
        download: True để download về local
        output_dir: Thư mục lưu ảnh
    """
    print("🔍 Đang kết nối MinIO...")
    minio = MinIOClient()
    
    # Lấy danh sách ảnh processed
    bucket = "traffic-signs-processed"
    print(f"📦 Đang lấy danh sách ảnh từ bucket '{bucket}'...")
    
    images = minio.list_images(bucket=bucket)
    
    if not images:
        print("❌ Không tìm thấy ảnh processed trong MinIO!")
        print("💡 Hãy chạy 'python main.py' để tạo ảnh processed")
        return
    
    print(f"✅ Tìm thấy {len(images)} ảnh processed")
    print(f"📸 Đang xem {min(num_images, len(images))} ảnh đầu tiên...\n")
    
    if download:
        os.makedirs(output_dir, exist_ok=True)
        print(f"💾 Sẽ download vào thư mục: {output_dir}/\n")
    
    for i, img_name in enumerate(images[:num_images]):
        print(f"[{i+1}/{min(num_images, len(images))}] {img_name}")
        
        try:
            # Download ảnh từ MinIO
            img_data = minio.download_image(img_name, bucket=bucket)
            
            if img_data:
                # Hiển thị thông tin
                size_kb = len(img_data) / 1024
                print(f"  ✓ Kích thước: {size_kb:.1f} KB")
                
                # Mở ảnh để xem thông tin
                img = Image.open(io.BytesIO(img_data))
                print(f"  ✓ Độ phân giải: {img.size[0]}x{img.size[1]}")
                print(f"  ✓ Format: {img.format}")
                
                # Download nếu cần
                if download:
                    save_path = os.path.join(output_dir, img_name)
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                    print(f"  ✓ Đã lưu: {save_path}")
                
                print()
            else:
                print(f"  ✗ Lỗi: Không download được\n")
                
        except Exception as e:
            print(f"  ✗ Lỗi: {e}\n")
    
    print("="*60)
    print(f"✅ Hoàn thành! Đã xem {min(num_images, len(images))} ảnh")
    if download:
        print(f"💾 Ảnh đã được lưu tại: {output_dir}/")
    print("="*60)


def list_all_buckets():
    """Liệt kê tất cả buckets trong MinIO"""
    print("🔍 Đang kết nối MinIO...")
    minio = MinIOClient()
    
    print("\n📦 Danh sách buckets:")
    buckets = minio.client.list_buckets()
    
    for bucket in buckets:
        print(f"\n  • {bucket.name}")
        
        # Đếm số file trong bucket
        try:
            objects = list(minio.client.list_objects(bucket.name))
            total_size = sum(obj.size for obj in objects)
            print(f"    - Số files: {len(objects)}")
            print(f"    - Tổng dung lượng: {total_size / 1024 / 1024:.1f} MB")
        except Exception as e:
            print(f"    - Lỗi: {e}")
    
    print()


def download_specific_image(image_name, bucket="traffic-signs-processed", output_dir="downloads"):
    """
    Download 1 ảnh cụ thể từ MinIO
    
    Args:
        image_name: Tên file ảnh
        bucket: Tên bucket
        output_dir: Thư mục lưu
    """
    print(f"🔍 Đang download '{image_name}' từ bucket '{bucket}'...")
    
    minio = MinIOClient()
    img_data = minio.download_image(image_name, bucket=bucket)
    
    if img_data:
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, image_name)
        
        with open(save_path, 'wb') as f:
            f.write(img_data)
        
        print(f"✅ Đã lưu: {save_path}")
        print(f"📊 Kích thước: {len(img_data) / 1024:.1f} KB")
    else:
        print("❌ Không tìm thấy ảnh!")


def open_minio_console():
    """Hướng dẫn mở MinIO Console"""
    print("="*60)
    print("🌐 CÁCH XEM ẢNH TRÊN MINIO CONSOLE")
    print("="*60)
    print("\n1. Mở trình duyệt và truy cập:")
    print("   👉 http://localhost:9001")
    print("\n2. Đăng nhập:")
    print("   Username: minioadmin")
    print("   Password: minioadmin")
    print("\n3. Chọn bucket:")
    print("   • traffic-signs-raw (ảnh gốc)")
    print("   • traffic-signs-processed (ảnh đã xử lý)")
    print("\n4. Click vào ảnh để xem preview")
    print("   • Có thể download từng ảnh")
    print("   • Có thể xem thông tin chi tiết")
    print("\n" + "="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Xem ảnh từ MinIO")
    parser.add_argument("--list-buckets", action="store_true", help="Liệt kê tất cả buckets")
    parser.add_argument("--view", type=int, default=10, help="Số lượng ảnh muốn xem (default: 10)")
    parser.add_argument("--download", action="store_true", help="Download ảnh về local")
    parser.add_argument("--output", default="sample_images", help="Thư mục lưu ảnh (default: sample_images)")
    parser.add_argument("--bucket", default="traffic-signs-processed", help="Bucket name (default: traffic-signs-processed)")
    parser.add_argument("--image", help="Tên ảnh cụ thể muốn download")
    parser.add_argument("--console", action="store_true", help="Hướng dẫn mở MinIO Console")
    
    args = parser.parse_args()
    
    if args.console:
        open_minio_console()
    elif args.list_buckets:
        list_all_buckets()
    elif args.image:
        download_specific_image(args.image, bucket=args.bucket, output_dir=args.output)
    else:
        view_processed_images(num_images=args.view, download=args.download, output_dir=args.output)
