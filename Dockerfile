FROM python:3.11

RUN apt-get update && apt-get install -y \
    build-essential \
    curl
# Get Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN curl https://wasmtime.dev/install.sh -sSf | bash

COPY . /code/wasmtime-py
WORKDIR /code/wasmtime-py
RUN rustup target add wasm32-unknown-unknown wasm32-wasi
RUN cargo install wasm-tools


RUN python ci/download-wasmtime.py
RUN python ci/build-rust.py
RUN pip install -e .[testing]
CMD sleep infinity
