import streamlit as st
import fal_client
import os
import requests
from openai import OpenAI
import base64
from io import BytesIO
import time

# Page config
st.set_page_config(page_title="Fal.ai Creative Studio", layout="wide")

# Sidebar for API Keys
st.sidebar.title="Configuration"

# Initialize session state for API keys if not exists
if 'fal_key' not in st.session_state:
    st.session_state.fal_key = os.environ.get("FAL_KEY", "")
if 'deepseek_key' not in st.session_state:
    st.session_state.deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")

# Delete button BEFORE input fields
# Input fields using session_state
fal_key = st.sidebar.text_input("FAL_KEY", type="password", value=st.session_state.fal_key, key="fal_input")
deepseek_key = st.sidebar.text_input("DEEPSEEK_API_KEY", type="password", value=st.session_state.deepseek_key, key="deepseek_input")
delete_key = st.sidebar.button("Delete API Key")
if delete_key:
    # Clear all sources
    st.session_state.fal_key = ""
    st.session_state.deepseek_key = ""
    os.environ["DEEPSEEK_API_KEY"] = ""
    os.environ["FAL_KEY"] = ""
    st.sidebar.success("API Key deleted!")
    time.sleep(4)
    st.rerun()


st.sidebar.divider()
st.sidebar.subheader("💾 Local Storage")
auto_save = st.sidebar.checkbox("Auto-save generated files", value=True)
save_dir = st.sidebar.text_input("Save directory", value="./generated_files")

# Update both session_state and os.environ when keys are entered
if fal_key:
    st.session_state.fal_key = fal_key
    os.environ["FAL_KEY"] = fal_key
if deepseek_key:
    st.session_state.deepseek_key = deepseek_key
    os.environ["DEEPSEEK_API_KEY"] = deepseek_key



st.title("Fal.ai Creative Studio")

