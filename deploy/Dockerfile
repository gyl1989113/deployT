# 基础镜像，CUDA 12.6 devel 版本
FROM nvidia/cuda:12.6.0-devel-ubuntu20.04

WORKDIR /root

# 设置非交互模式，防止安装时出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    openssh-client \
    cmake \
    build-essential \
    pkg-config \
    libcurl4-openssl-dev \
    zlib1g-dev \
    libssl-dev \
    nvidia-utils-525 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装 Nsight Systems 工具（确保与 CUDA 版本兼容）
ARG NSYS_URL=https://developer.nvidia.com/downloads/assets/tools/secure/nsight-systems/2024_4/
ARG NSYS_PKG=NsightSystems-linux-cli-public-2024.4.1.61-3431596.deb
RUN apt-get update && apt install -y wget libglib2.0-0
RUN wget ${NSYS_URL}${NSYS_PKG} && dpkg -i $NSYS_PKG && rm $NSYS_PKG

# 安装 Rust 和 Cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo 'source $HOME/.cargo/env' >> /root/.bashrc

# 设置环境变量以确保 cargo 可用
ENV PATH="/root/.cargo/bin:${PATH}"

# 安装 CMake >= 3.24
ARG CMAKE_VERSION=3.24.3
RUN wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && chmod +x cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && ./cmake-${CMAKE_VERSION}-linux-x86_64.sh --skip-license --prefix=/usr/local \
    && rm cmake-${CMAKE_VERSION}-linux-x86_64.sh

# 安装 Boost 1.66 或更高版本
ARG BOOST_VERSION=1.82.0
ARG BOOST_VERSION_UNDERSCORE=1_82_0
RUN wget https://archives.boost.io/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz \
    && tar -xzf boost_${BOOST_VERSION_UNDERSCORE}.tar.gz \
    && cd boost_${BOOST_VERSION_UNDERSCORE} \
    && ./bootstrap.sh \
    && ./b2 install --prefix=/usr/local --with=all -j$(nproc) \
    && cd .. \
    && rm -rf boost_${BOOST_VERSION_UNDERSCORE} boost_${BOOST_VERSION_UNDERSCORE}.tar.gz

# 安装 Prometheus-Cpp 库
RUN git clone --branch v0.13.0 https://github.com/jupp0r/prometheus-cpp.git /prometheus-cpp \
    && cd /prometheus-cpp \
    && git submodule update --init --recursive \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install

# 设置 NVML 库的路径
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

RUN mkdir /root/.ssh/