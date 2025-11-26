import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import json

# Page Config
st.set_page_config(page_title="Data Generator", layout="wide")

st.title("🤖 DeepSeek Data Generator")

# Sidebar Configuration
st.sidebar.header("Configuration")
deepseek_key = st.sidebar.text_input("DeepSeek API Key", type="password", value=os.environ.get("DEEPSEEK_API_KEY", ""))

if deepseek_key:
    os.environ["DEEPSEEK_API_KEY"] = deepseek_key

# Constants
st.sidebar.header("File Management")
uploaded_file = st.sidebar.file_uploader("Upload CSV to replace n8n.csv", type=['csv'])

if uploaded_file is not None:
    if st.sidebar.button("💾 Replace Local File"):
        # Save uploaded file to n8n.csv
        with open("n8n.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success("✅ File replaced! Reloading...")
        st.rerun()

# Constants - use uploaded file temporarily if available, otherwise use local n8n.csv
if uploaded_file is not None:
    CSV_FILE = uploaded_file
else:
    CSV_FILE = "n8n.csv"

# Input Parameters
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic/Theme", "Sci-Fi Adventures")
with col2:
    num_rows = st.number_input("Number of Rows", min_value=1, max_value=20, value=5)

def load_existing_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=['row_number', 'index', 'story', 'model', 'aspect_ratio', 'resolution', 'duration', 'number_of_scene', 'status'])

def generate_data(api_key, topic, count):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    system_prompt = """You are a data generator. Generate a JSON object containing a list of items.
    The list should be under the key 'data'.
    Each item must have these fields:
    - story: string (a short creative story about the topic)
    - aspect_ratio: string (e.g., '9:16', '16:9', '1:1')
    - resolution: string (e.g., '480p', '720p', '1080p')
    - duration: integer (duration in seconds, between 2 and 12)
    - number_of_scene: integer (MUST be between 1 and 5, default to 1)
    - status: string (default 'pending')
    - scenes: list of objects, where each object has:
        - title: string (short title of the scene)
        - prompt: string (visual prompt for the scene)
    
    The number of items in 'scenes' MUST match 'number_of_scene'.
    Do NOT include row_number or index in the JSON.
    Output ONLY valid JSON."""
    
    user_prompt = f"Generate {count} rows of data about '{topic}'. Ensure 'scenes' are detailed and match 'number_of_scene'."
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        if 'data' in data:
            df = pd.DataFrame(data['data'])
            
            # Ensure number_of_scene is valid
            if 'number_of_scene' not in df.columns:
                df['number_of_scene'] = 1
            df['number_of_scene'] = df['number_of_scene'].fillna(1).astype(int)
            
            # Ensure aspect_ratio is valid
            if 'aspect_ratio' not in df.columns:
                df['aspect_ratio'] = '9:16'
            df['aspect_ratio'] = df['aspect_ratio'].fillna('9:16')
            
            # Set model to video generation model name
            df['model'] = 'bytedance/seedance/v1/lite/text-to-video'
            
            # Ensure resolution is valid
            if 'resolution' not in df.columns:
                df['resolution'] = '720p'
            df['resolution'] = df['resolution'].fillna('720p')
            
            # Ensure duration is valid
            if 'duration' not in df.columns:
                df['duration'] = 5
            df['duration'] = df['duration'].fillna(5).astype(int)
            
            # Ensure status is valid
            if 'status' not in df.columns:
                df['status'] = 'pending'
            df['status'] = df['status'].fillna('pending')
            
            # Flatten scenes with robust fallback
            for i in range(1, 6):
                df[f'scene_{i}'] = ""
                df[f'scene_detail_{i}'] = ""
            
            for idx, row in df.iterrows():
                scenes = row.get('scenes', [])
                num_scenes = row['number_of_scene']
                
                # If scenes is not a list, try to parse it or default to empty
                if not isinstance(scenes, list):
                    scenes = []
                
                # Fill available scenes
                for i, scene in enumerate(scenes):
                    if i < 5:
                        title = scene.get('title', '')
                        prompt = scene.get('prompt', '')
                        # Fallback if empty
                        if not title: title = f"Scene {i+1}"
                        if not prompt: prompt = f"Visual for scene {i+1}"
                        
                        df.at[idx, f'scene_{i+1}'] = title
                        df.at[idx, f'scene_detail_{i+1}'] = prompt
                
                # If we have fewer scenes than number_of_scene, generate placeholders
                current_scene_count = len(scenes)
                if current_scene_count < num_scenes and current_scene_count < 5:
                    for i in range(current_scene_count, min(num_scenes, 5)):
                        df.at[idx, f'scene_{i+1}'] = f"Scene {i+1} (Auto-filled)"
                        df.at[idx, f'scene_detail_{i+1}'] = f"Scene {i+1} visual description for {row.get('story', 'story')[:20]}..."

            # Drop the scenes column if it exists
            if 'scenes' in df.columns:
                df = df.drop(columns=['scenes'])
                
            return df
        else:
            st.error("Invalid JSON structure received")
            return None
            
    except Exception as e:
        st.error(f"Error generating data: {e}")
        return None

