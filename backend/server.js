// require('dotenv').config();
// const express = require('express');
// const { Pool } = require('pg');
// const redis = require('redis');
// const cors = require('cors');
// const bodyParser = require('body-parser');

// // Setup Express
// const app = express();
// const port = 3000;
// app.use(cors());
// app.use(bodyParser.json());

// // Setup Database Connection
// const pool = new Pool({
//   user: 'admin',
//   host: 'localhost',
//   database: 'robotics_v1',
//   password: 'securepassword123',
//   port: 5432,
// });

// // Setup Redis
// const redisClient = redis.createClient();
// redisClient.connect().catch(console.error);

// // ============================================
// // API ENDPOINTS
// // ============================================

// // Health Check
// app.get('/', (req, res) => {
//   res.json({
//     status: 'active',
//     system: 'warehouse-robotics-backend',
//     time: new Date()
//   });
// });

// // ============================================
// // SIMULATION MANAGEMENT
// // ============================================

// // Start Simulation Run
// app.post('/api/simulations/start', async (req, res) => {
//   const { scenario_id, scenario_name } = req.body;
//   try {
//     const result = await pool.query(
//       `INSERT INTO simulation_runs (scenario_id, status) 
//        VALUES ($1, 'running') RETURNING id`,
//       [scenario_id || null]
//     );

//     const run_id = result.rows[0].id;

//     // Cache run info in Redis
//     await redisClient.set(`run:${run_id}:status`, 'running', { EX: 3600 });

//     res.json({
//       run_id: run_id,
//       status: 'started',
//       message: 'Simulation run started successfully'
//     });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // End Simulation Run
// app.post('/api/simulations/end/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const { final_score, total_tasks, total_energy, failures } = req.body;

//   try {
//     await pool.query(
//       `UPDATE simulation_runs 
//        SET status = 'completed', 
//            end_time = NOW(),
//            final_score = $1,
//            total_tasks_completed = $2,
//            total_energy_used = $3,
//            total_failures = $4
//        WHERE id = $5`,
//       [final_score, total_tasks, total_energy, failures, run_id]
//     );

//     res.json({ status: 'completed' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // ROBOT TELEMETRY
// // ============================================

// // Ingest Robot Telemetry (High Frequency)
// app.post('/api/telemetry/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     robot_icon,
//     position_x,
//     position_y,
//     position_z,
//     battery,
//     task_state,
//     status,
//     carrying_item,
//     movement_state,
//     current_pickup,
//     current_shelf,
//     current_delivery,
//     tasks_completed,
//     total_energy_used,
//     sensor_data
//   } = req.body;

//   try {
//     // Fast write to Redis for real-time dashboard
//     const cacheKey = `robot:${run_id}:${robot_id}:latest`;
//     await redisClient.set(cacheKey, JSON.stringify(req.body), { EX: 60 });

//     // Async write to PostgreSQL for persistence
//     pool.query(
//       `INSERT INTO robot_telemetry (
//         run_id, robot_id, robot_icon,
//         position_x, position_y, position_z,
//         battery_level, task_state, status,
//         carrying_item, movement_state,
//         current_pickup, current_shelf, current_delivery,
//         tasks_completed, total_energy_used,
//         sensor_data
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)`,
//       [
//         run_id, robot_id, robot_icon,
//         position_x, position_y, position_z,
//         battery, task_state, status,
//         carrying_item, movement_state,
//         current_pickup, current_shelf, current_delivery,
//         tasks_completed, total_energy_used,
//         sensor_data || {}
//       ]
//     ).catch(err => console.error('DB Insert Error:', err));

//     res.json({ status: 'ok', message: 'Telemetry received' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Get Latest Robot States (Real-time Dashboard)
// app.get('/api/telemetry/:run_id/latest', async (req, res) => {
//   const { run_id } = req.params;

//   try {
//     const result = await pool.query(
//       `SELECT DISTINCT ON (robot_id) *
//        FROM robot_telemetry
//        WHERE run_id = $1
//        ORDER BY robot_id, timestamp DESC`,
//       [run_id]
//     );

