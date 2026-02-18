require('dotenv').config();
const express = require('express');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// ============================================
// ERROR HANDLING
// ============================================

process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error.message);
});

process.on('unhandledRejection', (error) => {
    console.error('❌ Unhandled Promise:', error.message);
});

// ============================================
// DATABASE CONNECTION
// ============================================

const pool = new Pool({
    user: 'admin',
    host: 'localhost',
    database: 'robotics_v1',
    password: 'securepassword123',
    port: 5432,
});

pool.on('error', (err) => {
    console.error('Database error:', err);
});

console.log('✅ PostgreSQL: Connection pool initialized');

// ============================================
// GEMINI AI (OPTIONAL)
// ============================================

let geminiModel = null;
const apiKey = process.env.GEMINI_API_KEY;

if (apiKey && apiKey.length > 10) {
    try {
        const genAI = new GoogleGenerativeAI(apiKey);
        geminiModel = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
        console.log('✅ Gemini AI: Initialized');
    } catch (error) {
        console.log('⚠️  Gemini AI: Not available');
    }
} else {
    console.log('⚠️  Gemini AI: No API key (using mathematical algorithms only)');
}

// ============================================
// Q-LEARNING SYSTEM
// ============================================

class QLearningEngine {
    constructor() {
        // Q-Table: state-action pairs with values
        // Key: "zone_A->zone_B"
        // Value: { q_value, visits, avg_time, success_rate }
        this.q_table = {};
        
        // Learning parameters
        this.alpha = 0.15;      // Learning rate
        this.gamma = 0.9;       // Discount factor
        this.epsilon = 0.15;    // Exploration rate
        
        // Spatial grid for failure mapping (20x20 grid for -5 to 5 coordinate space)
        this.failure_grid = Array(20).fill().map(() => Array(20).fill(0));
        
        // Resource tracking
        this.zone_congestion = {};  // Current robot count per zone
        this.zone_utilization = {}; // Historical utilization
    }
    
    /**
     * Convert world coordinates to grid indices
     */
    toGridIndex(x, y) {
        const gridX = Math.floor((x + 5) * 2);
        const gridY = Math.floor((y + 5) * 2);
        return {
            x: Math.max(0, Math.min(19, gridX)),
            y: Math.max(0, Math.min(19, gridY))
        };
    }
    
    /**
     * Initialize Q-value for a state-action pair
     */
    initializeQValue(state, action) {
        const key = `${state}->${action}`;
        if (!this.q_table[key]) {
            this.q_table[key] = {
                q_value: 50.0,  // Neutral initial value
                visits: 0,
                avg_time: 0,
                total_time: 0,
                success_count: 0,
                failure_count: 0
            };
        }
        return key;
    }
    
    /**
     * Q-Learning Update
     * Q(s,a) = Q(s,a) + α[r + γmax(Q(s',a')) - Q(s,a)]
     */
    updateQValue(state, action, reward, next_state, possible_next_actions) {
        const key = this.initializeQValue(state, action);
        const entry = this.q_table[key];
        
        // Find maximum Q-value for next state
        let max_next_q = 0;
        if (possible_next_actions && possible_next_actions.length > 0) {
            max_next_q = Math.max(...possible_next_actions.map(next_action => {
                const next_key = `${next_state}->${next_action}`;
                return this.q_table[next_key] ? this.q_table[next_key].q_value : 50.0;
            }));
        }
        
        // Q-Learning formula
        const current_q = entry.q_value;
        const new_q = current_q + this.alpha * (reward + this.gamma * max_next_q - current_q);
        
        entry.q_value = new_q;
        entry.visits++;
        
        return new_q;
    }
    
    /**
     * Learn from completed task
     */
    learnFromTask(route, duration, success) {
        const { pickup, shelf, delivery } = route;
        
        // Calculate rewards
        // Fast completion = high reward
        // Slow completion = low reward
        // Failure = negative reward
        const base_reward = success ? 100 : -50;
        const time_bonus = Math.max(0, 60 - duration);  // Bonus for completing in <60s
        const time_penalty = Math.max(0, duration - 60) * 0.5;  // Penalty for >60s
        
        const pickup_to_shelf_reward = base_reward + time_bonus - time_penalty;
        const shelf_to_delivery_reward = base_reward + time_bonus - time_penalty;
        
        // Update Q-values
        this.updateQValue(pickup, shelf, pickup_to_shelf_reward, shelf, [delivery]);
        this.updateQValue(shelf, delivery, shelf_to_delivery_reward, delivery, []);
        
        // Update statistics
        const key1 = `${pickup}->${shelf}`;
        const key2 = `${shelf}->${delivery}`;
        
        if (this.q_table[key1]) {
            this.q_table[key1].total_time += duration / 2;
            this.q_table[key1].avg_time = this.q_table[key1].total_time / this.q_table[key1].visits;
            if (success) this.q_table[key1].success_count++;
            else this.q_table[key1].failure_count++;
        }
        
        if (this.q_table[key2]) {
            this.q_table[key2].total_time += duration / 2;
            this.q_table[key2].avg_time = this.q_table[key2].total_time / this.q_table[key2].visits;
            if (success) this.q_table[key2].success_count++;
            else this.q_table[key2].failure_count++;
        }
    }
    
