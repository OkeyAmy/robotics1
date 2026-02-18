# Autonomous Robotics Command Center

Warehouse robotics simulation using Webots, a Node.js backend API, and Python robot controllers. Robots run in a simulated warehouse, report telemetry to the backend, execute pickup/shelf/delivery tasks, and can use optional AI (Gemini) for decisions.

## Project layout

| Directory       | Description |
| --------------- | ----------- |
| **backend/**    | Node.js API and AI server (Express, PostgreSQL, Redis). Main API on port 3000; AI server on port 4000. Handles simulation runs, telemetry, tasks, and metrics. |
| **controllers/**| Webots Python controllers (e.g. warehouse robot, calibration). Run inside the simulation and talk to the backend. |
| **worlds/**     | Webots world files (`.wbt`, `.wbproj`) — the simulation scene. |

## Prerequisites

- **Webots** — for simulation and worlds (e.g. R2024 or compatible).
- **Node.js** (v20+) and **pnpm** — for the backend.
- **Docker** — for PostgreSQL and Redis (see `backend/docker-compose.yml`).
- **Python** (3.x) — for Webots controllers (optional venv in `controllers/`).

## Quick start

1. **Backend:** From the repo root:
   ```bash
   cd backend
   pnpm install
   cp .env.example .env   # edit .env if needed (e.g. GEMINI_API_KEY)
   sudo docker-compose up -d
   node server.js         # API on http://localhost:3000
   ```
   In another terminal, optionally start the AI server: `node ai_server.js` (port 4000).

   On some systems the command may be `docker compose up -d` (no hyphen); you may not need `sudo` if your user is in the `docker` group.

2. **Simulation:** Open the world in `worlds/` with Webots. The warehouse controller talks to the backend at `http://localhost:3000` and the AI server at `http://localhost:4000`.

## Running the simulation

1. Start the backend and (optionally) the AI server as above.
2. Open the project in Webots and load the world from `worlds/`.
3. Run the simulation; controllers will connect to the API and send telemetry and task updates.

## Environment

Backend configuration is via environment variables. Copy `backend/.env.example` to `backend/.env` and set values as needed (e.g. `GEMINI_API_KEY` for AI features). See **backend/README.md** for the full list and API details.
