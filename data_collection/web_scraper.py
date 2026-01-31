import sys
import os
import shutil
import hashlib
import time
import logging
import types
import threading

# ────────────────────────────────────────────────────────────────
#                     FIX ICRAWLER THREAD ERRORS (2026)
# ────────────────────────────────────────────────────────────────

class DummyFile:
    def write(self, x): pass
    def flush(self): pass

# Redirect stderr sớm nhất có thể (ẩn lỗi từ import icrawler)
original_stderr = sys.stderr
sys.stderr = DummyFile()

from icrawler.builtin import BingImageCrawler, GoogleImageCrawler

# Khôi phục stderr sau import (nếu cần log khác)
sys.stderr = original_stderr

# Tắt logging icrawler triệt để
logging.getLogger("icrawler").setLevel(logging.WARNING)
logging.getLogger("icrawler.parser").setLevel(logging.WARNING)
logging.getLogger("icrawler.downloader").setLevel(logging.WARNING)
logging.getLogger("icrawler.feeder").setLevel(logging.WARNING)
logging.getLogger("icrawler.crawler").setLevel(logging.WARNING)

# Monkey-patch Parser.worker_exec đúng cách
import icrawler.parser

def safe_worker_exec(self, response, **kwargs):
    try:
        result = self.parse(response, **kwargs)
        if result is None:
            return
        for task in result:
            if task is not None:
                self.output_queue.put(task)
    except TypeError as te:
        msg = str(te).lower()
        if any(phrase in msg for phrase in [
            "nonetype object is not iterable",
            "not subscriptable",
            "missing",
            "positional argument",
            "response"
        ]):
            return  # im lặng
        raise
    except Exception:
        # Các lỗi khác (timeout, connection...) vẫn để mặc định hoặc log nếu cần
        pass


# Gán lại method chuẩn (giữ bound method)
icrawler.parser.Parser.worker_exec = types.MethodType(
    safe_worker_exec,
    icrawler.parser.Parser
)

# Hook excepthook để ẩn traceback thread của icrawler
def icrawler_silent_excepthook(args):
    if args.exc_type is TypeError:
        msg = str(args.exc_value).lower()
        if any(p in msg for p in ["nonetype", "not iterable", "missing", "positional argument", "response"]):
            return  # không in gì cả
    # Các lỗi khác vẫn in (hoặc comment dòng dưới nếu muốn tắt hết)
    sys.__excepthook__(args)

threading.excepthook = icrawler_silent_excepthook

# ────────────────────────────────────────────────────────────────
#                             CODE CHÍNH
# ────────────────────────────────────────────────────────────────

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
    SCRAPER_RATE_LIMIT = 1.2          # tăng nhẹ để giảm lỗi Google
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
        self.interrupted = False

    def crawl(self, keywords, max_num=SCRAPER_MAX_IMAGES_PER_KEYWORD):
        temp_dir = "temp_crawl"
        os.makedirs(temp_dir, exist_ok=True)
        
        logger.section("Starting Web Scraping Campaign")
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Max images per keyword: {max_num}")
        logger.info(f"Rate limit: {SCRAPER_RATE_LIMIT}s")

        batch_buffer = []
        
        try:
            for idx, kw in enumerate(keywords, 1):
                if self.interrupted:
                    logger.warning("Scraping interrupted by user (Ctrl+C).")
                    break

                logger.info(f"\n[{idx}/{len(keywords)}] Crawling keyword: '{kw}'")
                
                try:
                    self._crawl_bing(kw, max_num, temp_dir)
                    
                    # Google: giảm số lượng + rate limit cao hơn → giảm ban & lỗi parser
                    self._crawl_google(kw, int(max_num * 0.5), temp_dir)
                    
                    batch_buffer = self._process_temp_images(temp_dir, kw, batch_buffer)
                    
                    time.sleep(SCRAPER_RATE_LIMIT)
                    
                except KeyboardInterrupt:
                    logger.warning("Interrupted by user (Ctrl+C).")
                    self.interrupted = True
                    break
                except Exception as e:
                    logger.error(f"Error crawling '{kw}': {str(e)[:200]}")
                    if not SCRAPER_SKIP_ON_ERROR:
                        raise
                    self.stats['total_errors'] += 1
        except KeyboardInterrupt:
            logger.warning("Interrupted (outer).")
            self.interrupted = True

        if batch_buffer and not self.interrupted:
            self._upload_batch(batch_buffer)
        
        try:
            shutil.rmtree(temp_dir)
        except:
            logger.warning("Cleanup temp dir failed")

        self._print_summary()

    def _crawl_bing(self, keyword, max_num, temp_dir):
        try:
            logger.info("  → Bing: crawling...")
            crawler = BingImageCrawler(storage={'root_dir': temp_dir})
            crawler.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info("  ✓ Bing: completed")
        except Exception as e:
            logger.warning(f"  ✗ Bing failed: {str(e)[:150]}")

    def _crawl_google(self, keyword, max_num, temp_dir):
        try:
            logger.info("  → Google: crawling...")
            crawler = GoogleImageCrawler(storage={'root_dir': temp_dir})
            crawler.crawl(keyword=keyword, max_num=max_num, overwrite=True)
            logger.info("  ✓ Google: completed")
        except Exception as e:
            logger.warning(f"  ✗ Google failed: {str(e)[:150]}")

    def _process_temp_images(self, temp_dir, keyword, batch_buffer):
        processed = 0
        
        for filename in list(os.listdir(temp_dir)):
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
                    
            except Exception as e:
                logger.debug(f"Process error {filename}: {e}")
                self.stats['total_errors'] += 1
            finally:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
        
        if processed > 0:
            logger.info(f"  ✓ Processed: {processed} images")
        
        return batch_buffer

    def _upload_batch(self, batch):
        if not self.minio or not batch:
            return
        
        logger.info(f"  → Uploading batch ({len(batch)} imgs)...")
        
        try:
            results = self.minio.upload_images_batch(batch)
            success = sum(1 for v in results.values() if v)
            self.stats['total_uploaded'] += success
            
            if success < len(batch):
                logger.warning(f"  ⚠️ {len(batch)-success} failed in batch")
            else:
                logger.info("  ✓ Batch uploaded OK")
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            self.stats['total_errors'] += len(batch)

    def _print_summary(self):
        logger.section("Scraping Campaign Summary")
        logger.info(f"Total crawled : {self.stats['total_crawled']}")
        logger.info(f"Total uploaded : {self.stats['total_uploaded']}")
        logger.info(f"Total skipped  : {self.stats['total_skipped']}")
        logger.info(f"Total errors   : {self.stats['total_errors']}")
        
        if self.stats['total_crawled'] > 0:
            rate = (self.stats['total_uploaded'] / self.stats['total_crawled']) * 100
            logger.info(f"Success rate   : {rate:.1f}%")