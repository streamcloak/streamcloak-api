# StreamCloak API

**License:** This project is licensed under **CC BY-NC-SA 4.0**.

- ✅ **Free for personal/private use:** You can build this yourself at home.
- ❌ **Commercial use strictly prohibited:** You may not sell devices running this software or use it for business purposes without explicit permission.

## Overview
This repository contains the FastAPI backend service for the StreamCloak VPN Box.
It acts as the central control endpoint, serving as the bridge between the user interface (Mobile/Web App) and the underlying Linux operating system.

## How it Works
The application exposes an HTTP API that allows the client app to trigger system-level operations on the device. Instead of direct SSH access, the app sends requests to this endpoint to manage settings securely.

## Tech Stack
- **Language:** Python 3
- **Framework:** FastAPI
- **Server:** Uvicorn