# Main UI
st.subheader("Current Data")
existing_df = load_existing_data()
st.dataframe(existing_df, width='stretch')

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("Generate & Append Data", type="primary"):
        if not deepseek_key:
            st.error("Please provide a DeepSeek API Key in the sidebar.")
        else:
            with st.spinner(f"Generating {num_rows} rows about '{topic}'..."):
                # Calculate start indices
                if not existing_df.empty:
                    try:
                        last_row_num = existing_df['row_number'].max()
                        last_index = existing_df['index'].max()
                        # Handle NaN if file exists but empty columns
                        if pd.isna(last_row_num): last_row_num = 0
                        if pd.isna(last_index): last_index = -1
                    except:
                        last_row_num = 0
                        last_index = -1
                else:
                    last_row_num = 0
                    last_index = -1
                
                new_df = generate_data(deepseek_key, topic, num_rows)
                
                if new_df is not None:
                    # Add sequential numbers
                    new_df['row_number'] = range(int(last_row_num) + 1, int(last_row_num) + 1 + len(new_df))
                    new_df['index'] = range(int(last_index) + 1, int(last_index) + 1 + len(new_df))
                    
                    # Reorder columns to match existing if possible
                    if not existing_df.empty:
                        final_columns = existing_df.columns.tolist()
                        # Ensure new_df has all these columns
                        for col in final_columns:
                            if col not in new_df.columns:
                                new_df[col] = None
                        new_df = new_df[final_columns]
                    
                    # Append and Save
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    updated_df.to_csv(CSV_FILE, index=False)
                    
                    st.success(f"Successfully appended {len(new_df)} rows to {CSV_FILE}!")
                    st.rerun()

with col_btn2:
    if st.button("Fill Missing Data", type="secondary"):
        if not deepseek_key:
            st.error("Please provide a DeepSeek API Key in the sidebar.")
        elif existing_df.empty:
            st.warning("No data to fill.")
        else:
            with st.spinner("Scanning for missing data..."):
                # Identify rows with missing scene data
                rows_to_fix = []
                for idx, row in existing_df.iterrows():
                    # Check if any scene fields are empty
                    has_missing = False
                    for i in range(1, 6):
                        scene_col = f'scene_{i}'
                        prompt_col = f'scene_detail_{i}'
                        if scene_col in row and prompt_col in row:
                            if pd.isna(row[scene_col]) or row[scene_col] == '' or pd.isna(row[prompt_col]) or row[prompt_col] == '':
                                has_missing = True
                                break
                    
                    if has_missing:
                        rows_to_fix.append(idx)
                
                if not rows_to_fix:
                    st.info("No missing data found!")
                else:
                    st.write(f"Found {len(rows_to_fix)} rows with missing data. Filling...")
                    
                    for idx in rows_to_fix:
                        row = existing_df.loc[idx]
                        story = row.get('story', 'Unknown story')
                        num_scenes_val = row.get('number_of_scene', 1)
                        # Handle NaN values
                        if pd.isna(num_scenes_val):
                            num_scenes = 1
                        else:
                            num_scenes = int(num_scenes_val)
                        
                        # Generate scenes for this story
                        client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
                        
                        system_prompt = f"""Generate {num_scenes} scenes for this story. 
                        Return a JSON object with key 'scenes' containing a list of {num_scenes} scene objects.
                        Each scene object must have:
                        - title: short scene title
                        - prompt: visual description for the scene
                        
                        Story: {story}
                        
                        Output ONLY valid JSON."""
                        
                        try:
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": f"Generate {num_scenes} scenes"}
                                ],
                                response_format={ "type": "json_object" },
                                temperature=0.7
                            )
                            
                            content = response.choices[0].message.content
                            data = json.loads(content)
                            
                            if 'scenes' in data and isinstance(data['scenes'], list):
                                scenes = data['scenes']
                                for i, scene in enumerate(scenes[:5]):
                                    scene_col = f'scene_{i+1}'
                                    prompt_col = f'scene_detail_{i+1}'
                                    if scene_col in existing_df.columns and prompt_col in existing_df.columns:
                                        existing_df.at[idx, scene_col] = scene.get('title', f'Scene {i+1}')
                                        existing_df.at[idx, prompt_col] = scene.get('prompt', f'Scene {i+1} description')
                        except Exception as e:
                            st.warning(f"Failed to fill row {idx}: {e}")
                    
                    # Save updated data
                    existing_df.to_csv(CSV_FILE, index=False)
                    st.success(f"Successfully filled {len(rows_to_fix)} rows!")
                    st.rerun()