import streamlit as st
import pandas as pd

def optimize_playlist(playlist_data):
    playlist_data['likeRate'] = pd.to_numeric(playlist_data['likeRate'], errors='coerce').fillna(0)
    playlist_data['saveRate'] = pd.to_numeric(playlist_data['saveRate'], errors='coerce').fillna(0)
    playlist_data['skipRate'] = pd.to_numeric(playlist_data['skipRate'], errors='coerce').fillna(0)
    
    # Calculate discoveryRate and opt_score
    playlist_data['discoveryRate'] = playlist_data['likeRate'] + playlist_data['saveRate']
    # Add a small value to skip_rate to avoid division by zero, and cap it at 1
    playlist_data['skipRate'] = playlist_data['skipRate'].clip(0.01, 1)
    playlist_data['opt_score'] = playlist_data['discoveryRate'] / playlist_data['skipRate']
    
    # Add opt_score_percentage column
    playlist_data['opt_score_percentage'] = (playlist_data['opt_score'] * 100).round(2).astype(str) + '%'
    
    # Reorder columns to place opt_score_percentage after track_uri if track_uri exists
    if 'track_uri' in playlist_data.columns:
        # Get the position of track_uri
        track_uri_pos = playlist_data.columns.get_loc('track_uri')
        # Create new column order
        cols = list(playlist_data.columns)
        # Remove opt_score_percentage from its current position
        cols.remove('opt_score_percentage')
        # Insert it after track_uri
        cols.insert(track_uri_pos + 1, 'opt_score_percentage')
        # Reorder the dataframe
        playlist_data = playlist_data[cols]
    
    # Sort by opt_score in descending order
    return playlist_data.sort_values(by='opt_score', ascending=False)

st.title("Playlist Sequencer")

uploaded_file = st.file_uploader("Upload your playlist CSV file", type="csv")
if uploaded_file is not None:
    playlist_data = pd.read_csv(uploaded_file)
    optimized_playlist = optimize_playlist(playlist_data)
    st.write("Optimized Playlist:")
    st.dataframe(optimized_playlist)
    
    # Download link
    st.download_button(
        label="Download Optimized Playlist",
        data=optimized_playlist.to_csv(index=False).encode('utf-8'),
        file_name="optimized_playlist.csv",
        mime="text/csv"
    )