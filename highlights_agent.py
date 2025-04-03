from moviepy.editor import VideoFileClip, concatenate_videoclips
from utils import create_temp_file, logger
import time
import os

def create_highlights(video_path, timestamps, buffer_seconds=5):
    """
    Create a highlights video from the original video and a list of timestamps
    Each highlight will include {buffer_seconds} before and after the timestamp
    """
    logger.info(f"Creating highlights video from {video_path}")
    logger.info(f"Number of highlight timestamps: {len(timestamps)}")
    logger.info(f"Buffer around each highlight: {buffer_seconds} seconds")
    
    if not timestamps:
        logger.warning("No highlights to process. Returning None.")
        return None
    
    try:
        start_time = time.time()
        
        # Open the original video with audio
        logger.info("Loading original video...")
        original_clip = VideoFileClip(video_path, audio=True)
        video_duration = original_clip.duration
        has_audio = original_clip.audio is not None
        logger.info(f"Original video loaded: duration={video_duration:.2f}s, fps={original_clip.fps}, has_audio={has_audio}")
        
        # Process each highlight timestamp
        highlight_clips = []
        logger.info("Extracting highlight clips...")
        
        for i, timestamp in enumerate(timestamps):
            clip_start = time.time()
            
            # Calculate start and end times for this highlight
            start_time_clip = max(0, timestamp - buffer_seconds)
            end_time_clip = min(original_clip.duration, timestamp + buffer_seconds)
            actual_duration = end_time_clip - start_time_clip
            
            logger.info(f"Highlight #{i+1}: timestamp={timestamp:.2f}s, extracting {start_time_clip:.2f}s to {end_time_clip:.2f}s (duration: {actual_duration:.2f}s)")
            
            try:
                # Extract the subclip
                highlight_clip = original_clip.subclip(start_time_clip, end_time_clip)
                clip_has_audio = highlight_clip.audio is not None
                logger.debug(f"Highlight clip #{i+1} has audio: {clip_has_audio}")
                
                highlight_clips.append(highlight_clip)
                logger.debug(f"Highlight #{i+1} extracted successfully in {time.time() - clip_start:.2f}s")
            except Exception as e:
                logger.error(f"Failed to extract highlight #{i+1}: {str(e)}")
                # Continue with other highlights
        
        # Concatenate all highlight clips
        if highlight_clips:
            logger.info(f"Concatenating {len(highlight_clips)} highlight clips...")
            concat_start = time.time()
            
            try:
                # Use method='compose' to preserve audio quality better
                final_clip = concatenate_videoclips(highlight_clips, method="compose")
                final_duration = final_clip.duration
                final_has_audio = final_clip.audio is not None
                
                logger.info(f"Concatenation successful: duration={final_duration:.2f}s, has_audio={final_has_audio}")
                
                # Create output path and write the final video
                output_path = create_temp_file(folder_type='output')
                logger.info(f"Writing final highlights video to {output_path} (expected duration: {final_duration:.2f}s)")
                
                # Write with audio codecs that ensure quality
                final_clip.write_videofile(
                    output_path, 
                    codec='libx264',
                    audio_codec='aac',  # Use AAC for better compatibility
                    temp_audiofile=f"{output_path}.temp-audio.m4a",
                    remove_temp=True,
                    logger=None,  # Disable moviepy's logger to avoid spam
                    ffmpeg_params=["-q:a", "0"]  # Use high quality audio
                )
                
                # Log file size
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Highlights video created: {file_size_mb:.2f} MB")
                
                # Validate the final video has audio if the original did
                if has_audio:
                    validation_clip = VideoFileClip(output_path)
                    output_has_audio = validation_clip.audio is not None
                    logger.info(f"Final output has audio: {output_has_audio}")
                    if not output_has_audio and has_audio:
                        logger.warning("Audio was lost during highlight creation!")
                    validation_clip.close()
                
                final_clip.close()
                logger.info(f"Highlights compilation completed in {time.time() - concat_start:.2f}s")
            except Exception as e:
                logger.error(f"Failed to concatenate highlights: {str(e)}")
                output_path = None
        else:
            logger.warning("No valid highlight clips to concatenate")
            output_path = None
        
        # Close the original clip to free resources
        original_clip.close()
        
        total_time = time.time() - start_time
        logger.info(f"Highlight creation process completed in {total_time:.2f}s")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Highlight creation failed: {str(e)}")
        # Clean up resources if needed
        if 'original_clip' in locals():
            try:
                original_clip.close()
            except:
                pass
        return None 