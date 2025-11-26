# Face-Matcher GPU Dockerfile
# ArcFace-based facial biometrics with CUDA/ONNX Runtime GPU support
# Optimized for NVIDIA RTX 3050 (6GB VRAM)

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONIOENCODING=UTF-8 \
  CUDA_HOME=/usr/local/cuda \
  PATH=/usr/local/cuda/bin:$PATH \
  LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3.10 \
  python3.10-venv \
  python3-pip \
  python3.10-dev \
  build-essential \
  cmake \
  git \
  wget \
  curl \
  libgl1-mesa-glx \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender-dev \
  libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
  && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Create application directory
WORKDIR /app

# Copy requirements first for layer caching
COPY face-matcher/pyproject.toml /app/

# Install Python dependencies with ONNX Runtime GPU
RUN python -m pip install --upgrade pip setuptools wheel && \
  python -m pip install \
  onnxruntime-gpu==1.16.3 \
  numpy>=1.24.0 \
  pillow>=10.0.0 \
  opencv-python-headless>=4.8.0 \
  faiss-gpu \
  pydantic>=2.0.0 \
  pyyaml>=6.0 \
  httpx>=0.24.0 \
  mcp>=1.0.0

# Copy Face-Matcher source code
COPY face-matcher/src /app/src
COPY face-matcher/config /app/config

# Create models directory for downloaded models
RUN mkdir -p /app/models /app/data

# Download ArcFace model (ResNet100 - InsightFace)
RUN python -c "import urllib.request; \
  urllib.request.urlretrieve( \
  'https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip', \
  '/app/models/buffalo_l.zip')" && \
  cd /app/models && \
  python -c "import zipfile; zipfile.ZipFile('buffalo_l.zip').extractall('.')" && \
  rm buffalo_l.zip

# Set PYTHONPATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import onnxruntime as ort; print('GPU:', 'CUDAExecutionProvider' in ort.get_available_providers())"

# Default command - run MCP server
CMD ["python", "-m", "mcp_server.biometrics_server"]

# Expose port for HTTP transport (if enabled)
EXPOSE 8080
