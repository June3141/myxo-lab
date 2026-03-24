# ============================================================
# Stage 1: Install Nix and devbox, then run devbox install
# ============================================================
FROM debian:bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Nix in single-user mode
RUN curl -L https://nixos.org/nix/install | sh -s -- --no-daemon

ENV PATH="/root/.nix-profile/bin:${PATH}"

# Install devbox
RUN curl -fsSL https://get.jetify.com/devbox | bash -s -- -f

WORKDIR /app

COPY devbox.json ./

# Run devbox install to set up A-layer tools
RUN devbox install

# ============================================================
# Stage 2: Final minimal image with devbox environment
# ============================================================
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy Nix store and profiles from builder
COPY --from=builder /nix /nix
COPY --from=builder /root/.nix-profile /root/.nix-profile
COPY --from=builder /root/.local/bin/devbox /usr/local/bin/devbox
COPY --from=builder /app /app

ENV PATH="/root/.nix-profile/bin:${PATH}"

WORKDIR /workspace
