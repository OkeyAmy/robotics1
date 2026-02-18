# Backend — Autonomous Robotics Command Center

This directory is the **backend** for the Autonomous Robotics Command Center: API and AI server for the warehouse robotics simulation (Version 7 Hackathon).

## What this backend does

- **Simulation runs:** Start and end runs; store scenario and run metadata in PostgreSQL.
- **Telemetry:** Accept high-frequency robot state (position, velocity, battery, sensors) per run; persist to Redis and Postgres.
- **Tasks:** Ingest task creation and completion; link to runs.
- **Metrics:** Expose runs and per-robot metrics for dashboards.
- **Optional AI:** AI server (`ai_server.js`) uses Gemini for decisions when `GEMINI_API_KEY` is set.

**Status:** LIVE — **Base URL:** `http://149.28.125.185`

## Stack

- **Runtime:** Node.js v20 + Express
- **Database:** PostgreSQL 15 (relational data)
- **Cache:** Redis 7 (real-time telemetry)
- **Infrastructure:** Docker Compose (+ Vultr VPS for production)

## API Endpoints

### Health

- `GET /` — Health check; returns status and system name.

### Simulation control

- `POST /api/simulations/start` — Start a simulation run. Body: `{ "scenario_id": "UUID", "scenario_name": "string" }`. Response: `{ "run_id": "UUID", "status": "started" }`.
- `POST /api/simulations/end/:run_id` — End a run; optional body: `final_score`, `total_tasks`, etc.

### Telemetry and tasks

- `POST /api/telemetry/:run_id` — Robot pushes state (position, velocity, battery, sensors). Stored in Redis and Postgres.
- `GET /api/telemetry/:run_id/latest` — Latest telemetry for a run.
- `POST /api/tasks/:run_id` — Submit task data for a run.
- `POST /api/tasks/:task_id/complete` — Mark a task complete.

### Metrics

- `GET /api/metrics/runs` — List recent runs and scores.
- `GET /api/metrics/robots/:run_id` — Per-robot metrics for a run.
- `POST /api/metrics/:run_id` — Submit or update metrics for a run.

### AI (AI server on port 4000)

- `POST /api/ai/decisions/:run_id` — Request AI-driven decisions (handled by `ai_server.js`).

## Environment variables

Copy `.env.example` to `.env` and set as needed. Main variables:

| Variable        | Description |
| --------------- | ----------- |
| `PORT`          | Server port (default 3000). |
| `PGUSER`, `PGHOST`, `PGDATABASE`, `PGPASSWORD`, `PGPORT` | PostgreSQL connection (defaults match `docker-compose.yml`). |
| `REDIS_URL`     | Redis URL (optional; app defaults to localhost:6379). |
| `GEMINI_API_KEY`| Optional; required for AI features in `ai_server.js`. |

## Local setup (run order)

1. **Copy environment:** `cp .env.example .env` and fill in values (e.g. `GEMINI_API_KEY` for AI).

2. **Install dependencies:**
   ```bash
   pnpm install
   ```

3. **Start database and Redis (Docker):** From the `backend/` directory:
   ```bash
   sudo docker-compose up -d
   ```
   `sudo` may be required depending on your Docker setup. On some systems the command is `docker compose up -d` (no hyphen).

4. **Initialize schema:** Run the contents of `init_db.sql` in your Postgres client (e.g. `psql` or GUI).

5. **Start main server:**
   ```bash
   node server.js
   ```
   API is at `http://localhost:3000`.

6. **Start AI server (optional):** In another terminal, from `backend/`:
   ```bash
   node ai_server.js
   ```
   AI server listens on port 4000.