# Helper function to save uploaded file to temp
def save_uploaded_file(uploaded_file):
    try:
        with open(os.path.join("temp_image.jpg"), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return "temp_image.jpg"
    except Exception as e:
        return None

# Helper function to upload file to fal
def upload_to_fal(file_path):
    url = fal_client.upload_file(file_path)
    return url

# Helper function to sanitize filename
def sanitize_filename(text, max_length=50):
    """Convert text to safe filename"""
    import re
    # Remove special characters, keep only alphanumeric and spaces
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Lowercase and limit length
    text = text.lower()[:max_length]
    # Remove trailing underscores
    text = text.rstrip('_')
    return text or "generated"

# Helper function to save file from URL
def save_file_from_url(url, filename, subfolder=""):
    """Download and save file from URL to local directory"""
    if not auto_save:
        return None
    
    try:
        # Create directory structure
        save_path = os.path.join(save_dir, subfolder)
        os.makedirs(save_path, exist_ok=True)
        
        # Download file
        response = requests.get(url)
        if response.status_code == 200:
            filepath = os.path.join(save_path, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        st.warning(f"Could not save file: {e}")
    return None

# Prompt Enhancement Section
st.header("1. Prompt Enhancer (DeepSeek)")
with st.expander("Enhance your prompt"):
    simple_prompt = st.text_area("Enter a simple theme or idea:", "A futuristic city with flying cars")
    
    content_theme = st.selectbox(
        "Select Content Theme:",
        ["General", "Storytelling", "Mini Investigation", "Did You Know?", "Mystery", "Horror", "Cinematic"]
    )

    if st.button("Enhance Prompt"):
        if not deepseek_key:
            st.error("Please provide DEEPSEEK_API_KEY in the sidebar.")
        else:
            try:
                client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
                
                # System prompt yang lebih fokus dan ringkas
                system_prompt = """You are a creative assistant specialized in creating prompts for AI video generation.

IMPORTANT RULES:
- Keep VISUAL_PROMPT under 100 words
- Use simple, clear descriptions
- Avoid complex camera movements
- Focus on main subject, lighting, and mood
- Use concrete visual terms, avoid abstract concepts
- Make AUDIO_SCRIPT longer and more detailed (50-75 words / ~20-30 seconds)

Create two parts:
1. VISUAL_PROMPT: A concise, clear prompt for video generation (max 100 words). Focus on: main subject, setting, lighting, colors, and overall mood.
2. AUDIO_SCRIPT: A detailed, engaging voiceover script (50-75 words, ~20-30 seconds). Should be complete narration with intro, body, and conclusion. Include specific details and descriptions that bring the visual to life.

Separate with labels 'VISUAL_PROMPT:' and 'AUDIO_SCRIPT:'."""
                
                if content_theme == "Storytelling":
                    system_prompt += "\n\nTHEME: Storytelling - Simple narrative scene with clear emotional tone. Audio should tell a brief story."
                elif content_theme == "Mini Investigation":
                    system_prompt += "\n\nTHEME: Investigation - Detective-style scene with mystery atmosphere. Audio should be investigative and curious."
                elif content_theme == "Did You Know?":
                    system_prompt += "\n\nTHEME: Educational - Clean, bright educational setting. Audio should present an interesting fact clearly."
                elif content_theme == "Mystery":
                    system_prompt += "\n\nTHEME: Mystery - Dark, intriguing atmosphere with shadows. Audio should be mysterious and captivating."
                elif content_theme == "Horror":
                    system_prompt += "\n\nTHEME: Horror - Dark, eerie setting with ominous mood. Audio should be suspenseful and chilling."
                elif content_theme == "Cinematic":
                    system_prompt += "\n\nTHEME: Cinematic - Professional movie-quality scene with dramatic lighting. Audio should be like a powerful movie trailer."

                with st.spinner("Enhancing prompt..."):
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Create a video prompt for: {simple_prompt}\n\nIMPORTANT: Keep VISUAL_PROMPT simple and under 100 words!"}
                        ],
                        temperature=0.7,
                        max_tokens=500  # Batasi output
                    )
                    full_response = response.choices[0].message.content
                    
                    # Parse response
                    visual_prompt = ""
                    audio_script = ""
                    
                    if "VISUAL_PROMPT:" in full_response and "AUDIO_SCRIPT:" in full_response:
                        parts = full_response.split("AUDIO_SCRIPT:")
                        visual_prompt = parts[0].replace("VISUAL_PROMPT:", "").strip()
                        audio_script = parts[1].strip()
                    else:
                        visual_prompt = full_response
                        audio_script = full_response

                    st.session_state['enhanced_prompt'] = visual_prompt
                    st.session_state['audio_script'] = audio_script
                    st.success("Prompt enhanced!")
            except Exception as e:
                st.error(f"Error enhancing prompt: {e}")

    final_prompt = st.text_area("Final Visual Prompt (Editable):", value=st.session_state.get('enhanced_prompt', simple_prompt), height="stretch")
    final_audio_script = st.text_area("Final Audio Script (Editable):", value=st.session_state.get('audio_script', simple_prompt), height="stretch")


# Tabs for Generation
tab1, tab2, tab3 = st.tabs(["Thumbnail Generation", "Video Generation", "Audio Generation"])

