FROM python:3.13-slim

# Install dependencies OS (jika diperlukan)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ffmpeg curl && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dulu → biar cache build efisien
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh project
COPY . .

# Expose port Streamlit
EXPOSE 8501

# Jalankan aplikasi
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