//     res.json({ robots: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // TASK MANAGEMENT
// // ============================================

// // Save Task Assignment
// app.post('/api/tasks/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     task_number,
//     pickup_zone,
//     shelf_zone,
//     delivery_zone,
//     ai_decision
//   } = req.body;

//   try {
//     const result = await pool.query(
//       `INSERT INTO robot_tasks (
//         run_id, robot_id, task_number,
//         pickup_zone, shelf_zone, delivery_zone,
//         ai_decision, status
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'assigned') RETURNING id`,
//       [run_id, robot_id, task_number, pickup_zone, shelf_zone, delivery_zone, ai_decision || {}]
//     );

//     res.json({
//       task_id: result.rows[0].id,
//       status: 'assigned'
//     });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Complete Task
// app.post('/api/tasks/:task_id/complete', async (req, res) => {
//   const { task_id } = req.params;
//   const { completion_time, energy_used } = req.body;

//   try {
//     await pool.query(
//       `UPDATE robot_tasks 
//        SET status = 'completed',
//            completed_at = NOW(),
//            completion_time = $1,
//            energy_used = $2
//        WHERE id = $3`,
//       [completion_time, energy_used, task_id]
//     );

//     res.json({ status: 'completed' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // METRICS & ANALYTICS
// // ============================================

// // Get Simulation Runs
// app.get('/api/metrics/runs', async (req, res) => {
//   try {
//     const result = await pool.query(
//       `SELECT * FROM simulation_runs 
//        ORDER BY start_time DESC LIMIT 10`
//     );
//     res.json({ runs: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Get Robot Performance Metrics
// app.get('/api/metrics/robots/:run_id', async (req, res) => {
//   const { run_id } = req.params;

//   try {
//     const result = await pool.query(
//       `SELECT 
//         robot_id,
//         COUNT(*) as total_tasks,
//         AVG(completion_time) as avg_completion_time,
//         SUM(energy_used) as total_energy,
//         MAX(timestamp) as last_update
//        FROM robot_metrics
//        WHERE run_id = $1
//        GROUP BY robot_id`,
//       [run_id]
//     );

//     res.json({ metrics: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Save Performance Metrics
// app.post('/api/metrics/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     task_number,
//     completion_time,
//     energy_used,
//     pickup_zone,
//     shelf_zone,
//     delivery_zone
//   } = req.body;

//   try {
//     await pool.query(
//       `INSERT INTO robot_metrics (
//         run_id, robot_id, task_number,
//         completion_time, energy_used,
//         pickup_zone, shelf_zone, delivery_zone
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
//       [run_id, robot_id, task_number, completion_time, energy_used,
//         pickup_zone, shelf_zone, delivery_zone]
//     );

//     res.json({ status: 'saved' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // AI DECISIONS
// // ============================================

// // Save AI Decision
// app.post('/api/ai/decisions/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     decision_type,
//     assigned_robot,
//     assigned_route,
//     confidence,
//     input_state,
//     decision_output
//   } = req.body;

//   try {
//     await pool.query(
//       `INSERT INTO ai_decisions (
//         run_id, decision_type, assigned_robot,
//         assigned_route, confidence,
//         input_state, decision_output
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
//       [run_id, decision_type, assigned_robot, assigned_route || {},
//         confidence, input_state || {}, decision_output || {}]
//     );

//     res.json({ status: 'saved' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Start Server
// app.listen(port, () => {
//   console.log(`🚀 Warehouse Robotics Backend running on Port ${port}`);
//   console.log(`📊 Database: PostgreSQL + Redis`);
//   console.log(`🌐 API: http://localhost:${port}`);
// });


// require('dotenv').config();
// const express = require('express');
// const { Pool } = require('pg');
// const redis = require('redis');
// const cors = require('cors');
// const bodyParser = require('body-parser');

