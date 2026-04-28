import streamlit as st

NEW_URL = "https://snow.spotify.net/spa/playlist-sequencer/"

st.set_page_config(page_title="Playlist Sequencer (moved)", layout="centered")

# Streamlit's st.markdown sanitizer strips <meta> and <script> tags even with
# unsafe_allow_html=True, and Streamlit's outer iframe sandbox lacks
# allow-top-navigation — so neither meta-refresh nor JS window.top.location
# can deliver an auto-redirect. The user must click. We make that one click
# as obvious as possible.
st.markdown(
    f"""
    <div style="text-align: center; padding: 4rem 1rem; font-family: 'Source Sans Pro', system-ui, sans-serif;">
      <h1 style="margin: 0 0 0.5rem 0; font-size: 2rem;">This tool has moved</h1>
      <p style="color: rgb(120, 124, 130); font-size: 1.05rem; margin: 0 0 2rem 0;">
        Playlist Sequencer is now hosted on Spotify-internal Snow.<br>
        VPN required.
      </p>
      <a href="{NEW_URL}" target="_blank" rel="noopener" style="
        display: inline-block;
        background-color: rgb(33, 128, 141);
        color: white;
        padding: 0.6rem 1.5rem;
        border-radius: 0.5rem;
        text-decoration: none;
        font-size: 1rem;
        font-weight: 500;
      ">Open Playlist Sequencer &rarr;</a>
      <p style="color: rgb(120, 124, 130); font-size: 0.875rem; margin: 1.5rem 0 0 0;">
        Opens <code>snow.spotify.net/spa/playlist-sequencer/</code> in a new tab.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
