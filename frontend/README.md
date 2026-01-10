# JobReels Frontend

Minimal Expo React Native app that displays health status for backend services.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure service URLs:**
   
   Edit `src/config.js` and update the base URLs:

   **For local development:**
   - Use your laptop's local IP address (not `localhost`)
   - Find your IP: 
     - macOS/Linux: `ifconfig` or `ip addr`
     - Windows: `ipconfig`
   - Example: `http://192.168.1.100:8000`

   **For production (Vultr):**
   - Use your Vultr server's public IP
   - Example: `http://YOUR_VULTR_IP:8000`
   - For headless/video, use the same IP (they're exposed in dev mode)

   **For Tailscale:**
   - Use Tailscale DNS names if services are accessed via Tailscale
   - Example: `http://vultr-node:8000`

3. **Start Expo:**
   ```bash
   npx expo start --tunnel
   ```

   The `--tunnel` flag allows you to test on a physical device even when your laptop and phone are on different networks.

4. **Test with Expo Go:**
   - Install Expo Go app on your phone (iOS or Android)
   - Scan the QR code displayed in the terminal
   - The app will load and display health status for all services

## Usage

- **Refresh Button**: Tap to check health status of all three services (backend, headless, video)
- **Status Indicators**: 
  - Green dot = Service is healthy (`{"status":"ok"}`)
  - Red dot = Connection error or service unavailable
  - Gray = Not checked yet

## Development

- **Entry point**: `App.js`
- **Configuration**: `src/config.js`
- **Test locally**: Make sure services are running (`docker compose up`) and use your laptop's IP in config
- **Test production**: Update config to point at your Vultr IP

## Troubleshooting

**Can't connect to services:**
- Verify services are running: `docker compose ps`
- Check your IP address is correct in `src/config.js`
- Ensure you're using your local IP (not `localhost` or `127.0.0.1`) when testing on a physical device
- If using tunnel mode, ensure ports 8000-8002 are accessible from your network

**Expo Go can't load app:**
- Make sure you're using `--tunnel` flag
- Check your phone and laptop are connected to internet
- Try restarting Expo: `npx expo start --clear --tunnel`