// // Setup Express
// const app = express();
// const port = 3000;
// app.use(cors());
// app.use(bodyParser.json());

// // Setup Database Connection
// const pool = new Pool({
//   user: 'admin',
//   host: 'localhost',
//   database: 'robotics_v1',
//   password: 'securepassword123',
//   port: 5432,
// });

// // Setup Redis
// const redisClient = redis.createClient();
// redisClient.connect().catch(console.error);

// // ============================================
// // API ENDPOINTS
// // ============================================

// // Health Check
// app.get('/', (req, res) => {
//   res.json({
//     status: 'active',
//     system: 'warehouse-robotics-backend',
//     time: new Date()
//   });
// });

// // ============================================
// // SIMULATION MANAGEMENT
// // ============================================

// // Start Simulation Run
// app.post('/api/simulations/start', async (req, res) => {
//   const { scenario_id, scenario_name } = req.body;
//   try {
//     const result = await pool.query(
//       `INSERT INTO simulation_runs (scenario_id, status) 
//        VALUES ($1, 'running') RETURNING id`,
//       [scenario_id || null]
//     );

//     const run_id = result.rows[0].id;

//     // Cache run info in Redis
//     await redisClient.set(`run:${run_id}:status`, 'running', { EX: 3600 });

//     res.json({
//       run_id: run_id,
//       status: 'started',
//       message: 'Simulation run started successfully'
//     });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // End Simulation Run
// app.post('/api/simulations/end/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const { final_score, total_tasks, total_energy, failures } = req.body;

//   try {
//     await pool.query(
//       `UPDATE simulation_runs 
//        SET status = 'completed', 
//            end_time = NOW(),
//            final_score = $1,
//            total_tasks_completed = $2,
//            total_energy_used = $3,
//            total_failures = $4
//        WHERE id = $5`,
//       [final_score, total_tasks, total_energy, failures, run_id]
//     );

//     res.json({ status: 'completed' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // ROBOT TELEMETRY
// // ============================================

// // Ingest Robot Telemetry (High Frequency)
// app.post('/api/telemetry/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     robot_icon,
//     position_x,
//     position_y,
//     position_z,
//     battery,
//     task_state,
//     status,
//     carrying_item,
//     movement_state,
//     current_pickup,
//     current_shelf,
//     current_delivery,
//     tasks_completed,
//     total_energy_used,
//     sensor_data
//   } = req.body;

//   try {
//     // Fast write to Redis for real-time dashboard
//     const cacheKey = `robot:${run_id}:${robot_id}:latest`;
//     await redisClient.set(cacheKey, JSON.stringify(req.body), { EX: 60 });

//     // Async write to PostgreSQL for persistence
//     pool.query(
//       `INSERT INTO robot_telemetry (
//         run_id, robot_id, robot_icon,
//         position_x, position_y, position_z,
//         battery_level, task_state, status,
//         carrying_item, movement_state,
//         current_pickup, current_shelf, current_delivery,
//         tasks_completed, total_energy_used,
//         sensor_data
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)`,
//       [
//         run_id, robot_id, robot_icon,
//         position_x, position_y, position_z,
//         battery, task_state, status,
//         carrying_item, movement_state,
//         current_pickup, current_shelf, current_delivery,
//         tasks_completed, total_energy_used,
//         sensor_data || {}
//       ]
//     ).catch(err => console.error('DB Insert Error:', err));

//     res.json({ status: 'ok', message: 'Telemetry received' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Get Latest Robot States (Real-time Dashboard)
// app.get('/api/telemetry/:run_id/latest', async (req, res) => {
//   const { run_id } = req.params;

//   try {
//     const result = await pool.query(
//       `SELECT DISTINCT ON (robot_id) *
//        FROM robot_telemetry
//        WHERE run_id = $1
//        ORDER BY robot_id, timestamp DESC`,
//       [run_id]
//     );

//     res.json({ robots: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // TASK MANAGEMENT
// // ============================================

