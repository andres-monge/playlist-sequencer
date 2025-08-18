# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python Streamlit application called "Playlist Sequencer" that analyzes and optimizes music playlists based on engagement metrics. The app takes CSV files containing playlist data and reorders tracks by calculating scores based on like rates, save rates, and skip rates.

## Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Development Container
The project includes a devcontainer configuration that:
- Uses Python 3.11 base image
- Auto-installs requirements and streamlit
- Runs the app on port 8501 after container startup
- Opens with README.md and app.py files

## Architecture

### Core Application (app.py)
Single-file Streamlit application with the main function `optimize_playlist()` that:
1. Processes CSV data with playlist metrics (likeRate, saveRate, skipRate)
2. Calculates `discoveryRate = likeRate + saveRate`
3. Computes `track_score = discoveryRate / skipRate` (with skip rate clamped to avoid division by zero)
4. Adds percentage formatting for display
5. Sorts tracks by score descending for optimal playlist ordering

### Data Flow
- User uploads CSV file via Streamlit file uploader
- CSV is processed by pandas to clean and calculate metrics
- Results displayed in interactive dataframe
- Optimized playlist available for download as CSV

### Key Algorithms
- **Score Calculation**: `track_score = (likeRate + saveRate) / max(skipRate, 0.01)`
- **Skip Rate Clamping**: Prevents division by zero by setting minimum skip rate to 0.01
- **Column Reordering**: Places track_score_percentage after track_uri column when present

## Dependencies
- **streamlit**: Web app framework
- **pandas**: Data processing and CSV handling
- **streamlit-js-eval**: JavaScript evaluation for clipboard access

## Key Features
- **Automatic Clipboard Copy**: Track URIs are automatically copied when CSV is uploaded
- **Manual Copy Button**: Users can re-copy URIs using the "Copy all track URIs" button
- **Toast Notifications**: User feedback for copy actions and error states
- **Error Handling**: Graceful degradation when track_uri column is missing