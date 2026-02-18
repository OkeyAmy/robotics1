# Backend — Autonomous Robotics Command Center

This directory is the **backend** for the Autonomous Robotics Command Center: high-performance API and AI server for the warehouse robotics simulation, built for the Version 7 Hackathon.

## 🚀 status: LIVE
**Base URL:** `http://149.28.125.185`

## 🏗 Stack
*   **Runtime:** Node.js v20 + Express
*   **Database:** PostgreSQL 15 (Relational Data)
*   **Cache:** Redis 7 (Real-time Telemetry)
*   **Infrastructure:** Docker Compose + Vultr VPS

## 🔌 API Endpoints

### 1. Simulation Control
*   `POST /api/simulations/start`
    *   **Description:** Initialize a new simulation run.
    *   **Body:** `{ "scenario_id": "UUID", "username": "string" }`
    *   **Response:** `{ "run_id": "UUID", "status": "started" }`

### 2. Robot Telemetry Stream (High Frequency)
*   `POST /api/telemetry/:run_id`
    *   **Description:** Robot pushes state (Position, Velocity, Sensors). Autosaved to Redis & Postgres.
    *   **Body:** `{ "x": float, "y": float, "velocity": float, "battery": float, "sensors": {} }`

### 3. Dashboard Metrics
*   `GET /api/metrics/runs`
    *   **Description:** Fetch recent simulation runs and scores.

## 🛠 Local Setup (For Developers)

1.  **Copy environment template:** Copy `.env.example` to `.env` and fill in any required values (e.g. `GEMINI_API_KEY` for AI features).

2.  **Install Dependencies:**
    ```bash
    pnpm install
    ```

3.  **Start Database (Docker):**
    ```bash
    docker compose up -d
    ```

4.  **Initialize Schema:** Run the contents of `init_db.sql` in your Postgres console.

5.  **Start Server:**
    ```bash
    node server.js
    ```
    Start the AI server separately (e.g. `node ai_server.js`) if using Gemini.
