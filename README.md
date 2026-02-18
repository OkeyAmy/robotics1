# Autonomous Robotics Command Center

Warehouse robotics simulation with Webots, a Node.js backend API, and Python robot controllers.

## Project layout

| Directory    | Description |
| ----------- | ------------ |
| **backend/** | Node.js API and AI server (Express, PostgreSQL, Redis). Main API on port 3000; AI server on 4000. |
| **controllers/** | Webots Python controllers (e.g. warehouse robot, calibration). |
| **worlds/** | Webots world files (`.wbt`, `.wbproj`). |

## Prerequisites

- **Webots** — for simulation and worlds
- **Node.js** (v20+) and **pnpm** — for the backend
- **Docker** — for PostgreSQL and Redis (see `backend/docker-compose.yml`)
- **Python** (3.x) — for Webots controllers (optional venv in `controllers/`)

## Quick start

1. **Backend:** From the repo root:
   ```bash
   cd backend
   pnpm install
   cp .env.example .env   # edit .env if needed (e.g. GEMINI_API_KEY)
   docker compose up -d
   node server.js        # API on http://localhost:3000
   ```
   In another terminal, optionally start the AI server: `node ai_server.js` (port 4000).

2. **Simulation:** Open the world in `worlds/` with Webots. The warehouse controller talks to the backend at `http://localhost:3000` and the AI server at `http://localhost:4000`.

See **backend/README.md** for API endpoints and local setup details.
