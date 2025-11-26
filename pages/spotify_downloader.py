import streamlit as st
import subprocess
import shutil
import os
import glob

def check_ffmpeg():
    """Check if ffmpeg is installed and available in PATH.
    Also checks local directories and updates PATH if found.
    """
    # Check if ffmpeg is already in PATH
    if shutil.which("ffmpeg"):
        return True
        
    # Check local directories
    current_dir = os.getcwd()
    possible_paths = [
        os.path.join(current_dir, "ffmpeg.exe"),
        os.path.join(current_dir, ".spotdl", "ffmpeg.exe"),
        os.path.join(os.path.expanduser("~"), ".spotdl", "ffmpeg.exe"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            # Add directory to PATH
            ffmpeg_dir = os.path.dirname(path)
            os.environ["PATH"] += os.pathsep + ffmpeg_dir
            return True
            
    return False

st.title("Spotify Downloader")

if not check_ffmpeg():
    st.error("⚠️ FFmpeg is not installed or not found in PATH. Please install FFmpeg to use this downloader.")
    st.info("You can download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or install it using a package manager (e.g., `winget install ffmpeg`).")
else:
    st.write("Enter a Spotify URL (Song, Album, or Playlist) to download.")

    spotify_url = st.text_input("Spotify URL", placeholder="https://open.spotify.com/track/...")

    if st.button("Download"):
        if spotify_url:
            try:
                with st.spinner("Downloading... This may take a while depending on the playlist size."):
                    # Create a downloads directory if it doesn't exist
                    download_dir = "downloads"
                    os.makedirs(download_dir, exist_ok=True)

                    # Run spotdl command
                    # We run it in the downloads directory so files are saved there
                    command = ["spotdl", spotify_url]
                    
                    process = subprocess.Popen(
                        command,
                        cwd=download_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    
                    # Stream output to UI
                    output_container = st.empty()
                    logs = []
                    
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            logs.append(output.strip())
                            # Update the last few lines of logs
                            output_container.code("\n".join(logs[-10:]))
                            
                    rc = process.poll()
                    
                    if rc == 0:
                        st.success("Download completed successfully!")
                        
                        # Find the most recently created mp3 file
                        list_of_files = glob.glob(os.path.join(download_dir, '*.mp3'))
                        if list_of_files:
                            latest_file = max(list_of_files, key=os.path.getctime)
                            file_name = os.path.splitext(os.path.basename(latest_file))[0]
                            
                            st.audio(latest_file, format="audio/mp3")
                            
                            with open(latest_file, "rb") as f:
                                st.download_button(
                                    label=f"Download {file_name}",
                                    data=f,
                                    file_name=f"{file_name}.mp3",
                                    mime="audio/mp3",
                                ) 
                    else:
                        st.error("An error occurred during download. See logs above for details.")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.warning("Please enter a Spotify URL.")