with tab1:
    st.header("Thumbnail Generation (Imagen4)")
    col1, col2 = st.columns([3, 1])
    with col1:
        tema = st.text_area("Tema", value=f"{final_prompt}")
        aspect_ratio = st.selectbox("Aspect Ratio", ["9:16", "16:9", "1:1", "4:3", "3:4"], index=0)
    with col2:
        num_images = st.number_input("Number of Images", min_value=1, max_value=4, value=1)
        
    if st.button("Generate Thumbnail"):
        if not fal_key:
            st.error("Please provide FAL_KEY in the sidebar.")
        else:
            try:
                with st.spinner("Generating thumbnail..."):
                    def on_queue_update(update):
                        if isinstance(update, fal_client.InProgress):
                            for log in update.logs:
                                st.text(f"Log: {log['message']}")

                    generated_images = []
                    for i in range(num_images):
                        st.write(f"Generating thumbnail {i+1}/{num_images}...")
                        result = fal_client.subscribe(
                            "fal-ai/imagen4/preview",
                            arguments={
                                "prompt": tema,
                                "aspect_ratio": aspect_ratio
                            },
                            with_logs=True,
                            on_queue_update=on_queue_update,
                        )
                        
                        if result and 'images' in result and len(result['images']) > 0:
                            image_url = result['images'][0]['url']
                            generated_images.append(image_url)
                            st.image(image_url, caption=f"Generated Thumbnail {i+1}")
                            
                            # Save locally
                            if auto_save:
                                filename_base = sanitize_filename(simple_prompt)
                                saved_path = save_file_from_url(
                                    image_url, 
                                    f"{filename_base}_thumb{i+1}_{aspect_ratio.replace(':', 'x')}.png",
                                    "thumbnails"
                                )
                                if saved_path:
                                    st.caption(f"💾 Saved: {saved_path}")
                        else:
                            st.error(f"No thumbnail returned for iteration {i+1}.")
                            st.write(result)
                    
                    if generated_images:
                        st.session_state['generated_image_urls'] = generated_images
                        st.session_state['generated_image_url'] = generated_images[0] # Default to first
                        st.success(f"{len(generated_images)} thumbnails generated successfully!")

            except Exception as e:
                st.error(f"Error generating thumbnail: {e}")

with tab2:
    st.header("Video Generation (Seedance)")
    
    # Option to use reference images
    use_reference_images = st.checkbox("Use Generated Thumbnails as Reference", value=False)
    selected_image_urls = []
    
    if use_reference_images and 'generated_image_urls' in st.session_state:
        selected_indices = st.multiselect(
            "Select Thumbnails to Use:", 
            range(len(st.session_state['generated_image_urls'])), 
            format_func=lambda x: f"Thumbnail {x+1}"
        )
        selected_image_urls = [st.session_state['generated_image_urls'][i] for i in selected_indices]
        
        if selected_image_urls:
            cols = st.columns(min(len(selected_image_urls), 4))
            for idx, url in enumerate(selected_image_urls[:4]):
                with cols[idx]:
                    st.image(url, caption=f"Ref {idx+1}", width=100)
    
    # Editable Video Prompt
    col_dur, col_warn = st.columns([1, 3])
    with col_dur:
        durasi = st.number_input("Durasi Video (detik)", min_value=2, max_value=12, value=5, step=1)
    with col_warn:
        st.info("ℹ️ Seedance API hanya mendukung durasi 2-12 detik")
    
    default_video_prompt = f"Video rasio 9:16, durasi {durasi} detik. {final_prompt}"
    video_prompt = st.text_area("Video Prompt:", value=default_video_prompt, height=100)

    if st.button("Generate Video"):
        if not fal_key:
            st.error("Please provide FAL_KEY in the sidebar.")
        else:
            try:
                with st.spinner("Generating video..."):
                    # Build video arguments
                    video_args = {
                        "prompt": video_prompt,
                        "aspect_ratio": "auto",
                        "resolution": "720p",
                        "duration": durasi  # Use user-specified duration
                    }
                    
                    # Add reference images - they are required for Seedance
                    if selected_image_urls:
                        video_args["reference_image_urls"] = selected_image_urls
                    elif 'generated_image_urls' in st.session_state and st.session_state['generated_image_urls']:
                        # Use first generated image as fallback
                        video_args["reference_image_urls"] = [st.session_state['generated_image_urls'][0]]
                        st.warning("⚠️ No images selected. Using first generated thumbnail as reference.")
                    else:
                        st.error("❌ Seedance requires at least one reference image. Please generate thumbnails first!")
                        st.stop()
                    
                    result = fal_client.subscribe(
                        "fal-ai/bytedance/seedance/v1/lite/reference-to-video",
                        arguments=video_args,
                        with_logs=False,

                    )
                    
                    if result and 'video' in result:
                        video_url = result['video']['url']
                        st.video(video_url)
                        
                        # Store video URL for potential audio combination
                        st.session_state['generated_video_url'] = video_url
                        
                        # Save locally
                        if auto_save:
                            filename_base = sanitize_filename(simple_prompt)
                            saved_path = save_file_from_url(
                                video_url, 
                                f"{filename_base}_video_{durasi}s.mp4",
                                "videos"
                            )
                            if saved_path:
                                st.success(f"💾 Video saved: {saved_path}")
                        
                        # Download button
                        video_content = requests.get(video_url).content
                        st.download_button(
                            label="Download Video",
                            data=video_content,
                            file_name="generated_video.mp4",
                            mime="video/mp4"
                        )
                        
                        # Show info if audio is available
                        if 'generated_audio_url' in st.session_state:
                            st.info("💡 Video dan audio telah di-generate. Untuk menggabungkan audio ke video, Anda bisa menggunakan editor video atau tools seperti FFmpeg.")
                            st.code(f"ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -shortest output.mp4", language="bash")
                        
                        st.success("Video generated successfully!")
                    else:
                        st.error("No video returned.")
                        st.write(result)

            except Exception as e:
                st.error(f"Error generating video: {e}")

