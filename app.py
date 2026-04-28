import streamlit as st

NEW_URL = "https://snow.spotify.net/spa/playlist-sequencer/"

st.set_page_config(page_title="Playlist Sequencer (moved)", layout="centered")

st.markdown(
    f"""
    <meta http-equiv="refresh" content="3; url={NEW_URL}">
    <div style="text-align: center; padding: 4rem 1rem; font-family: 'Source Sans Pro', system-ui, sans-serif;">
      <h1 style="margin: 0 0 1rem 0;">This tool has moved</h1>
      <p style="color: rgb(120, 124, 130); font-size: 1.05rem; margin: 0 0 1.5rem 0;">
        Playlist Sequencer is now hosted at <code>snow.spotify.net/spa/playlist-sequencer/</code>.<br>
        Redirecting in 3 seconds…
      </p>
      <p>
        <a href="{NEW_URL}" target="_top" style="color: rgb(33, 128, 141);">
          Click here if you are not redirected automatically.
        </a>
      </p>
    </div>
    <script>
      setTimeout(function() {{
        try {{ window.top.location.href = "{NEW_URL}"; }}
        catch (e) {{ window.location.href = "{NEW_URL}"; }}
      }}, 3000);
    </script>
    """,
    unsafe_allow_html=True,
)
