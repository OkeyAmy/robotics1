"""
LOCAL DATA STORAGE - Simulates Backend Database
Saves data to JSON files locally
Easy to replace with REST API calls later
"""

import json
import os
from datetime import datetime
import csv

# Data directory
DATA_DIR = "warehouse_data"
TELEMETRY_DIR = os.path.join(DATA_DIR, "telemetry")
TASKS_DIR = os.path.join(DATA_DIR, "tasks")
RUNS_DIR = os.path.join(DATA_DIR, "runs")
METRICS_DIR = os.path.join(DATA_DIR, "metrics")

# Create directories if they don't exist
for directory in [DATA_DIR, TELEMETRY_DIR, TASKS_DIR, RUNS_DIR, METRICS_DIR]:
    os.makedirs(directory, exist_ok=True)

class DataStorage:
    """Simulates backend database with local JSON files"""
    
    def __init__(self):
        self.current_run_id = self._get_next_run_id()
        self.run_start_time = datetime.now()
        
    def _get_next_run_id(self):
        """Get next run ID"""
        runs = [f for f in os.listdir(RUNS_DIR) if f.startswith("run_")]
        if not runs:
            return 1
        run_numbers = [int(f.split("_")[1].split(".")[0]) for f in runs]
        return max(run_numbers) + 1
    
    # ==========================================
    # TELEMETRY (robot position, battery, etc.)
    # ==========================================
    
    def save_telemetry(self, telemetry_data):
        """
        Save robot telemetry to JSON file
        In production: POST to /api/telemetry
        """
        robot_id = telemetry_data.get("robot_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = os.path.join(TELEMETRY_DIR, f"{robot_id}_telemetry.jsonl")
        
        # Append to JSONL file (one JSON per line)
        with open(filename, 'a') as f:
            f.write(json.dumps(telemetry_data) + '\n')
    
    # ==========================================
    # TASKS (task assignments)
    # ==========================================
    
    def save_task(self, task_data):
        """
        Save task assignment
        In production: POST to /api/tasks
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(TASKS_DIR, f"task_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(task_data, f, indent=2)
    
    def get_pending_tasks(self, robot_id):
        """
        Get pending tasks for robot
        In production: GET from /api/tasks/{robot_id}
        """
        # Placeholder - returns None for now
        # AI engine will assign tasks
        return None
    
    # ==========================================
    # SIMULATION RUNS (overall run metrics)
    # ==========================================
    
    def save_run_metrics(self, metrics):
        """
        Save simulation run metrics
        In production: POST to /api/runs
        """
        filename = os.path.join(RUNS_DIR, f"run_{self.current_run_id}.json")
        
        run_data = {
            "run_id": self.current_run_id,
            "start_time": self.run_start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "metrics": metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(run_data, f, indent=2)
        
        print(f"\n💾 Run {self.current_run_id} metrics saved to {filename}")
    
    def get_previous_runs(self, limit=3):
        """Get previous run metrics for comparison"""
        runs = []
        for f in sorted(os.listdir(RUNS_DIR))[-limit:]:
            filepath = os.path.join(RUNS_DIR, f)
            with open(filepath, 'r') as file:
                runs.append(json.load(file))
        return runs
    
    # ==========================================
    # METRICS (performance data)
    # ==========================================
    
    def save_performance_metrics(self, robot_id, metrics):
        """
        Save robot performance metrics
        In production: POST to /api/metrics
        """
        filename = os.path.join(METRICS_DIR, f"{robot_id}_metrics.json")
        
        # Load existing or create new
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {"robot_id": robot_id, "metrics": []}
        
        data["metrics"].append(metrics)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==========================================
    # AI DECISIONS (for tracking)
    # ==========================================
    
    def save_ai_decision(self, decision_data):
        """
        Save AI decision for tracking
        In production: POST to /api/ai_decisions
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(DATA_DIR, f"ai_decisions_{self.current_run_id}.jsonl")
        
        with open(filename, 'a') as f:
            f.write(json.dumps(decision_data) + '\n')

# Global instance
storage = DataStorage()
