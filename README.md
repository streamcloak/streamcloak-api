# StreamCloak API

**License:** This project is licensed under **CC BY-NC-SA 4.0**.

- ✅ **Free for personal/private use:** You can build this yourself at home.
- ❌ **Commercial use strictly prohibited:** You may not sell devices running this software or use it for business purposes without explicit permission.

## Overview
This repository contains the FastAPI backend service for the StreamCloak VPN Box.
It acts as the central control endpoint, serving as the bridge between the user interface (Mobile/Web App) and the 
underlying Linux operating system.

## How it Works
The application exposes an HTTP API that allows the client app to trigger system-level operations on the device. 
Instead of direct SSH access, the app sends requests to this endpoint to manage settings securely.

## Tech Stack
- **Language:** Python 3
- **Framework:** FastAPI
- **Server:** Uvicorn

---

## ⚠️ System Integration & Architectural Constraints
**Please Note:** This application acts as the control plane for the **StreamCloak VPN Box**. It is strictly designed to 
execute on a dedicated Single Board Computer (e.g., Raspberry Pi) running **Debian 12+** / **Raspberry Pi OS**.
The backend relies heavily on specific low-level system configurations and hardware interfaces, including but 
not limited to:

- **Network Interfaces:** Specific management of wlan0 (AP mode), eth0, and tun0 (VPN tunnel).
- **System Services:** Direct interaction with hostapd, pihole-FTL, openvpn, and iptables / nftables.
- **Routing:** Modification of policy-based routing tables and IP forwarding.

Running this application in a standard development environment (e.g., macOS, Windows, or a generic Linux desktop) will 
result in functional errors when invoking system-level commands.

A separate repository containing the full OS image build scripts and network infrastructure setup will be linked here 
soon.

---

## Installation

1. Clone the Repository
    ```bash
    git clone https://github.com/streamcloak/streamcloak-api.git /var/www/backend
    cd /var/www/backend
    ```

2. Install uv (if not installed)
The project relies on uv for dependency management.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    ```

3. Install Dependencies
Sync the environment using the lockfile to ensure exact reproduction of the production environment.
    ```bash
    # Creates a .venv and installs dependencies defined in uv.lock
    uv sync --frozen --no-dev --python /usr/bin/python3
    ```

4. Configuration
    Copy the example environment file and configure the secrets.
    ```bash
    cp .env.example .env
    nano .env
    ```
    **Required settings:**
    - `SECRET_KEY`: Generate a secure random string (e.g., `openssl rand -hex 32`).
    - `DEVICE_ID`: Unique identifier for the VPN Box.
    - `DEVICE_PASSWORD`: Authenticated client password.
    - `PIHOLE_PASSWORD`: Access token for Pi-hole integration.
