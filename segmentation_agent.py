from moviepy.editor import VideoFileClip
from utils import get_video_duration, create_temp_file, logger
import time
import os

def segment_video(video_path, segment_length=300):
    """
    Split video into segments of specified length (default 5 minutes = 300 seconds)
    Returns list of paths to segmented videos
    """
    logger.info(f"Starting video segmentation process for {video_path}")
    logger.info(f"Segment length: {segment_length} seconds")
    
    try:
        start_time_total = time.time()
        
        # Get video information
        clip = VideoFileClip(video_path, audio=True)  # Explicitly load audio
        duration = clip.duration
        fps = clip.fps
        size = clip.size
        has_audio = clip.audio is not None
        
        logger.info(f"Video loaded: duration={duration:.2f}s, fps={fps}, size={size}, has_audio={has_audio}")
        
        if not has_audio:
            logger.warning("Input video does not have audio track")
        
        segment_paths = []
        total_segments = (int(duration) + segment_length - 1) // segment_length  # Ceiling division
        logger.info(f"Splitting video into {total_segments} segments")
        
        for i, start_t in enumerate(range(0, int(duration), segment_length)):
            segment_start = time.time()
            
            end_t = min(start_t + segment_length, duration)
            logger.info(f"Creating segment {i+1}/{total_segments}: {start_t}s to {end_t}s (duration: {end_t-start_t:.2f}s)")
            
            try:
                # Extract the segment
                segment = clip.subclip(start_t, end_t)
                
                # Check if segment has audio
                segment_has_audio = segment.audio is not None
                logger.info(f"Segment {i+1} has audio: {segment_has_audio}")
                
                # Create output path
                segment_path = create_temp_file()
                logger.info(f"Writing segment to {segment_path}")
                
                # Write segment to file with progress reporting
                segment.write_videofile(
                    segment_path, 
                    codec='libx264',
                    audio_codec='aac',  # Use AAC for better compatibility
                    temp_audiofile=f"{segment_path}.temp-audio.m4a",  # Temp file for audio
                    remove_temp=True,  # Remove temp audio file when done
                    logger=None  # Disable moviepy's logger to avoid spam
                )
                
                segment_paths.append((segment_path, start_t, end_t))
                segment_time = time.time() - segment_start
                logger.info(f"Segment {i+1} created successfully in {segment_time:.2f}s")
                
                # Check file size and validate audio
                file_size_mb = os.path.getsize(segment_path) / (1024 * 1024)
                logger.debug(f"Segment file size: {file_size_mb:.2f} MB")
                
                # Validate that the segment has audio if original did
                if has_audio:
                    validation_clip = VideoFileClip(segment_path)
                    if validation_clip.audio is None:
                        logger.warning(f"Segment {i+1} is missing audio! Original had audio but segment does not.")
                    else:
                        logger.debug(f"Segment {i+1} audio validation passed")
                    validation_clip.close()
                
            except Exception as e:
                logger.error(f"Failed to create segment {i+1}: {str(e)}")
                # Continue with other segments even if one fails
        
        # Close the original clip
        clip.close()
        
        total_time = time.time() - start_time_total
        logger.info(f"Video segmentation completed: {len(segment_paths)} segments created in {total_time:.2f}s")
        
        return segment_paths
        
    except Exception as e:
        logger.error(f"Video segmentation failed: {str(e)}")
        # If we already opened the clip, try to close it
        if 'clip' in locals():
            try:
                clip.close()
            except:
                pass
        return [] 