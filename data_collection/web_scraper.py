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
    SCRAPER_RATE_LIMIT = 0.5
    SCRAPER_MAX_IMAGES_PER_KEYWORD = 200
    SCRAPER_TIMEOUT = 15
    SCRAPER_SKIP_ON_ERROR = True
    DATABASE_BATCH_SIZE = 100


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
        """
        Crawl images from Bing and Google with error handling
        
        Args:
            keywords: List of search keywords
            max_num: Maximum images per keyword
        """
        temp_dir = "temp_crawl"
        os.makedirs(temp_dir, exist_ok=True)
        
        logger.section(f"Starting Web Scraping Campaign")
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Max images per keyword: {max_num}")
        logger.info(f"Rate limit: {SCRAPER_RATE_LIMIT}s between requests")

        batch_buffer = []  # Buffer for batch uploads
        
        for idx, kw in enumerate(keywords, 1):
            logger.info(f"\n[{idx}/{len(keywords)}] Crawling keyword: '{kw}'")
            
            try:
                # Crawl from Bing
                self._crawl_bing(kw, max_num, temp_dir)
                
                # Crawl from Google (reduced to avoid bans)
                self._crawl_google(kw, int(max_num * 0.6), temp_dir)
                
                # Process downloaded images
                batch_buffer = self._process_temp_images(temp_dir, kw, batch_buffer)
                
                # Rate limiting
                time.sleep(SCRAPER_RATE_LIMIT)
                
            except KeyboardInterrupt:
                logger.warning("⚠️  Scraping interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error crawling '{kw}': {e}")
                if not SCRAPER_SKIP_ON_ERROR:
                    raise
                self.stats['total_errors'] += 1
        
        # Upload remaining batch
        if batch_buffer:
            self._upload_batch(batch_buffer)
        
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
        
        # Final report
        self._print_summary()

    def _crawl_bing(self, keyword, max_num, temp_dir):
        """Crawl from Bing with error handling"""
        try:
            logger.info(f"  → Bing: crawling...")
            bing = BingImageCrawler(storage={'root_dir': temp_dir})
            bing.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info(f"  ✓ Bing: completed")
        except Exception as e:
            logger.warning(f"  ✗ Bing failed: {e}")
            if not SCRAPER_SKIP_ON_ERROR:
                raise

    def _crawl_google(self, keyword, max_num, temp_dir):
        """Crawl from Google with error handling"""
        try:
            logger.info(f"  → Google: crawling...")
            google = GoogleImageCrawler(storage={'root_dir': temp_dir})
            google.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info(f"  ✓ Google: completed")
        except Exception as e:
            logger.warning(f"  ✗ Google failed: {e}")
            if not SCRAPER_SKIP_ON_ERROR:
                raise

    def _process_temp_images(self, temp_dir, keyword, batch_buffer):
        """Process downloaded images and prepare for batch upload"""
        processed = 0
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            try:
                # Read file
                with open(filepath, "rb") as f:
                    data = f.read()
                
                # Skip small files (likely errors or placeholders)
                if len(data) < 5120:  # < 5KB
                    self.stats['total_skipped'] += 1
                    os.remove(filepath)
                    continue
                
                # Generate unique name
                ext = os.path.splitext(filename)[1] or '.jpg'
                hash_name = hashlib.md5(f"{keyword}_{filename}".encode()).hexdigest()[:10]
                new_name = f"crawl_{hash_name}{ext}"
                
                # Add to batch buffer
                batch_buffer.append((new_name, data))
                processed += 1
                self.stats['total_crawled'] += 1
                
                # Upload batch if buffer is full
                if len(batch_buffer) >= DATABASE_BATCH_SIZE:
                    self._upload_batch(batch_buffer)
                    batch_buffer = []
                
            except Exception as e:
                logger.debug(f"Error processing {filename}: {e}")
                self.stats['total_errors'] += 1
            finally:
                # Always cleanup temp file
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
        
        if processed > 0:
            logger.info(f"  ✓ Processed: {processed} images")
        
        return batch_buffer

    def _upload_batch(self, batch):
        """Upload batch of images to MinIO"""
        if not self.minio or not batch:
            return
        
        logger.info(f"  → Uploading batch of {len(batch)} images...")
        
        try:
            results = self.minio.upload_images_batch(batch)
            success_count = sum(1 for v in results.values() if v)
            self.stats['total_uploaded'] += success_count
            
            if success_count < len(batch):
                failed = len(batch) - success_count
                logger.warning(f"  ⚠️  {failed} uploads failed in batch")
            else:
                logger.info(f"  ✓ Batch uploaded successfully")
                
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            self.stats['total_errors'] += len(batch)

    def _print_summary(self):
        """Print final statistics"""
        logger.section("Scraping Campaign Summary")
        logger.info(f"Total crawled:  {self.stats['total_crawled']}")
        logger.info(f"Total uploaded: {self.stats['total_uploaded']}")
        logger.info(f"Total skipped:  {self.stats['total_skipped']}")
        logger.info(f"Total errors:   {self.stats['total_errors']}")
        
        if self.stats['total_crawled'] > 0:
            success_rate = (self.stats['total_uploaded'] / self.stats['total_crawled']) * 100
            logger.info(f"Success rate:   {success_rate:.1f}%")
