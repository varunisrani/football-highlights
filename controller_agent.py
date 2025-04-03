import asyncio
import time
from segmentation_agent import segment_video
from analysis_agent import analyze_all_segments
from highlights_agent import create_highlights
from utils import logger

async def process_video(video_path, progress_callback=None):
    """
    Main controller function that orchestrates the entire process
    
    Args:
        video_path: Path to the video file
        progress_callback: Optional callback function to report progress (step, message, percent)
    """
    logger.info(f"Starting football highlight detection for: {video_path}")
    start_time_total = time.time()
    
    # Helper function to update progress if callback exists
    def update_progress(step, message, percent):
        if progress_callback:
            progress_callback(step, message, percent)
        logger.debug(f"Progress: Step {step}, {percent}%, {message}")
    
    try:
        # Step 1: Segment the video
        logger.info("Step 1: Segmenting video...")
        update_progress(1, "Segmenting video...", 5)
        segment_start = time.time()
        
        segments = segment_video(video_path)
        
        if not segments:
            logger.error("Video segmentation failed or returned no segments")
            update_progress(1, "Video segmentation failed", 100)
            return {
                "original_video": video_path,
                "segments": [],
                "highlight_timestamps": [],
                "highlights_video": None,
                "success": False,
                "error": "Video segmentation failed"
            }
            
        segment_time = time.time() - segment_start
        logger.info(f"Video segmentation completed in {segment_time:.2f}s: {len(segments)} segments created")
        update_progress(1, f"Video segmented into {len(segments)} parts", 33)
        
        # Step 2: Analyze segments for highlights
        logger.info("Step 2: Analyzing segments for highlights...")
        update_progress(2, "Analyzing segments for highlights...", 35)
        analysis_start = time.time()
        
        # Periodically update progress during analysis
        total_segments = len(segments)
        
        # Create a wrapper to track analysis progress
        async def analyze_with_progress():
            highlight_timestamps = await analyze_all_segments(segments)
            
            # Report progress throughout based on time estimation (simplified)
            for i in range(10):
                # Skip first and last update (we do those outside)
                if i > 0 and i < 9:
                    progress = 35 + int((i / 9) * 30)  # Scale to 35-65% range
                    update_progress(2, f"Analyzing segments for highlights... {i*10}%", progress)
                await asyncio.sleep(0.1)
                
            return highlight_timestamps
            
        highlight_timestamps = await analyze_with_progress()
        
        analysis_time = time.time() - analysis_start
        logger.info(f"Highlight analysis completed in {analysis_time:.2f}s: {len(highlight_timestamps)} highlights detected")
        update_progress(2, f"Found {len(highlight_timestamps)} highlights", 66)
        
        # Step 3: Create highlights video
        if highlight_timestamps:
            logger.info("Step 3: Creating highlights video...")
            update_progress(3, "Creating highlights video...", 70)
            highlight_start = time.time()
            
            highlights_path = create_highlights(video_path, highlight_timestamps)
            
            highlight_time = time.time() - highlight_start
            if highlights_path:
                logger.info(f"Highlights video created successfully in {highlight_time:.2f}s: {highlights_path}")
                update_progress(3, "Highlights video created successfully", 95)
            else:
                logger.warning("Failed to create highlights video")
                update_progress(3, "Failed to create highlights video", 95)
        else:
            logger.warning("No highlights detected. Skipping highlight video creation.")
            update_progress(3, "No highlights detected", 95)
            highlights_path = None
        
        # Log overall process statistics
        total_time = time.time() - start_time_total
        logger.info(f"Highlight detection process completed in {total_time:.2f}s")
        logger.info(f"Summary: {len(segments)} segments processed, {len(highlight_timestamps)} highlights detected")
        update_progress(3, "Process complete", 100)
        
        # Return the results
        return {
            "original_video": video_path,
            "segments": segments,
            "highlight_timestamps": highlight_timestamps,
            "highlights_video": highlights_path,
            "success": True,
            "processing_time": total_time
        }
    
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        update_progress(3, f"Error: {str(e)}", 100)
        # Return error information
        return {
            "original_video": video_path,
            "segments": [],
            "highlight_timestamps": [],
            "highlights_video": None,
            "success": False,
            "error": str(e)
        } 