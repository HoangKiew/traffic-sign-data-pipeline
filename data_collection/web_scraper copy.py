"""
High Volume Web Scraper for Traffic Signs (Working 2026 - Bing + Google fallback)
- Giữ nguyên icrawler gốc để crawl được
- Thay emoji bằng text để tránh UnicodeEncodeError trên Windows
- Tăng rate limit nhẹ để giảm block
- XÓA SẠCH temp_dir trước mỗi từ khóa để tránh lỗi icrawler không lưu file mới
- Comment Google nếu fail nhiều
"""

import os
import shutil
import hashlib
import time
from icrawler.builtin import BingImageCrawler, GoogleImageCrawler
from utils.database import MinIOClient

try:
    from utils.logger import get_logger
    from config.optimization_config import (
        SCRAPER_RATE_LIMIT, SCRAPER_MAX_IMAGES_PER_KEYWORD,
        SCRAPER_TIMEOUT, SCRAPER_SKIP_ON_ERROR, DATABASE_BATCH_SIZE
    )
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    SCRAPER_RATE_LIMIT = 2.0          # Tăng từ 0.5 lên 2s để an toàn hơn
    SCRAPER_MAX_IMAGES_PER_KEYWORD = 150  # Giảm nhẹ để tránh block nhanh
    SCRAPER_TIMEOUT = 15
    SCRAPER_SKIP_ON_ERROR = True
    DATABASE_BATCH_SIZE = 20  # Giảm batch size để tránh quá tải MinIO

class HighVolumeScraper:
    """Optimized scraper with error handling and batch uploads"""
    
    def __init__(self, save_to_minio=True):
        self.save_to_minio = save_to_minio
        self.minio = MinIOClient() if save_to_minio else None
        self.stats = {
            'total_crawled': 0,
            'total_uploaded': 0,
            'total_skipped': 0,
            'total_errors': 0
        }

    def crawl(self, keywords, max_num=SCRAPER_MAX_IMAGES_PER_KEYWORD):
        temp_dir = "temp_crawl"
        os.makedirs(temp_dir, exist_ok=True)
        
        logger.section("Starting Web Scraping Campaign")
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Max images per keyword: {max_num}")
        logger.info(f"Rate limit: {SCRAPER_RATE_LIMIT}s between requests")

        batch_buffer = []
        
        for idx, kw in enumerate(keywords, 1):
            logger.info(f"[{idx}/{len(keywords)}] Crawling keyword: '{kw}'")
            
            try:
                # XÓA SẠCH temp_dir TRƯỚC MỖI TỪ KHÓA ĐỂ ĐẢM BẢO ẢNH MỚI ĐƯỢC LƯU
                for f in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, f))
                    except Exception:
                        pass

                # Crawl from Bing (ưu tiên)
                self._crawl_bing(kw, max_num, temp_dir)
                
                # Crawl from Google (giảm số lượng, comment nếu fail nhiều)
                # self._crawl_google(kw, int(max_num * 0.5), temp_dir)  # <-- Comment nếu Google fail
                
                batch_buffer = self._process_temp_images(temp_dir, kw, batch_buffer)
                
                time.sleep(SCRAPER_RATE_LIMIT)
                
            except KeyboardInterrupt:
                logger.warning("Scraping interrupted by user (Ctrl+C)")
                break
            except Exception as e:
                logger.error(f"Error crawling '{kw}': {str(e)}")
                if not SCRAPER_SKIP_ON_ERROR:
                    raise
                self.stats['total_errors'] += 1
        
        if batch_buffer:
            self._upload_batch(batch_buffer)
        
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
        
        self._print_summary()

    def _crawl_bing(self, keyword, max_num, temp_dir):
        try:
            logger.info("  -> Bing: crawling...")
            bing = BingImageCrawler(storage={'root_dir': temp_dir})
            bing.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info("  [OK] Bing: completed")
        except Exception as e:
            logger.warning(f"  [Fail] Bing: {str(e)}")

    def _crawl_google(self, keyword, max_num, temp_dir):
        try:
            logger.info("  -> Google: crawling...")
            google = GoogleImageCrawler(storage={'root_dir': temp_dir})
            google.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info("  [OK] Google: completed")
        except Exception as e:
            logger.warning(f"  [Fail] Google: {str(e)}")

    def _process_temp_images(self, temp_dir, keyword, batch_buffer):
        processed = 0
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                
                if len(data) < 5120:
                    self.stats['total_skipped'] += 1
                    os.remove(filepath)
                    continue
                
                ext = os.path.splitext(filename)[1] or '.jpg'
                hash_name = hashlib.md5(f"{keyword}_{filename}".encode()).hexdigest()[:10]
                new_name = f"crawl_{hash_name}{ext}"
                
                batch_buffer.append((new_name, data))
                processed += 1
                self.stats['total_crawled'] += 1
                
                if len(batch_buffer) >= DATABASE_BATCH_SIZE:
                    self._upload_batch(batch_buffer)
                    batch_buffer = []
                    time.sleep(2)  # Nghỉ 2s sau mỗi batch upload để giảm tải MinIO
                
            except Exception as e:
                logger.debug(f"Error processing {filename}: {e}")
                self.stats['total_errors'] += 1
            finally:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
        
        if processed > 0:
            logger.info(f"  [OK] Processed: {processed} images")
        
        return batch_buffer

    def _upload_batch(self, batch):
        if not self.minio or not batch:
            return
        logger.info(f"  -> Uploading batch of {len(batch)} images...")
        try:
            results = self.minio.upload_images_batch(batch)
            success_count = sum(1 for v in results.values() if v)
            self.stats['total_uploaded'] += success_count
            if success_count < len(batch):
                failed = len(batch) - success_count
                logger.warning(f"  [Warn] {failed} uploads failed in batch")
            else:
                logger.info("  [OK] Batch uploaded successfully")
            time.sleep(2)  # Nghỉ 2s sau mỗi batch upload để giảm tải MinIO
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            self.stats['total_errors'] += len(batch)

    def _print_summary(self):
        logger.section("Scraping Campaign Summary")
        logger.info(f"Total crawled:  {self.stats['total_crawled']}")
        logger.info(f"Total uploaded: {self.stats['total_uploaded']}")
        logger.info(f"Total skipped:  {self.stats['total_skipped']}")
        logger.info(f"Total errors:   {self.stats['total_errors']}")
        
        if self.stats['total_crawled'] > 0:
            success_rate = (self.stats['total_uploaded'] / self.stats['total_crawled']) * 100
            logger.info(f"Success rate:   {success_rate:.1f}%")