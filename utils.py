import os
from moviepy.editor import VideoFileClip
import tempfile
import logging
import time
import json
from datetime import datetime
import uuid

# Configure logging
def setup_logging():
    """Configure and return a logger with proper formatting"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'highlight_detection_{timestamp}.log')
    
    # Create logger
    logger = logging.getLogger('football_highlights')
    logger.setLevel(logging.DEBUG)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Check if running on Streamlit Cloud
def is_streamlit_cloud():
    """Check if the app is running on Streamlit Cloud"""
    return os.environ.get('IS_STREAMLIT_CLOUD') == 'true' or '/mount/src/' in os.path.dirname(os.path.abspath(__file__))

# Create folder for storing videos
def ensure_folders_exist():
    """Create necessary folders for storing videos and output"""
    # Determine if we're running on Streamlit Cloud
    on_streamlit_cloud = is_streamlit_cloud()
    logger.info(f"Running on Streamlit Cloud: {on_streamlit_cloud}")
    
    # Choose base directory based on environment
    if on_streamlit_cloud:
        # On Streamlit Cloud, use /tmp for storage (ephemeral but accessible)
        base_dir = '/tmp'
        logger.info("Using /tmp directory for storage on Streamlit Cloud")
    else:
        # For local development, use the project directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Using local directory for storage: {base_dir}")
    
    # Create folders
    folders = {
        'segments': os.path.join(base_dir, 'football_highlights', 'segments'),
        'output': os.path.join(base_dir, 'football_highlights', 'output'),
        'uploads': os.path.join(base_dir, 'football_highlights', 'uploads')
    }
    
    for folder_name, folder_path in folders.items():
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Ensured folder exists: {folder_path}")
    
    return folders

# Initialize folders
FOLDERS = ensure_folders_exist()

def get_video_duration(video_path):
    """Get duration of video in seconds"""
    logger.info(f"Getting duration for video: {video_path}")
    start_time = time.time()
    
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        elapsed = time.time() - start_time
        logger.info(f"Video duration: {duration:.2f} seconds (operation took {elapsed:.2f}s)")
        return duration
    except Exception as e:
        logger.error(f"Failed to get video duration: {str(e)}")
        raise

def create_temp_file(suffix=".mp4", folder_type='segments'):
    """Create a file in the specified folder type"""
    try:
        # Generate a unique filename with timestamp and UUID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
        
        if folder_type not in FOLDERS:
            folder_type = 'segments'  # Default to segments folder
            
        filename = f"{timestamp}_{unique_id}{suffix}"
        file_path = os.path.join(FOLDERS[folder_type], filename)
        
        logger.debug(f"Created file path: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to create file path: {str(e)}")
        # Fallback to temporary file if there's an error
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        logger.debug(f"Created fallback temporary file: {path}")
        return path

def save_uploaded_file(uploaded_file):
    """Save an uploaded file to the uploads folder"""
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Get file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if not file_ext:
            file_ext = '.mp4'  # Default to mp4 if no extension
            
        # Create filepath
        filename = f"{timestamp}_{unique_id}{file_ext}"
        file_path = os.path.join(FOLDERS['uploads'], filename)
        
        # Write file content
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
            
        logger.info(f"Uploaded file saved to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise

def log_api_request(model, prompt, is_multimodal=False):
    """Log information about an API request"""
    logger.info(f"API Request - Model: {model}")
    logger.info(f"API Request - Multimodal: {is_multimodal}")
    logger.debug(f"API Request - Prompt: {prompt[:500]}...")

def log_api_response(response_text, elapsed_time):
    """Log information about an API response"""
    logger.info(f"API Response received in {elapsed_time:.2f}s")
    # Truncate very long responses to avoid huge log files
    if len(response_text) > 1000:
        logger.debug(f"API Response (truncated): {response_text[:1000]}...")
    else:
        logger.debug(f"API Response: {response_text}")

def log_json_data(data, prefix=""):
    """Log a JSON object in a readable format"""
    try:
        formatted_json = json.dumps(data, indent=2)
        logger.debug(f"{prefix}\n{formatted_json}")
    except Exception as e:
        logger.error(f"Failed to log JSON data: {str(e)}") 