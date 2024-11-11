import streamlit as st
import pandas as pd

def optimize_playlist(playlist_data):
    playlist_data['likeRate'] = pd.to_numeric(playlist_data['likeRate'], errors='coerce').fillna(0)
    playlist_data['saveRate'] = pd.to_numeric(playlist_data['saveRate'], errors='coerce').fillna(0)
    playlist_data['skipRate'] = pd.to_numeric(playlist_data['skipRate'], errors='coerce').fillna(0)
    
    # Calculate like&saveRate and opt_score
    playlist_data['like&saveRate'] = playlist_data['likeRate'] + playlist_data['saveRate']
    playlist_data['opt_score'] = playlist_data['like&saveRate'] * (1 - playlist_data['skipRate'])
    
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