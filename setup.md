You are editing a brand-new repo from scratch. Create an initial scaffold that is optimized for:
- MongoDB Atlas as the ONLY database (no local Mongo container)
- Deployment to a single Vultr VM using Docker Compose
- Optional Tailscale integration to avoid opening multiple ports (keep internal services private)
- A minimal Expo frontend that can be tested with Expo Go

Keep everything minimal, working, and hackathon-ready. No extra endpoints or business logic.

==================================================
1) FOLDER STRUCTURE
==================================================

/
  docker-compose.yml
  docker-compose.prod.yml
  .env.example  
  README.md

  frontend/
    package.json
    app.json
    App.js
    src/
      config.js
    README.md

  backend/
    Dockerfile
    requirements.txt
    app/
      __init__.py
      main.py

  services/
    headless/
      Dockerfile
      requirements.txt
      app/
        __init__.py
        main.py
    video/
      Dockerfile
      requirements.txt
      app/
        __init__.py
        main.py

  scripts/
    vultr_setup.sh
    tailscale_setup.sh

==================================================
2) FASTAPI SERVICES (ONLY /health)
==================================================

backend, services/headless, services/video:
- Python 3.11-slim
- FastAPI + uvicorn
- Only endpoint: GET /health -> {"status":"ok"}
- Read env vars (even if unused yet):
  - MONGODB_URI (MongoDB Atlas connection string)
  - MONGODB_DB
- No other routes or logic

requirements.txt for each python service:
- fastapi
- uvicorn[standard]
- motor
- pymongo

(Do not actually connect to DB yet; just load env vars.)

==================================================
3) DOCKERFILES
==================================================

For each python service:
- python:3.11-slim
- WORKDIR /app
- install requirements
- copy app/
- CMD runs uvicorn app.main:app on:
  - backend: 8000
  - headless: 8001
  - video: 8002
Bind host 0.0.0.0

==================================================
4) DOCKER COMPOSE (DEV + PROD)
==================================================

Goal: make local dev simple, but assume Atlas for DB always.

docker-compose.yml (dev):
- Runs backend, headless, video
- Exposes ports 8000, 8001, 8002 to localhost for convenience
- Uses env_file: .env
- No mongo container

docker-compose.prod.yml (prod on Vultr):
- Runs backend, headless, video
- Only exposes backend publicly on 8000
- headless and video should NOT be published publicly (no ports section or bind to 127.0.0.1)
- Use env_file: .env
- Include restart policy (unless-stopped)

All services must receive:
- MONGODB_URI=${MONGODB_URI}
- MONGODB_DB=${MONGODB_DB}

==================================================
5) TAILSCALE INTEGRATION (OPTIONAL BUT SUPPORTED)
==================================================

Add notes + optional compose blocks to make it easy:
- Provide a Tailscale sidecar container that can be enabled in prod to create a tailnet node on the VM.
- Document two modes:
  A) Simple mode: expose backend on 8000 publicly (no Tailscale needed)
  B) Tailscale mode: keep backend/headless/video private and access them over Tailscale, and optionally use Funnel for a single public endpoint later.

Implementation requirements:
- In docker-compose.prod.yml, include an optional service "tailscale" (commented or profile-based) using the official tailscale image.
- Use TS_AUTHKEY from env for non-interactive login.
- Document that TS_AUTHKEY must be ephemeral and not committed.
- For simplicity, do not implement Funnel commands; just lay groundwork + docs.

==================================================
6) EXPO FRONTEND (MINIMAL + EXPO GO)
==================================================

Create a minimal Expo app (JavaScript) that:
- Runs with:
  - npm install
  - npx expo start --tunnel
- Shows title (e.g., JobReels)
- Shows health status for:
  - backend /health
  - headless /health
  - video /health
- Has a Refresh button
- Uses src/config.js exporting:
  - BASE_URL_BACKEND
  - BASE_URL_HEADLESS
  - BASE_URL_VIDEO
Default to placeholders:
  http://YOUR_SERVER_OR_IP:8000
  http://YOUR_SERVER_OR_IP:8001
  http://YOUR_SERVER_OR_IP:8002

frontend/README.md must explain:
- For local dev: use your laptop IP
- For prod: use Vultr public IP OR a Tailscale DNS name (if using Tailscale)
- Run Expo Go with tunnel

==================================================
7) SCRIPTS (QUALITY OF LIFE)
==================================================

scripts/vultr_setup.sh:
- installs docker + docker compose plugin on Ubuntu
- enables docker
- prints next steps (clone repo, create .env, docker compose -f docker-compose.prod.yml up -d --build)

scripts/tailscale_setup.sh:
- placeholder instructions for:
  - creating TS_AUTHKEY
  - setting it in .env
  - enabling tailscale service in compose
(Keep it simple; no interactive prompts required.)

==================================================
8) .env.example (MUST EMPHASIZE ATLAS)
==================================================

MONGODB_URI=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=app
TS_AUTHKEY=tskey-auth-REPLACE_ME   (optional; leave blank if not using)

==================================================
9) ROOT README.md
==================================================

Include:
- Purpose: Atlas is the only DB; Vultr deployment; optional Tailscale
- Local dev:
  - cp .env.example .env (fill Atlas URI)
  - docker compose up --build
  - curl localhost:8000/health etc.
- Vultr deployment:
  - run scripts/vultr_setup.sh
  - set .env with Atlas URI
  - docker compose -f docker-compose.prod.yml up -d --build
- Tailscale (optional):
  - explain that headless/video can be kept private; backend can be private too
  - mention TS_AUTHKEY
- Frontend:
  - cd frontend; npm install; npx expo start --tunnel
  - update frontend/src/config.js to point at Vultr IP or Tailscale DNS

==================================================
10) FINAL CHECKS
==================================================

Ensure:
- docker compose up --build runs backend/headless/video and all /health return {"status":"ok"}
- Prod compose only exposes backend publicly by default
- No local Mongo container exists anywhere
- Everything is minimal and clean

Create all files with correct contents.
