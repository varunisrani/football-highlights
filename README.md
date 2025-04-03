# Football Video Highlights Generator

This application automatically generates highlight reels from football videos using Google's Gemini 2.0 Flash model for video analysis.

## Features

- **Advanced Video Analysis**: Uses Google's Gemini 2.0 Flash multimodal model to detect exciting moments in football videos
- **Parallel Processing**: Analyzes video segments in parallel for faster performance
- **Highlight Detection**: Automatically identifies goals, near misses, great saves, skillful plays, and fouls
- **Comprehensive Logging**: Detailed logging of all operations including API calls to Gemini
- **User-Friendly Interface**: Simple Streamlit interface for easy upload and processing
- **Error Handling**: Robust error handling throughout the pipeline

## Requirements

- Python 3.8 or higher
- Google Gemini API key

## Installation

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your Gemini API key to the `.env` file:
   ```
   API_KEY="your_gemini_api_key"
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
2. Upload a football video file (MP4, MOV, or AVI format)
3. Click "Generate Highlights" to start the analysis process
4. View timestamps, statistics, and download the generated highlights

## Logging System

The application includes a comprehensive logging system that records:

- **API Calls**: All requests and responses from the Gemini API
- **Processing Steps**: Detailed information about each step of the pipeline
- **Performance Metrics**: Timing information for all major operations
- **Errors and Warnings**: Complete error tracking throughout the application

Logs are stored in the `logs` directory with timestamps and can be viewed in the application UI by expanding the "Application Logs" section.

## How it Works

1. **Segmentation**: The application splits the input video into manageable segments
2. **Analysis**: Each segment is analyzed by Gemini 2.0 Flash to detect exciting moments
3. **Compilation**: A highlight reel is created by extracting and concatenating the detected moments

## Project Structure

```
football-highlights/
  ├── .env                  # API key storage
  ├── app.py                # Main Streamlit application
  ├── controller_agent.py   # Main controller logic
  ├── segmentation_agent.py # Video segmentation logic
  ├── analysis_agent.py     # Highlight detection with Gemini
  ├── highlights_agent.py   # Final highlight creation
  ├── utils.py              # Utility functions and logging
  └── logs/                 # Directory for log files
```

## Limitations

- Processing time depends on video length and quality
- Performance may vary based on the clarity of the video
- Requires internet connection for AI model access

## License

MIT 