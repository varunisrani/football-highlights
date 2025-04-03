import streamlit as st
import os
import tempfile
import asyncio
import time
import threading
from dotenv import load_dotenv
from controller_agent import process_video
from utils import logger, save_uploaded_file, FOLDERS, is_streamlit_cloud

# First check for Streamlit secrets
api_key = None
if is_streamlit_cloud():
    # On Streamlit Cloud, get API key from secrets
    try:
        # First try to get API key from the general section
        try:
            api_key = st.secrets["general"]["API_KEY"]
            logger.info("API key loaded from Streamlit secrets general section")
        except:
            # Then try to get API key directly
            api_key = st.secrets["API_KEY"]
            logger.info("API key loaded from Streamlit secrets root level")
    except Exception as e:
        logger.error(f"Failed to load API key from Streamlit secrets: {str(e)}")
        # No API key from secrets
else:
    # Local development - load from .env
    load_dotenv()
    api_key = os.getenv("API_KEY")
    logger.info("API key loaded from .env file")

# Set the API_KEY environment variable for other components to use
if api_key:
    os.environ["API_KEY"] = api_key
else:
    logger.error("API_KEY not found in environment or secrets")

# Create a global variable to track progress
progress_data = {
    "step": 0,
    "total_steps": 3,
    "message": "Initializing...",
    "percent": 0
}

# Function to update progress from background threads
def update_progress(step, message, percent):
    progress_data["step"] = step
    progress_data["message"] = message
    progress_data["percent"] = percent
    logger.info(f"Progress update: Step {step}, {percent}%, {message}")