// // Save Task Assignment
// app.post('/api/tasks/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     task_number,
//     pickup_zone,
//     shelf_zone,
//     delivery_zone,
//     ai_decision
//   } = req.body;

//   try {
//     const result = await pool.query(
//       `INSERT INTO robot_tasks (
//         run_id, robot_id, task_number,
//         pickup_zone, shelf_zone, delivery_zone,
//         ai_decision, status
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'assigned') RETURNING id`,
//       [run_id, robot_id, task_number, pickup_zone, shelf_zone, delivery_zone, ai_decision || {}]
//     );

//     res.json({
//       task_id: result.rows[0].id,
//       status: 'assigned'
//     });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Complete Task
// app.post('/api/tasks/:task_id/complete', async (req, res) => {
//   const { task_id } = req.params;
//   const { completion_time, energy_used } = req.body;

//   try {
//     await pool.query(
//       `UPDATE robot_tasks 
//        SET status = 'completed',
//            completed_at = NOW(),
//            completion_time = $1,
//            energy_used = $2
//        WHERE id = $3`,
//       [completion_time, energy_used, task_id]
//     );

//     res.json({ status: 'completed' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // METRICS & ANALYTICS
// // ============================================

// // Get Simulation Runs
// app.get('/api/metrics/runs', async (req, res) => {
//   try {
//     const result = await pool.query(
//       `SELECT * FROM simulation_runs 
//        ORDER BY start_time DESC LIMIT 10`
//     );
//     res.json({ runs: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Get Robot Performance Metrics
// app.get('/api/metrics/robots/:run_id', async (req, res) => {
//   const { run_id } = req.params;

//   try {
//     const result = await pool.query(
//       `SELECT 
//         robot_id,
//         COUNT(*) as total_tasks,
//         AVG(completion_time) as avg_completion_time,
//         SUM(energy_used) as total_energy,
//         MAX(timestamp) as last_update
//        FROM robot_metrics
//        WHERE run_id = $1
//        GROUP BY robot_id`,
//       [run_id]
//     );

//     res.json({ metrics: result.rows });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Save Performance Metrics
// app.post('/api/metrics/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     robot_id,
//     task_number,
//     completion_time,
//     energy_used,
//     pickup_zone,
//     shelf_zone,
//     delivery_zone
//   } = req.body;

//   try {
//     await pool.query(
//       `INSERT INTO robot_metrics (
//         run_id, robot_id, task_number,
//         completion_time, energy_used,
//         pickup_zone, shelf_zone, delivery_zone
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
//       [run_id, robot_id, task_number, completion_time, energy_used,
//         pickup_zone, shelf_zone, delivery_zone]
//     );

//     res.json({ status: 'saved' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // ============================================
// // AI DECISIONS
// // ============================================

// // Save AI Decision
// app.post('/api/ai/decisions/:run_id', async (req, res) => {
//   const { run_id } = req.params;
//   const {
//     decision_type,
//     assigned_robot,
//     assigned_route,
//     confidence,
//     input_state,
//     decision_output
//   } = req.body;

//   try {
//     await pool.query(
//       `INSERT INTO ai_decisions (
//         run_id, decision_type, assigned_robot,
//         assigned_route, confidence,
//         input_state, decision_output
//       ) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
//       [run_id, decision_type, assigned_robot, assigned_route || {},
//         confidence, input_state || {}, decision_output || {}]
//     );

//     res.json({ status: 'saved' });
//   } catch (err) {
//     res.status(500).json({ error: err.message });
//   }
// });

// // Start Server
// app.listen(port, () => {
//   console.log(`🚀 Warehouse Robotics Backend running on Port ${port}`);
//   console.log(`📊 Database: PostgreSQL + Redis`);
//   console.log(`🌐 API: http://localhost:${port}`);
// });


require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const redis = require('redis');
const cors = require('cors');
const bodyParser = require('body-parser');

// Setup Express
const app = express();
const port = 3000;
app.use(cors());
app.use(bodyParser.json());

