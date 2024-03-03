# Base Image
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 as base
WORKDIR /home/autodockgpu

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    python3-pip

# Clone AutoDock-GPU from GitHub
RUN git clone https://github.com/ccsb-scripps/AutoDock-GPU.git

# Build stage for AutoDock-GPU
FROM base as autodockgpu_build
WORKDIR /home/autodockgpu/AutoDock-GPU

# Set CUDA PATHS
ENV GPU_INCLUDE_PATH /usr/local/cuda/include
ENV GPU_LIBRARY_PATH /usr/local/cuda/lib64

# Export PATHS
RUN export GPU_INCLUDE_PATH=/usr/local/cuda/include && \
    export GPU_LIBRARY_PATH=/usr/local/cuda/lib64


# Compile AutoDock-GPU with CUDA support
RUN make DEVICE=CUDA NUMWI=128

RUN /home/autodockgpu/AutoDock-GPU/bin/autodock_gpu_128wi

# Runner stage for setting up the environment with Python dependencies
FROM autodockgpu_build as requirements_install
WORKDIR /var/www/server
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Final stage for the application
FROM requirements_install as runner
COPY . .

