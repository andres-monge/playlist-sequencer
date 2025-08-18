import streamlit as st
import pandas as pd
import json

def extract_track_uris(playlist_data):
    """Extract track URIs from optimized playlist in order"""
    if 'track_uri' not in playlist_data.columns:
        return None
    return '\n'.join(playlist_data['track_uri'].astype(str))

def optimize_playlist(playlist_data):
    playlist_data['likeRate'] = pd.to_numeric(playlist_data['likeRate'], errors='coerce').fillna(0)
    playlist_data['saveRate'] = pd.to_numeric(playlist_data['saveRate'], errors='coerce').fillna(0)
    playlist_data['skipRate'] = pd.to_numeric(playlist_data['skipRate'], errors='coerce').fillna(0)
    
    # Calculate discoveryRate and track_score
    playlist_data['discoveryRate'] = playlist_data['likeRate'] + playlist_data['saveRate']
    # Add a small value to skip_rate to avoid division by zero, and cap it at 1
    playlist_data['skipRate'] = playlist_data['skipRate'].clip(0.01, 1)
    playlist_data['track_score'] = playlist_data['discoveryRate'] / playlist_data['skipRate']
    
    # Add track_score_percentage column
    playlist_data['track_score_percentage'] = (playlist_data['track_score'] * 100).round(2).astype(str) + '%'
    
    # Reorder columns to place track_score_percentage after track_uri if track_uri exists
    if 'track_uri' in playlist_data.columns:
        # Get the position of track_uri
        track_uri_pos = playlist_data.columns.get_loc('track_uri')
        # Create new column order
        cols = list(playlist_data.columns)
        # Remove track_score_percentage from its current position
        cols.remove('track_score_percentage')
        # Insert it after track_uri
        cols.insert(track_uri_pos + 1, 'track_score_percentage')
        # Reorder the dataframe
        playlist_data = playlist_data[cols]
    
    # Sort by track_score in descending order
    return playlist_data.sort_values(by='track_score', ascending=False)

st.title("Playlist Sequencer")

uploaded_file = st.file_uploader("Upload your playlist CSV file", type="csv")
if uploaded_file is not None:
    playlist_data = pd.read_csv(uploaded_file)
    optimized_playlist = optimize_playlist(playlist_data)
    
    # Extract track URIs for clipboard functionality
    track_uris = extract_track_uris(optimized_playlist)
    
    # Create header row with button aligned to dataframe
    if track_uris:
        st.components.v1.html(f"""
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            width: 100%; 
            margin-bottom: 16px;
        ">
            <h3 style="
                margin: 0; 
                font-family: 'Source Sans Pro', sans-serif; 
                font-size: 16px; 
                font-weight: 600; 
                color: rgb(49, 51, 63);
            ">Optimized Playlist:</h3>
            
            <button id="copyBtn" style="
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background-color: rgb(33, 128, 141);
                border: 1px solid rgb(33, 128, 141);
                border-radius: 0.5rem;
                padding: 0.4rem 1rem;
                color: white;
                font-family: 'Source Sans Pro', sans-serif;
                font-size: 16px;
                font-weight: 400;
                cursor: pointer;
                transition: opacity 0.3s;
                width: auto;
                min-width: 180px;
                height: 38px;
                justify-content: center;
                box-sizing: border-box;
                white-space: nowrap;
            " onclick="copyToClipboard()" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
                    <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
                </svg>
                <span id="btnText">Copy All Track URIs</span>
            </button>
        </div>

        <script>
        const trackData = {json.dumps(track_uris)};

        function copyToClipboard() {{
            const btnText = document.getElementById('btnText');
            
            navigator.clipboard.writeText(trackData).then(() => {{
                btnText.textContent = 'Copied';
                
                setTimeout(() => {{
                    btnText.textContent = 'Copy All Track URIs';
                }}, 2000);
            }}).catch(err => {{
                btnText.textContent = 'Copy failed - try again';
                console.error('Clipboard error:', err);
                
                setTimeout(() => {{
                    btnText.textContent = 'Copy All Track URIs';
                }}, 3000);
            }});
        }}
        </script>
        """, height=60)
    else:
        st.write("Optimized Playlist:")
    
    # Display the dataframe
    st.dataframe(optimized_playlist)
    
    # Download link
    st.download_button(
        label="Download Optimized Playlist",
        data=optimized_playlist.to_csv(index=False).encode('utf-8'),
        file_name="optimized_playlist.csv",
        mime="text/csv"
    )
    
    # Show warning if no track_uri column found
    if not track_uris:
        st.warning("No 'track_uri' column found in the uploaded file. Clipboard functionality is not available.")