# ============================================================
# Stage 1: Install Nix and devbox, then run devbox install
# ============================================================
FROM debian:bookworm-slim AS nix-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Nix in single-user mode
# Nix 2.34+ requires /nix pre-created and build-users-group disabled in containers
RUN mkdir -p -m 0755 /nix /etc/nix \
    && echo 'build-users-group =' > /etc/nix/nix.conf \
    && curl -fSL https://nixos.org/nix/install -o /tmp/nix-install.sh \
    && sh /tmp/nix-install.sh --no-daemon \
    && rm /tmp/nix-install.sh

ENV PATH="/root/.nix-profile/bin:${PATH}"

# Install devbox
RUN curl -fsSL https://get.jetify.com/devbox | bash -s -- -f

WORKDIR /app

COPY container/devbox.json ./

# Run devbox install to set up A-layer tools
RUN devbox install

# ============================================================
# Stage 2: Build Rust binary
# ============================================================
FROM rust:1.88-slim-bookworm AS rust-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Cache dependencies by building with empty src first
COPY Cargo.toml Cargo.lock rust-toolchain.toml ./
COPY crates/myxo-cli/Cargo.toml crates/myxo-cli/Cargo.toml
COPY crates/myxo-core/Cargo.toml crates/myxo-core/Cargo.toml

RUN mkdir -p crates/myxo-cli/src crates/myxo-core/src \
    && echo 'fn main() {}' > crates/myxo-cli/src/main.rs \
    && echo '' > crates/myxo-core/src/lib.rs \
    && cargo build --release --locked -p myxo-cli \
    && rm -rf crates/

# Copy actual source and build
COPY crates/ crates/
RUN cargo build --release --locked -p myxo-cli

# ============================================================
# Stage 3: Final minimal image with devbox environment + mxl
# ============================================================
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy Nix store and profiles from nix-builder
COPY --from=nix-builder /nix /nix
COPY --from=nix-builder /root/.nix-profile /root/.nix-profile
COPY --from=nix-builder /usr/local/bin/devbox /usr/local/bin/devbox
COPY --from=nix-builder /app /app

# Copy mxl binary from rust-builder
COPY --from=rust-builder /build/target/release/mxl /usr/local/bin/mxl

ENV PATH="/root/.nix-profile/bin:${PATH}"

WORKDIR /workspace
