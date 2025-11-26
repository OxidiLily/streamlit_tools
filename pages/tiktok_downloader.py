import streamlit as st
import requests
import json
from urllib.parse import urlparse

# Page Config
st.set_page_config(page_title="TikTok Downloader - No Watermark", layout="wide", page_icon="🎵")

# Title and Description
st.title("🎵 TikTok Downloader")
st.markdown("Download TikTok videos without watermark!")

# Create columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Enter TikTok URL")
    tiktok_url = st.text_input(
        "Paste TikTok video URL here",
        placeholder="https://www.tiktok.com/@username/video/1234567890",
        help="Paste the full TikTok video URL"
    )
    
    download_button = st.button("🚀 Download Video", type="primary", use_container_width=True)

with col2:
    st.markdown("### ℹ️ How to use")
    st.markdown("""
    1. Copy TikTok video URL
    2. Paste it in the input field
    3. Click Download button
    4. Wait for processing
    5. Download your video!
    """)

# Function to extract video ID from TikTok URL
def extract_video_id(url):
    """Extract video ID from TikTok URL"""
    try:
        # Handle different TikTok URL formats
        if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
            return url
        elif "/video/" in url:
            return url
        else:
            return url
    except:
        return None

# Function to download TikTok video without watermark
def download_tiktok_video(url):
    """Download TikTok video without watermark using API"""
    try:
        # Using TikTok scraper API (free service)
        api_url = "https://tiktok-video-no-watermark2.p.rapidapi.com/"
        
        # Alternative free API endpoints
        alternatives = [
            "https://www.tikwm.com/api/",
            "https://api.tiklydown.eu.org/api/download"
        ]
        
        # Try the first free API (tikwm.com)
        try:
            response = requests.post(
                alternatives[0],
                data={
                    "url": url,
                    "hd": 1
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return {
                        "success": True,
                        "video_url": data["data"]["play"],
                        "cover": data["data"]["cover"],
                        "title": data["data"]["title"],
                        "author": data["data"]["author"]["unique_id"],
                        "duration": data["data"]["duration"],
                        "download_url": data["data"]["hdplay"] if "hdplay" in data["data"] else data["data"]["play"]
                    }
        except Exception as e:
            st.warning(f"Primary API failed, trying alternative...")
        
        # Try second alternative API
        try:
            response = requests.get(
                alternatives[1],
                params={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    video_data = data.get("video", {})
                    return {
                        "success": True,
                        "video_url": video_data.get("noWatermark"),
                        "cover": data.get("cover"),
                        "title": data.get("title", "TikTok Video"),
                        "author": data.get("author", {}).get("username", "Unknown"),
                        "duration": data.get("duration", 0),
                        "download_url": video_data.get("noWatermark")
                    }
        except Exception as e:
            pass
        
        return {
            "success": False,
            "error": "All API endpoints failed. Please try again later."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }

# Main download logic
if download_button and tiktok_url:
    if not tiktok_url.strip():
        st.error("❌ Please enter a valid TikTok URL!")
    else:
        with st.spinner("🔄 Processing your request... Please wait..."):
            result = download_tiktok_video(tiktok_url)
            
            if result["success"]:
                st.success("✅ Video processed successfully!")
                
                # Display video information
                st.markdown("---")
                st.markdown("### 📹 Video Information")
                
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.markdown(f"**👤 Author:** @{result['author']}")
                    st.markdown(f"**📝 Title:** {result['title'][:100]}...")
                
                with info_col2:
                    st.markdown(f"**⏱️ Duration:** {result['duration']} seconds")
                
                # Display video preview
                st.markdown("### 🎬 Video Preview")
                
                preview_col1, preview_col2 = st.columns([2, 1])
                
                with preview_col1:
                    if result.get("video_url"):
                        st.video(result["video_url"])
                
                with preview_col2:
                    if result.get("cover"):
                        st.image(result["cover"], caption="Video Thumbnail", use_container_width=True)
                
                # Download button
                st.markdown("### 💾 Download")
                
                try:
                    video_response = requests.get(result["download_url"], timeout=30)
                    if video_response.status_code == 200:
                        st.download_button(
                            label="⬇️ Download Video (No Watermark)",
                            data=video_response.content,
                            file_name=f"tiktok_{result['author']}_{result['duration']}s.mp4",
                            mime="video/mp4",
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.error("Failed to fetch video for download. Please try the video player above.")
                except Exception as e:
                    st.warning("⚠️ Direct download failed. You can right-click the video above and select 'Save video as...'")
                    st.markdown(f"**Direct Link:** [Click here to download]({result['download_url']})")
                
            else:
                st.error(f"❌ {result.get('error', 'Failed to download video')}")
                st.info("💡 **Tips:**\n- Make sure the URL is correct\n- Check if the video is public\n- Try again in a few moments")

elif download_button:
    st.warning("⚠️ Please enter a TikTok URL first!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>📱 Supports all TikTok video formats</p>
    <p>⚡ Fast and free - No watermark!</p>
    <p style='font-size: 0.8em; margin-top: 10px;'>
        <em>Note: This tool is for personal use only. Please respect content creators' rights.</em>
    </p>
</div>
""", unsafe_allow_html=True)