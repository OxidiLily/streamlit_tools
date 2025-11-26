import streamlit as st
import os
import glob

st.title("Music Player")

# Define the downloads directory
DOWNLOADS_DIR = "downloads"

# Ensure the directory exists
if not os.path.exists(DOWNLOADS_DIR):
    st.error(f"Directory '{DOWNLOADS_DIR}' not found. Please download some music first.")
else:
    # Get list of mp3 files
    mp3_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp3"))
    
    if not mp3_files:
        st.warning("No MP3 files found in the downloads folder.")
    else:
        # Extract just the filenames for the selectbox
        file_names = [os.path.basename(f) for f in mp3_files]
        
        # Let user select a file
        selected_file = st.selectbox("Select a song to play", file_names)
        
        if selected_file:
            file_path = os.path.join(DOWNLOADS_DIR, selected_file)
            
            # Display audio player
            st.write(f"**Now Playing:** {selected_file}")
            st.audio(file_path, format='audio/mp3')
            
            # Create columns for buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Add a download button for the selected file
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="Download MP3",
                        data=f,
                        file_name=selected_file,
                        mime="audio/mp3"
                    )
            
            with col2:
                # Add delete button
                if st.button("Delete File", type="primary", key="delete_btn"):
                    try:
                        os.remove(file_path)
                        st.success(f"Deleted {selected_file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {e}")