    /**
     * Select best action using ε-greedy policy
     */
    selectBestAction(state, possible_actions) {
        // Exploration: Random selection
        if (Math.random() < this.epsilon) {
            return possible_actions[Math.floor(Math.random() * possible_actions.length)];
        }
        
        // Exploitation: Select highest Q-value
        let best_action = null;
        let highest_q = -Infinity;
        
        for (const action of possible_actions) {
            const key = `${state}->${action.id}`;
            const q_value = this.q_table[key] ? this.q_table[key].q_value : 50.0;
            
            // Consider congestion
            const congestion = this.zone_congestion[action.id] || 0;
            const congestion_penalty = congestion * 15;  // Each robot reduces score by 15
            
            const final_score = q_value - congestion_penalty;
            
            if (final_score > highest_q) {
                highest_q = final_score;
                best_action = action;
            }
        }
        
        return best_action || possible_actions[0];
    }
    
    /**
     * Register failure in spatial grid
     */
    registerFailure(x, y, severity = 3) {
        const grid_pos = this.toGridIndex(x, y);
        this.failure_grid[grid_pos.y][grid_pos.x] += severity;
        
        // Also mark neighboring cells (failure spread)
        for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
                const nx = grid_pos.x + dx;
                const ny = grid_pos.y + dy;
                if (nx >= 0 && nx < 20 && ny >= 0 && ny < 20) {
                    this.failure_grid[ny][nx] += Math.floor(severity / 2);
                }
            }
        }
    }
    
    /**
     * Update congestion tracking
     */
    updateCongestion(zone_id, delta) {
        if (!this.zone_congestion[zone_id]) {
            this.zone_congestion[zone_id] = 0;
        }
        this.zone_congestion[zone_id] = Math.max(0, this.zone_congestion[zone_id] + delta);
    }
    
    /**
     * Get efficiency metrics
     */
    getEfficiencyMetrics() {
        const total_routes = Object.keys(this.q_table).length;
        const avg_q_value = total_routes > 0
            ? Object.values(this.q_table).reduce((sum, e) => sum + e.q_value, 0) / total_routes
            : 50;
        
        const total_visits = Object.values(this.q_table).reduce((sum, e) => sum + e.visits, 0);
        const total_successes = Object.values(this.q_table).reduce((sum, e) => sum + e.success_count, 0);
        const success_rate = total_visits > 0 ? (total_successes / total_visits) * 100 : 0;
        
        return {
            total_routes_learned: total_routes,
            average_q_value: avg_q_value.toFixed(2),
            total_experience: total_visits,
            success_rate: success_rate.toFixed(1) + '%',
            exploration_rate: (this.epsilon * 100).toFixed(0) + '%'
        };
    }
}

const qLearning = new QLearningEngine();

// ============================================
// RUN MANAGEMENT
// ============================================

let currentRunNumber = 1;
let runHistory = [];
let robotStates = {};
let currentRunMetrics = {
    tasks_completed: 0,
    total_duration: 0,
    total_energy: 0,
    total_failures: 0,
    start_time: Date.now()
};

// ============================================
// API ENDPOINTS
// ============================================

app.get('/', (req, res) => {
    res.json({
        status: 'active',
        run: currentRunNumber,
        robots_active: Object.keys(robotStates).length,
        learning_stats: qLearning.getEfficiencyMetrics()
    });
});

app.get('/api/runs/next-number', (req, res) => {
    console.log(`📊 Run #${currentRunNumber} requested`);
    res.json({ run_number: currentRunNumber });
});

/**
 * RESOURCE ALLOCATION ENDPOINT
 * Uses Q-learning to assign optimal zones
 */
