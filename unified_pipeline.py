"""
Unified Pipeline Orchestrator
Manages the complete traffic sign data pipeline from crawling to final dataset
"""
import os
import sys
import signal
from pathlib import Path
from typing import Optional
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.database import MinIOClient, MongoDBClient
from config.optimization_config import CHECKPOINT_DIR, ENABLE_CHECKPOINTS, CHECKPOINT_INTERVAL

logger = get_logger()


class PipelineOrchestrator:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.checkpoint_dir = Path(CHECKPOINT_DIR)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "pipeline_state.json"
        self.interrupted = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.section("Pipeline Orchestrator Initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        logger.warning("\n⚠️  Interrupt signal received. Saving checkpoint...")
        self.interrupted = True
    
    def save_checkpoint(self, stage: str, data: dict):
        """Save pipeline checkpoint"""
        if not ENABLE_CHECKPOINTS:
            return
        
        checkpoint = {
            'stage': stage,
            'data': data
        }
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {stage}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[dict]:
        """Load pipeline checkpoint"""
        if not ENABLE_CHECKPOINTS or not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            logger.info(f"✅ Checkpoint loaded: {checkpoint['stage']}")
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def run_full_pipeline(self, skip_crawling: bool = False, skip_filtering: bool = False):
        """
        Run the complete pipeline
        
        Args:
            skip_crawling: Skip web scraping if True
            skip_filtering: Skip fast filtering if True
        """
        logger.section("STARTING FULL PIPELINE")
        
        try:
            # Stage 1: Web Scraping
            if not skip_crawling:
                self._run_web_scraping()
                if self.interrupted:
                    return
            
            # Stage 2: Fast Filtering
            if not skip_filtering:
                self._run_fast_filtering()
                if self.interrupted:
                    return
            
            # Stage 3: Data Cleaning & Preprocessing
            self._run_data_cleaning()
            if self.interrupted:
                return
            
            # Stage 4: Detection & Classification
            self._run_detection_classification()
            if self.interrupted:
                return
            
            # Stage 5: Labeling & Database Upload
            self._run_labeling()
            if self.interrupted:
                return
            
            # Stage 6: Dataset Splitting
            self._run_dataset_splitting()
            
            logger.section("✅ PIPELINE COMPLETED SUCCESSFULLY")
            
        except KeyboardInterrupt:
            logger.warning("Pipeline interrupted by user")
            self.save_checkpoint("interrupted", {})
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _run_web_scraping(self):
        """Stage 1: Web Scraping"""
        logger.section("Stage 1: Web Scraping")
        
        try:
            from data_collection.web_scraper import HighVolumeScraper
            from download_from_web import KEYWORDS
            
            scraper = HighVolumeScraper(save_to_minio=True)
            scraper.crawl(KEYWORDS, max_num=200)
            
            self.save_checkpoint("web_scraping_complete", {})
            
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            raise
    
    def _run_fast_filtering(self):
        """Stage 2: Fast Filtering"""
        logger.section("Stage 2: Fast Filtering")
        
        try:
            from fast_filter import FastFilter
            
            filter_tool = FastFilter()
            filter_tool.run()
            
            self.save_checkpoint("fast_filtering_complete", {})
            
        except Exception as e:
            logger.error(f"Fast filtering failed: {e}")
            raise
    
    def _run_data_cleaning(self):
        """Stage 3: Data Cleaning & Preprocessing"""
        logger.section("Stage 3: Data Cleaning & Preprocessing")
        
        try:
            from main import DataCleaningPipeline
            
            pipeline = DataCleaningPipeline()
            pipeline.run()
            
            self.save_checkpoint("data_cleaning_complete", {})
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            raise
    
    def _run_detection_classification(self):
        """Stage 4: Detection & Classification"""
        logger.section("Stage 4: Detection & Classification")
        
        try:
            from master_pipeline import run_master
            
            run_master()
            
            self.save_checkpoint("detection_complete", {})
            
        except Exception as e:
            logger.error(f"Detection & classification failed: {e}")
            raise
    
    def _run_labeling(self):
        """Stage 5: Labeling & Database Upload"""
        logger.section("Stage 5: Labeling & Database Upload")
        
        try:
            from label_data import LabelingPipeline
            
            pipeline = LabelingPipeline()
            pipeline.run()
            
            self.save_checkpoint("labeling_complete", {})
            
        except Exception as e:
            logger.error(f"Labeling failed: {e}")
            raise
    
    def _run_dataset_splitting(self):
        """Stage 6: Dataset Splitting"""
        logger.section("Stage 6: Dataset Splitting")
        
        logger.info("Dataset splitting is handled by finalizing/dataset_splitter.py")
        logger.info("Run it separately if needed for YOLO format output")
        
        self.save_checkpoint("pipeline_complete", {})


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Traffic Sign Data Pipeline")
    parser.add_argument("--skip-crawling", action="store_true", help="Skip web scraping")
    parser.add_argument("--skip-filtering", action="store_true", help="Skip fast filtering")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator()
    
    if args.resume:
        checkpoint = orchestrator.load_checkpoint()
        if checkpoint:
            logger.info(f"Resuming from: {checkpoint['stage']}")
    
    orchestrator.run_full_pipeline(
        skip_crawling=args.skip_crawling,
        skip_filtering=args.skip_filtering
    )


if __name__ == "__main__":
    main()