with tab3:
    st.header("Audio Generation (Chatterbox)")
    
    # Audio script expansion feature
    col1, col2 = st.columns([4, 1])
    with col1:
        audio_prompt = st.text_area("Enter text to generate audio:", value=final_audio_script, height=150)
    with col2:
        target_duration = st.number_input("Target Duration (seconds)", min_value=5, max_value=60, value=20)
        if st.button("🔄 Expand Script"):
            if not deepseek_key:
                st.error("Please provide DEEPSEEK_API_KEY in the sidebar.")
            else:
                try:
                    with st.spinner("Expanding audio script..."):
                        client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
                        target_words = int(target_duration * 2.5)  # ~2.5 words per second
                        
                        expansion_prompt = f"""Expand this audio script to approximately {target_words} words (~{target_duration} seconds).

Original script:
{audio_prompt}

Create a more detailed, engaging narration that:
- Maintains the same theme and tone
- Adds more descriptive details
- Includes specific examples or imagery
- Has a clear beginning, middle, and end
- Is suitable for text-to-speech voiceover
- Target length: {target_words} words

Provide ONLY the expanded script, no explanations."""
                        
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "You are a professional scriptwriter for video narrations."},
                                {"role": "user", "content": expansion_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        expanded_script = response.choices[0].message.content.strip()
                        st.session_state['expanded_audio_script'] = expanded_script
                        st.success(f"✅ Script expanded to ~{len(expanded_script.split())} words!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error expanding script: {e}")
    
    # Update audio prompt if expanded version exists
    if 'expanded_audio_script' in st.session_state:
        audio_prompt = st.session_state['expanded_audio_script']
    
    voice = st.selectbox("Select Voice:", ["Jennifer (English)", "Rigon (English)"], index=0)

    if st.button("Generate Audio"):
        if not fal_key:
            st.error("Please provide FAL_KEY in the sidebar.")
        else:
            try:
                with st.spinner("Generating audio..."):

                    result = fal_client.subscribe(
                        "fal-ai/chatterbox/text-to-speech",
                        arguments={
                            "text": audio_prompt,
                            "voice": "Jennifer" if "Jennifer" in voice else "Rigon"
                        },
                        with_logs=False,
                    )
                    
                    if result and 'audio' in result:
                        audio_url = result['audio']['url']
                        st.audio(audio_url)
                        
                        # Store audio URL
                        st.session_state['generated_audio_url'] = audio_url
                        
                        # Save locally
                        if auto_save:
                            filename_base = sanitize_filename(simple_prompt)
                            saved_path = save_file_from_url(
                                audio_url, 
                                f"{filename_base}_audio.mp3",
                                "audio"
                            )
                            if saved_path:
                                st.success(f"💾 Audio saved: {saved_path}")
                        
                        # Download button
                        audio_content = requests.get(audio_url).content
                        st.download_button(
                            label="Download Audio",
                            data=audio_content,
                            file_name="generated_audio.mp3",
                            mime="audio/mpeg"
                        )
                        st.success("Audio generated successfully!")
                    else:
                        st.error("No audio returned.")
                        st.write(result)

            except Exception as e:
                st.error(f"Error generating audio: {e}")
