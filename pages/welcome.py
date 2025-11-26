import streamlit as st

st.title("Welcome to the App")
st.write("Pilih menu di top navigation bar.")

with st.expander("About Tools"):
    st.title("Spotify Downloader")
    st.write("Tools yang digunakan untuk mengunduh lagu dari Spotify dengan menyalin link lagu dari Spotify")

    st.write("")
    st.title("Prompt Generator")
    st.write("Tools yang digunakan untuk menghasilkan prompt untuk AI gambar, AI suara, dan AI video dengan menggunakan DeepSeek API dan Fal.ai API")

    st.write("")
    st.title("Data Generator Content")
    st.write("Tools yang digunakan untuk menghasilkan ide konten untuk template n8n youtube automation")
    st.write("template n8n yang digunakan adalah https://n8n.io/workflows/5741-generate-cinematic-videos-from-text-prompts-with-gpt-4o-falai-seedance-and-audio/")
    
    st.write("")
    st.title("TikTok Downloader")
    st.write("Tools yang digunakan untuk mengunduh video dari TikTok dengan menyalin link video dari TikTok")
    
    st.write("")
    st.title("Music Player")
    st.write("Tools yang digunakan untuk memutar lagu dari file mp3 yang diunduh dari Spotify")
    