app.post('/api/allocator/assign-optimal', (req, res) => {
    try {
        const { robot_id, current_zone, target_type, available_options } = req.body;
        
        if (!available_options || available_options.length === 0) {
            return res.status(400).json({ error: 'No options provided' });
        }
        
        // Use Q-learning to select best option
        const current_state = current_zone || 'start';
        const best_target = qLearning.selectBestAction(current_state, available_options);
        
        // Update congestion
        qLearning.updateCongestion(best_target.id, 1);
        
        console.log(`🧠 Allocated ${best_target.id} to ${robot_id} (Q-Learning)`);
        
        res.json({ assigned_target: best_target });
    } catch (error) {
        console.error('Allocation error:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * TELEMETRY MONITORING
 * Normalizes payload from robot_control.py (position.x/y, battery, total_energy_used)
 * and ensures NOT NULL columns have defaults.
 */
app.post('/api/monitor/telemetry', async (req, res) => {
    try {
        const telemetry = req.body;
        const robot_id = telemetry.robot_id;
        
        // Update robot state
        robotStates[robot_id] = {
            ...telemetry,
            last_update: Date.now()
        };
        
        // Store in database (async - don't wait)
        if (telemetry.run_id) {
            const position_x = telemetry.position_x ?? telemetry.position?.x ?? 0;
            const position_y = telemetry.position_y ?? telemetry.position?.y ?? 0;
            const battery_level = telemetry.battery_level ?? telemetry.battery ?? 100;
            const task_state = telemetry.task_state ?? 'unknown';
            const total_energy = telemetry.total_energy ?? telemetry.total_energy_used ?? 0;
            const tasks_completed = telemetry.tasks_completed ?? 0;

            pool.query(
                `INSERT INTO robot_telemetry 
                (run_id, robot_id, position_x, position_y, task_state, status, battery_level, 
                 tasks_completed, total_energy_used, timestamp, sensor_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), $10)`,
                [
                    telemetry.run_id,
                    robot_id,
                    position_x,
                    position_y,
                    task_state,
                    'active',
                    Number(battery_level),
                    tasks_completed,
                    Number(total_energy),
                    JSON.stringify(telemetry.sensor_data || {})
                ]
            ).catch(err => console.error('DB insert error:', err.message));
        }
        
        res.json({ status: 'monitored' });
    } catch (error) {
        console.error('Telemetry error:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * STUCK ROBOT HANDLING
 */
app.post('/api/robots/stuck', (req, res) => {
    try {
        const { robot_id, position, task_state, failures } = req.body;
        
        // Register failure in spatial grid
        qLearning.registerFailure(position.x, position.y, 5);
        
        currentRunMetrics.total_failures++;
        
        console.log(`\n🚨 STUCK: ${robot_id} at (${position.x.toFixed(2)}, ${position.y.toFixed(2)})`);
        console.log(`   Task: ${task_state} | Total Failures: ${currentRunMetrics.total_failures}\n`);
        
        res.json({ status: 'logged', recovery: 'autonomous' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * TASK COMPLETION LEARNING
 */
app.post('/api/tasks/complete', async (req, res) => {
    try {
        const { 
            robot_id, run_number, task_number,
            pickup, shelf, delivery,
            duration, energy_used, failures, success 
        } = req.body;
        
        // Update metrics
        currentRunMetrics.tasks_completed++;
        currentRunMetrics.total_duration += duration;
        currentRunMetrics.total_energy += energy_used;
        
        // Q-Learning update
        qLearning.learnFromTask(
            { pickup, shelf, delivery },
            duration,
            success !== false
        );
        
        // Update congestion (release zones)
        qLearning.updateCongestion(pickup, -1);
        qLearning.updateCongestion(shelf, -1);
        qLearning.updateCongestion(delivery, -1);
        
        console.log(`✅ Task #${task_number} complete: ${duration.toFixed(1)}s | Energy: ${energy_used.toFixed(2)}`);
        
        // run_id must be a valid UUID or NULL (column is FK to simulation_runs)
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        const runId = req.body.run_id && uuidRegex.test(String(req.body.run_id)) ? req.body.run_id : null;

        // Store in database (robot_tasks has completed_at, not timestamp)
        pool.query(
            `INSERT INTO robot_tasks 
            (run_id, robot_id, task_number, pickup_zone, shelf_zone, delivery_zone,
             completion_time, energy_used, status, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())`,
            [
                runId,
                robot_id,
                task_number,
                pickup,
                shelf,
                delivery,
                duration,
                energy_used,
                success !== false ? 'completed' : 'failed'
            ]
        ).catch(err => console.error('DB task insert error:', err.message));
        
        res.json({ status: 'learned', q_metrics: qLearning.getEfficiencyMetrics() });
    } catch (error) {
        console.error('Task completion error:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * END RUN & ANALYSIS
 */
app.post('/api/runs/end', async (req, res) => {
    try {
        const run_duration = (Date.now() - currentRunMetrics.start_time) / 1000;
        
        // Calculate efficiency
        const avg_task_time = currentRunMetrics.tasks_completed > 0
            ? currentRunMetrics.total_duration / currentRunMetrics.tasks_completed
            : 0;
        
        const efficiency_score = currentRunMetrics.tasks_completed > 0
            ? (currentRunMetrics.tasks_completed * 100) / 
              ((avg_task_time + 1) * (currentRunMetrics.total_energy + 1) * (currentRunMetrics.total_failures + 1))
            : 0;
        
        const run_summary = {
            run_number: currentRunNumber,
            tasks_completed: currentRunMetrics.tasks_completed,
            avg_task_time: avg_task_time.toFixed(2),
            total_energy: currentRunMetrics.total_energy.toFixed(2),
            total_failures: currentRunMetrics.total_failures,
            efficiency_score: efficiency_score.toFixed(3),
            run_duration: run_duration.toFixed(1),
            learning_stats: qLearning.getEfficiencyMetrics()
        };
        
        runHistory.push(run_summary);
        
        console.log('\n' + '='.repeat(70));
        console.log('📊 RUN ANALYSIS');
        console.log('='.repeat(70));
        console.log(`Run #${currentRunNumber}`);
        console.log(`Tasks: ${currentRunMetrics.tasks_completed}`);
        console.log(`Avg Time: ${avg_task_time.toFixed(1)}s`);
        console.log(`Energy: ${currentRunMetrics.total_energy.toFixed(2)}`);
        console.log(`Failures: ${currentRunMetrics.total_failures}`);
        console.log(`Efficiency: ${efficiency_score.toFixed(3)}`);
        console.log('='.repeat(70));
        console.log('Q-Learning Stats:');
        console.log(JSON.stringify(qLearning.getEfficiencyMetrics(), null, 2));
        console.log('='.repeat(70) + '\n');
        
        // Gemini analysis (optional)
        let ai_analysis = null;
        if (geminiModel && runHistory.length > 1) {
            try {
                const prompt = `Analyze warehouse efficiency trends:

${runHistory.slice(-3).map(r => `Run ${r.run_number}: ${r.tasks_completed} tasks, ${r.avg_task_time}s avg, ${r.total_failures} failures, efficiency: ${r.efficiency_score}`).join('\n')}

Q-Learning: ${run_summary.learning_stats.total_routes_learned} routes learned, ${run_summary.learning_stats.success_rate} success rate

Provide 3 specific optimization recommendations in JSON:
{ "recommendations": ["rec1", "rec2", "rec3"], "trend": "improving|stable|degrading" }`;

                const result = await geminiModel.generateContent(prompt);
                const text = (await result.response).text();
                const jsonMatch = text.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    ai_analysis = JSON.parse(jsonMatch[0]);
                }
            } catch (err) {
                console.log('Gemini analysis failed:', err.message);
            }
        }
        
        // Reset for next run
        currentRunNumber++;
        currentRunMetrics = {
            tasks_completed: 0,
            total_duration: 0,
            total_energy: 0,
            total_failures: 0,
            start_time: Date.now()
        };
        robotStates = {};
        
        // NOTE: Q-learning knowledge is RETAINED across runs (this is learning!)
        
        res.json({
            run_summary: run_summary,
            ai_analysis: ai_analysis,
            next_run_number: currentRunNumber,
            knowledge_retained: true
        });
    } catch (error) {
        console.error('Run end error:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * DASHBOARD DATA
 */
app.get('/api/dashboard', (req, res) => {
    try {
        const robots = {};
        for (const [robot_id, state] of Object.entries(robotStates)) {
            robots[robot_id] = {
                position: { x: state.position_x, y: state.position_y },
                task_state: state.task_state,
                battery: state.battery_level,
                tasks_completed: state.tasks_completed
            };
        }
        
        res.json({
            run_number: currentRunNumber,
            robots: robots,
            current_metrics: currentRunMetrics,
            learning_stats: qLearning.getEfficiencyMetrics(),
            run_history: runHistory.slice(-5)
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ============================================
// SERVER START
// ============================================

const PORT = 4000;
const server = app.listen(PORT, () => {
    console.log('\n' + '='.repeat(70));
    console.log(`🧠 PRODUCTION AI SUPERVISOR - Port ${PORT}`);
    console.log('='.repeat(70));
    console.log('✅ Q-Learning: Active');
    console.log('✅ Resource Allocation: Active');
    console.log('✅ Spatial Mapping: Active');
    console.log('✅ Database Logging: Active');
    console.log(`🔄 Run #${currentRunNumber} ready`);
    console.log('='.repeat(70) + '\n');
});

server.on('error', (error) => {
    console.error('Server error:', error);
});