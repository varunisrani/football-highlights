import google.generativeai as genai
import base64
import os
import json
import time
from dotenv import load_dotenv
import asyncio
from utils import logger, log_api_request, log_api_response, log_json_data

load_dotenv()

# Configure the Gemini API
api_key = os.getenv("API_KEY")
if not api_key:
    logger.error("API_KEY not found in environment variables. Please set it in the .env file.")
    raise ValueError("API_KEY not found. Check your .env file.")

genai.configure(api_key=api_key)
logger.info("Gemini API configured successfully")

async def analyze_segment(segment_info):
    """
    Analyze a video segment to identify potential highlights
    Returns list of timestamps with highlight moments
    """
    segment_path, start_time, end_time = segment_info
    segment_duration = end_time - start_time
    
    logger.info(f"Analyzing segment from {start_time} to {end_time} (duration: {segment_duration}s)")
    logger.debug(f"Segment file path: {segment_path}")
    
    # Create the Gemini 2.0 Flash model
    model_name = 'gemini-2.0-flash-exp'
    model = genai.GenerativeModel(model_name)
    logger.info(f"Using model: {model_name}")
    
    # Read the video file as bytes
    try:
        with open(segment_path, "rb") as f:
            video_bytes = f.read()
        video_size_mb = len(video_bytes) / (1024 * 1024)
        logger.info(f"Video loaded: {video_size_mb:.2f} MB")
    except Exception as e:
        logger.error(f"Failed to read video file: {str(e)}")
        return []
    
    # Convert video to compatible format for the API
    video_part = {"mime_type": "video/mp4", "data": video_bytes}
    
    prompt = """
    Analyze this football video segment and identify potential highlight moments.
    Look for:
    1. Goals
    2. Near misses
    3. Great saves
    4. Skillful plays
    5. Fouls or cards
    
    Return a JSON list of objects with:
    1. timestamp_seconds (relative to this segment)
    2. event_type (from the categories above)
    3. confidence_score (0-1)
    
    Example format:
    [
      {"timestamp_seconds": 45.2, "event_type": "Goal", "confidence_score": 0.95},
      {"timestamp_seconds": 120.7, "event_type": "Great save", "confidence_score": 0.85}
    ]
    """
    
    log_api_request(model_name, prompt, is_multimodal=True)
    logger.info("Sending video analysis request to Gemini API...")
    
    # Generate content using Gemini 2.0 Flash with timing
    start_time_api = time.time()
    try:
        response = model.generate_content(
            contents=[video_part, prompt]
        )
        elapsed_time = time.time() - start_time_api
        log_api_response(response.text, elapsed_time)
    except Exception as e:
        logger.error(f"Gemini API request failed: {str(e)}")
        return []
    
    # Process the response to extract timestamps and events
    highlights = []
    logger.info("Parsing response for highlight timestamps")
    
    try:
        # Get the text response and try to find a JSON structure
        response_text = response.text.strip()
        
        # Attempt to find JSON in the response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            logger.info("JSON structure found in response")
            json_str = response_text[json_start:json_end]
            
            try:
                highlights_data = json.loads(json_str)
                log_json_data(highlights_data, "Parsed highlights data:")
                
                for idx, highlight in enumerate(highlights_data):
                    if "timestamp_seconds" in highlight:
                        relative_time = float(highlight["timestamp_seconds"])
                        global_time = start_time + relative_time
                        event_type = highlight.get("event_type", "Unknown")
                        confidence = highlight.get("confidence_score", 0)
                        
                        highlights.append(global_time)
                        logger.info(f"Highlight #{idx+1}: {event_type} at {global_time:.2f}s (confidence: {confidence})")
                    else:
                        logger.warning(f"Skipping highlight {idx+1}: missing timestamp_seconds field")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.debug(f"Problematic JSON string: {json_str}")
        else:
            logger.warning("No JSON structure found in response. Falling back to text parsing.")
            # Fallback to parsing text if no JSON is found
            for line_num, line in enumerate(response_text.split('\n')):
                if 'seconds' in line and ':' in line:
                    try:
                        time_part = line.split(':')[1].split(',')[0].strip()
                        if time_part.replace('.', '', 1).isdigit():
                            relative_time = float(time_part)
                            global_time = start_time + relative_time
                            highlights.append(global_time)
                            logger.info(f"Highlight found in line {line_num+1} at {global_time:.2f}s")
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num+1}: {str(e)}")
                        continue
    except Exception as e:
        logger.error(f"Error parsing highlight timestamps: {str(e)}")
    
    logger.info(f"Found {len(highlights)} highlights in segment {start_time}-{end_time}")
    return highlights

async def analyze_all_segments(segment_infos):
    """Analyze all segments in parallel"""
    logger.info(f"Starting analysis of {len(segment_infos)} video segments in parallel")
    
    tasks = [analyze_segment(segment_info) for segment_info in segment_infos]
    
    try:
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of highlights
        all_highlights = []
        for i, highlight_list in enumerate(results):
            segment_start = segment_infos[i][1]
            segment_end = segment_infos[i][2]
            logger.info(f"Segment {i+1} ({segment_start}-{segment_end}s): {len(highlight_list)} highlights")
            all_highlights.extend(highlight_list)
        
        # Sort highlights by timestamp
        sorted_highlights = sorted(all_highlights)
        logger.info(f"Total highlights found across all segments: {len(sorted_highlights)}")
        
        return sorted_highlights
    except Exception as e:
        logger.error(f"Failed to analyze all segments: {str(e)}")
        return [] 