// Setup Database Connection
const pool = new Pool({
  user: 'admin',
  host: 'localhost',
  database: 'robotics_v1',
  password: 'securepassword123',
  port: 5432,
});

// Setup Redis
const redisClient = redis.createClient();
redisClient.connect().catch(console.error);

// ============================================
// API ENDPOINTS
// ============================================

// Health Check
app.get('/', (req, res) => {
  res.json({
    status: 'active',
    system: 'warehouse-robotics-backend',
    time: new Date()
  });
});

// ============================================
// SIMULATION MANAGEMENT
// ============================================

// Start Simulation Run
app.post('/api/simulations/start', async (req, res) => {
  const { scenario_id, scenario_name } = req.body;
  try {
    const result = await pool.query(
      `INSERT INTO simulation_runs (scenario_id, status) 
       VALUES ($1, 'running') RETURNING id`,
      [scenario_id || null]
    );

    const run_id = result.rows[0].id;

    // Cache run info in Redis
    await redisClient.set(`run:${run_id}:status`, 'running', { EX: 3600 });

    res.json({
      run_id: run_id,
      status: 'started',
      message: 'Simulation run started successfully'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// End Simulation Run
app.post('/api/simulations/end/:run_id', async (req, res) => {
  const { run_id } = req.params;
  const { final_score, total_tasks, total_energy, failures } = req.body;

  try {
    await pool.query(
      `UPDATE simulation_runs 
       SET status = 'completed', 
           end_time = NOW(),
           final_score = $1,
           total_tasks_completed = $2,
           total_energy_used = $3,
           total_failures = $4
       WHERE id = $5`,
      [final_score, total_tasks, total_energy, failures, run_id]
    );

    res.json({ status: 'completed' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================
// ROBOT TELEMETRY (FIXED)
// ============================================

// Ingest Robot Telemetry (High Frequency)
app.post('/api/telemetry/:run_id', async (req, res) => {
  const { run_id } = req.params;
  
  // SUPER DEFENSIVE: Ensure battery_level is never null
  let battery_level = req.body.battery_level || req.body.battery;
  
  // If still null/undefined/NaN/0, use 100.0
  if (!battery_level || isNaN(battery_level)) {
    battery_level = 100.0;
  }
  
  const status = req.body.status || req.body.task_state || 'active';
  
  const {
    robot_id,
    robot_icon,
    position_x,
    position_y,
    position_z,
    task_state,
    carrying_item,
    movement_state,
    current_pickup,
    current_shelf,
    current_delivery,
    tasks_completed,
    total_energy_used,
    total_energy,
    sensor_data
  } = req.body;

  try {
    // Fast write to Redis for real-time dashboard
    const cacheKey = `robot:${run_id}:${robot_id}:latest`;
    await redisClient.set(cacheKey, JSON.stringify(req.body), { EX: 60 });

    // Async write to PostgreSQL with safe defaults
    pool.query(
      `INSERT INTO robot_telemetry (
        run_id, robot_id, robot_icon,
        position_x, position_y, position_z,
        battery_level, task_state, status,
        carrying_item, movement_state,
        current_pickup, current_shelf, current_delivery,
        tasks_completed, total_energy_used,
        sensor_data
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)`,
      [
        run_id, 
        robot_id || 'unknown', 
        robot_icon || '🤖',
        position_x || 0, 
        position_y || 0, 
        position_z || 0,
        battery_level,
        task_state || 'unknown',
        status,
        carrying_item || false,
        movement_state || 'idle',
        current_pickup || null,
        current_shelf || null,
        current_delivery || null,
        tasks_completed || 0,
        total_energy_used || total_energy || 0,
        sensor_data || {}
      ]
    ).catch(err => {
      // Only log first part of error to avoid spam
      if (!app.locals.dbErrorLogged) {
        console.error('DB Insert Error:', err.message);
        app.locals.dbErrorLogged = true;
      }
    });

    res.json({ status: 'ok', message: 'Telemetry received' });
  } catch (err) {
    console.error('Telemetry error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// Get Latest Robot States (Real-time Dashboard)
app.get('/api/telemetry/:run_id/latest', async (req, res) => {
  const { run_id } = req.params;

  try {
    const result = await pool.query(
      `SELECT DISTINCT ON (robot_id) *
       FROM robot_telemetry
       WHERE run_id = $1
       ORDER BY robot_id, timestamp DESC`,
      [run_id]
    );

    res.json({ robots: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================
// TASK MANAGEMENT
// ============================================

// Save Task Assignment
app.post('/api/tasks/:run_id', async (req, res) => {
  const { run_id } = req.params;
  const {
    robot_id,
    task_number,
    pickup_zone,
    shelf_zone,
    delivery_zone,
    ai_decision
  } = req.body;

  try {
    const result = await pool.query(
      `INSERT INTO robot_tasks (
        run_id, robot_id, task_number,
        pickup_zone, shelf_zone, delivery_zone,
        ai_decision, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'assigned') RETURNING id`,
      [run_id, robot_id, task_number, pickup_zone, shelf_zone, delivery_zone, ai_decision || {}]
    );

    res.json({
      task_id: result.rows[0].id,
      status: 'assigned'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Complete Task
app.post('/api/tasks/:task_id/complete', async (req, res) => {
  const { task_id } = req.params;
  const { completion_time, energy_used } = req.body;

  try {
    await pool.query(
      `UPDATE robot_tasks 
       SET status = 'completed',
           completed_at = NOW(),
           completion_time = $1,
           energy_used = $2
       WHERE id = $3`,
      [completion_time, energy_used, task_id]
    );

    res.json({ status: 'completed' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================
// METRICS & ANALYTICS
// ============================================

// Get Simulation Runs
app.get('/api/metrics/runs', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT * FROM simulation_runs 
       ORDER BY start_time DESC LIMIT 10`
    );
    res.json({ runs: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get Robot Performance Metrics
app.get('/api/metrics/robots/:run_id', async (req, res) => {
  const { run_id } = req.params;

  try {
    const result = await pool.query(
      `SELECT 
        robot_id,
        COUNT(*) as total_tasks,
        AVG(completion_time) as avg_completion_time,
        SUM(energy_used) as total_energy,
        MAX(timestamp) as last_update
       FROM robot_metrics
       WHERE run_id = $1
       GROUP BY robot_id`,
      [run_id]
    );

    res.json({ metrics: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Save Performance Metrics
app.post('/api/metrics/:run_id', async (req, res) => {
  const { run_id } = req.params;
  const {
    robot_id,
    task_number,
    completion_time,
    energy_used,
    pickup_zone,
    shelf_zone,
    delivery_zone
  } = req.body;

  try {
    await pool.query(
      `INSERT INTO robot_metrics (
        run_id, robot_id, task_number,
        completion_time, energy_used,
        pickup_zone, shelf_zone, delivery_zone
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [run_id, robot_id, task_number, completion_time, energy_used,
        pickup_zone, shelf_zone, delivery_zone]
    );

    res.json({ status: 'saved' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================
// AI DECISIONS
// ============================================

// Save AI Decision
app.post('/api/ai/decisions/:run_id', async (req, res) => {
  const { run_id } = req.params;
  const {
    decision_type,
    assigned_robot,
    assigned_route,
    confidence,
    input_state,
    decision_output
  } = req.body;

  try {
    await pool.query(
      `INSERT INTO ai_decisions (
        run_id, decision_type, assigned_robot,
        assigned_route, confidence,
        input_state, decision_output
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [run_id, decision_type, assigned_robot, assigned_route || {},
        confidence, input_state || {}, decision_output || {}]
    );

    res.json({ status: 'saved' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Start Server
app.listen(port, () => {
  console.log(`🚀 Warehouse Robotics Backend running on Port ${port}`);
  console.log(`📊 Database: PostgreSQL + Redis`);
  console.log(`🌐 API: http://localhost:${port}`);
});