def main():
    """Main Streamlit application function"""
    logger.info("Starting Streamlit application")
    
    st.set_page_config(
        page_title="Football Highlights Generator",
        page_icon="⚽",
        layout="wide"
    )

    st.title("⚽ Football Highlights Generator")
    st.write("Upload a football video to automatically generate highlights using Gemini 2.0 Flash!")

    # Add information about the model
    st.info("This application uses Gemini 2.0 Flash, Google's latest multimodal AI model with improved speed and performance for video analysis.")

    # API key warning if missing
    if not api_key:
        if is_streamlit_cloud():
            st.error("⚠️ API Key Missing: Please add your Gemini API key to the Streamlit Cloud secrets. See README for instructions.")
        else:
            st.error("⚠️ API Key Missing: Please add your Gemini API key to the .env file.")
        st.stop()

    # Display deployment info
    cloud_status = "Streamlit Cloud" if is_streamlit_cloud() else "Local Development"
    st.sidebar.info(f"Deployment: {cloud_status}")

    # Display folder paths
    with st.sidebar.expander("Storage Locations", expanded=False):
        st.write("Your videos and highlights are stored in the following locations:")
        for folder_name, folder_path in FOLDERS.items():
            st.code(f"{folder_name}: {folder_path}")
    
    # File uploader - increase size limit for Streamlit Cloud
    max_size_mb = 500 if is_streamlit_cloud() else 200
    st.write(f"Maximum upload size: {max_size_mb}MB")
    
    uploaded_file = st.file_uploader(f"Choose a video file (max {max_size_mb}MB)", type=["mp4", "mov", "avi"])

    # Progress indicators that will be updated
    if "progress_bar" not in st.session_state:
        st.session_state.progress_bar = None
        st.session_state.status_text = None

    # Initialize progress bar and status text placeholders
    progress_bar_placeholder = st.empty()
    status_text_placeholder = st.empty()

    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        logger.info(f"File uploaded: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # Check file size
        if file_size_mb > max_size_mb:
            st.error(f"File size ({file_size_mb:.2f}MB) exceeds the maximum allowed size ({max_size_mb}MB)")
            st.stop()
        
        # Save uploaded file to our uploads folder
        try:
            file_path = save_uploaded_file(uploaded_file)
            logger.info(f"File saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {str(e)}")
            st.error("Failed to process your uploaded file. Please try again.")
            st.stop()
        
        # Show the uploaded video
        st.subheader("Uploaded Video")
        st.video(file_path)
        
        # Process button
        if st.button("Generate Highlights"):
            start_time = time.time()
            logger.info("Highlight generation process started")
            
            # Set up progress tracking
            progress_bar = progress_bar_placeholder.progress(0)
            status_text = status_text_placeholder.text("Initializing...")
            
            # Define a function to update the progress periodically
            def progress_updater():
                last_percent = 0
                while progress_data["percent"] < 100:
                    # Only update if there's a change
                    if progress_data["percent"] != last_percent:
                        progress_bar.progress(progress_data["percent"] / 100)
                        status_text.text(f"Step {progress_data['step']}/{progress_data['total_steps']}: {progress_data['message']}")
                        last_percent = progress_data["percent"]
                    time.sleep(0.1)  # Check every 100ms
            
            # Start the progress updater in a thread
            progress_thread = threading.Thread(target=progress_updater)
            progress_thread.daemon = True
            progress_thread.start()
            
            with st.spinner("Processing video with Gemini 2.0 Flash..."):
                try:
                    # Create a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Initial progress update
                    update_progress(1, "Segmenting video...", 5)
                    
                    # Process the video
                    result = loop.run_until_complete(process_video(file_path, update_progress))
                    
                    # Set progress to complete
                    update_progress(3, "Processing complete!", 100)
                    time.sleep(0.5)  # Give the updater thread time to show 100%
                    
                    if not result.get("success", False):
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                        logger.error(f"Processing failed: {result.get('error')}")
                        st.stop()
                    
                    # Display results
                    processing_time = time.time() - start_time
                    st.success(f"Highlights generated successfully in {processing_time:.2f} seconds!")
                    
                    # Display highlight timestamps
                    st.subheader("Highlight Timestamps")
                    if result["highlight_timestamps"]:
                        for i, timestamp in enumerate(result["highlight_timestamps"]):
                            minutes = int(timestamp // 60)
                            seconds = int(timestamp % 60)
                            st.write(f"#{i+1}: {minutes:02d}:{seconds:02d}")
                    else:
                        st.warning("No highlights were detected in the video")
                    
                    # Display highlights video
                    if result["highlights_video"]:
                        st.subheader("Highlights Video")
                        st.video(result["highlights_video"])
                        
                        # Add download button
                        with open(result["highlights_video"], "rb") as file:
                            st.download_button(
                                label="Download Highlights Video",
                                data=file,
                                file_name="football_highlights.mp4",
                                mime="video/mp4"
                            )
                    else:
                        st.warning("Could not create highlights video")
                    
                    # Show processing statistics
                    st.subheader("Processing Statistics")
                    st.write(f"Total processing time: {processing_time:.2f} seconds")
                    st.write(f"Video segments created: {len(result['segments'])}")
                    st.write(f"Highlights detected: {len(result['highlight_timestamps'])}")
                    
                    # Log completion
                    logger.info(f"Highlight generation completed successfully in {processing_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"Application error: {str(e)}", exc_info=True)
                    st.error(f"An error occurred: {str(e)}")
                    
                finally:
                    # Clean up any resources we might have created
                    loop.close()

    # Show logging information at the bottom
    with st.expander("Application Logs", expanded=False):
        # Create a file handler for Streamlit UI
        if os.path.exists('logs'):
            log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
            if log_files:
                latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join('logs', x)))
                log_path = os.path.join('logs', latest_log)
                
                with open(log_path, 'r') as f:
                    log_content = f.read()
                st.text_area("Log Output", log_content, height=400)
            else:
                st.text("No log files found")
        else:
            st.text("Logging directory not created yet")

# Cleanup temporary files when the app is closed
def cleanup():
    logger.info("Cleaning up temporary files")
    try:
        # We no longer need to delete files since we're storing them in specific folders
        pass
    except Exception as e:
        logger.error(f"Failed to clean up temporary files: {str(e)}")

# Register the cleanup function
import atexit
atexit.register(cleanup)

if __name__ == "__main__":
    main() 