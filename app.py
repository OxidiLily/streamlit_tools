import streamlit as st

st.set_page_config(page_title="OxidiLily Tools",page_icon="✨", layout="wide")

pages = {
    "Home": [
        st.Page("pages/welcome.py", title="Welcome"),
    ],
    "Tools": [
        st.Page("pages/tiktok_downloader.py", title="TikTok Downloader"),
        st.Page("pages/spotify_downloader.py", title="Spotify Downloader"),
        st.Page("pages/promt_generator.py", title="Prompt Generator Video"),
        st.Page("pages/data.py", title="Data Generator Content"),
    ],
    "Music":[
        st.Page("pages/music.py", title="Music Player"),
    ]
}

pg = st.navigation(pages, position="top",expanded=True)
pg.run()
