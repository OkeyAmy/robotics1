-- -- Drop tables if they exist (for clean reset)
-- DROP TABLE IF EXISTS ai_decisions;
-- DROP TABLE IF EXISTS telemetry_logs;
-- DROP TABLE IF EXISTS simulation_runs;
-- DROP TABLE IF EXISTS scenarios;
-- DROP TABLE IF EXISTS users;

-- -- Create Users Table
-- CREATE TABLE users (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     username VARCHAR(50) UNIQUE NOT NULL,
--     api_key VARCHAR(100) UNIQUE NOT NULL,
--     role VARCHAR(20) DEFAULT 'viewer'
-- );

-- -- Create Scenarios
-- CREATE TABLE scenarios (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     name VARCHAR(100) NOT NULL,
--     config_json JSONB NOT NULL,
--     difficulty INT DEFAULT 1
-- );

-- -- Create Simulation Runs
-- CREATE TABLE simulation_runs (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     scenario_id UUID REFERENCES scenarios(id),
--     status VARCHAR(20) DEFAULT 'pending',
--     start_time TIMESTAMP DEFAULT NOW(),
--     end_time TIMESTAMP,
--     final_score FLOAT
-- );

-- -- Create Telemetry Logs (Time-Series)
-- CREATE TABLE telemetry_logs (
--     id BIGSERIAL PRIMARY KEY,
--     run_id UUID REFERENCES simulation_runs(id),
--     timestamp TIMESTAMP DEFAULT NOW(),
--     position_x FLOAT,
--     position_y FLOAT,
--     velocity FLOAT,
--     battery_level FLOAT,
--     sensor_data JSONB
-- );
-- CREATE INDEX idx_telemetry_run_id ON telemetry_logs(run_id);
-- CREATE INDEX idx_telemetry_timestamp ON telemetry_logs(timestamp);

-- -- Create AI Decisions
-- CREATE TABLE ai_decisions (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     run_id UUID REFERENCES simulation_runs(id),
--     timestamp TIMESTAMP DEFAULT NOW(),
--     input_state JSONB,
--     decision_output JSONB,
--     latency_ms INT
-- );


-- Drop tables if they exist (for clean reset)
DROP TABLE IF EXISTS ai_decisions;
DROP TABLE IF EXISTS robot_telemetry;
DROP TABLE IF EXISTS robot_tasks;
DROP TABLE IF EXISTS simulation_runs;
DROP TABLE IF EXISTS scenarios;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS robot_metrics;

-- Create Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer'
);

-- Create Scenarios
CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    difficulty INT DEFAULT 1
);

-- Create Simulation Runs
CREATE TABLE simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id),
    status VARCHAR(20) DEFAULT 'pending',
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    final_score FLOAT,
    total_tasks_completed INT DEFAULT 0,
    total_energy_used FLOAT DEFAULT 0.0,
    total_failures INT DEFAULT 0
);

-- ============================================
-- WAREHOUSE-SPECIFIC TABLES
-- ============================================

-- Robot Telemetry (Real-time Position & Status)
CREATE TABLE robot_telemetry (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES simulation_runs(id),
    robot_id VARCHAR(50) NOT NULL,
    robot_icon VARCHAR(10),
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Position (GPS coordinates from Webots)
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    position_z FLOAT,
    
    -- Robot State
    battery_level FLOAT NOT NULL,
    task_state VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    carrying_item BOOLEAN DEFAULT FALSE,
    movement_state VARCHAR(20),
    
    -- Task Info
    current_pickup VARCHAR(50),
    current_shelf VARCHAR(50),
    current_delivery VARCHAR(50),
    
    -- Metrics
    tasks_completed INT DEFAULT 0,
    total_energy_used FLOAT DEFAULT 0.0,
    
    -- Raw sensor data
    sensor_data JSONB
);

-- Indexes for fast queries
CREATE INDEX idx_telemetry_run_id ON robot_telemetry(run_id);
CREATE INDEX idx_telemetry_robot_id ON robot_telemetry(robot_id);
CREATE INDEX idx_telemetry_timestamp ON robot_telemetry(timestamp);

-- Robot Tasks (Task Assignments)
CREATE TABLE robot_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES simulation_runs(id),
    robot_id VARCHAR(50) NOT NULL,
    task_number INT NOT NULL,
    
    -- Task Details
    pickup_zone VARCHAR(50),
    shelf_zone VARCHAR(50),
    delivery_zone VARCHAR(50),
    
    -- Timing
    assigned_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Performance
    completion_time FLOAT,
    energy_used FLOAT,
    status VARCHAR(20) DEFAULT 'assigned',
    
    -- AI Decision
    ai_decision JSONB
);

-- Robot Performance Metrics (Per Task)
CREATE TABLE robot_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES simulation_runs(id),
    robot_id VARCHAR(50) NOT NULL,
    task_number INT NOT NULL,
    
    completion_time FLOAT,
    energy_used FLOAT,
    
    pickup_zone VARCHAR(50),
    shelf_zone VARCHAR(50),
    delivery_zone VARCHAR(50),
    
    timestamp TIMESTAMP DEFAULT NOW()
);

-- AI Decisions (Learning Loop)
CREATE TABLE ai_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES simulation_runs(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Input State
    robot_battery FLOAT,
    available_robots INT,
    pending_tasks INT,
    
    -- Decision Output
    decision_type VARCHAR(50),
    assigned_robot VARCHAR(50),
    assigned_route JSONB,
    
    -- Performance
    confidence FLOAT,
    latency_ms INT,
    
    input_state JSONB,
    decision_output JSONB
);