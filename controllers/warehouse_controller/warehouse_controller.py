"""
WAREHOUSE ROBOT CONTROLLER - FIXED VERSION
With calibrated zone coordinates and improved navigation

Based on your calibration:
Pickup: X=-3.02 to -3.14, Y=0.19-0.20
Shelf: X=1.53 to 2.03, Y=0.19-0.20  
Delivery: X=-0.07 to -0.11, Y=0.19
Charging: X=4.01 to 4.03, Y=0.19-0.20
"""

from controller import Robot
import math
import random
import time

# ============================================
# CONFIGURATION
# ============================================

BACKEND_URL = "http://localhost:3000"
AI_SERVER_URL = "http://localhost:4000"

try:
    import requests
    BACKEND_AVAILABLE = True
    print("✅ Network: Backend enabled")
except ImportError:
    BACKEND_AVAILABLE = False
    print("⚠️  Network: Offline mode")

# ============================================
# ROBOT INITIALIZATION
# ============================================

robot = Robot()
TIME_STEP = int(robot.getBasicTimeStep())
ROBOT_NAME = robot.getName()

ROBOT_ICONS = {
    "Pioneer 3-DX": "🔴", "Pioneer 3-DX(1)": "🔵", "Pioneer 3-DX(2)": "🟢",
    "Pioneer 3-DX(3)": "🟡", "Pioneer 3-DX(4)": "🟣",
}
ICON = ROBOT_ICONS.get(ROBOT_NAME, "🤖")

# Motors
left_motor = robot.getDevice('left wheel')
right_motor = robot.getDevice('right wheel')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))

# GPS
gps = robot.getDevice('gps')
if gps:
    gps.enable(TIME_STEP)
    GPS_ENABLED = True
else:
    GPS_ENABLED = False

# Compass
compass = robot.getDevice('compass')
if compass:
    compass.enable(TIME_STEP)
    COMPASS_ENABLED = True
else:
    COMPASS_ENABLED = False

# Distance sensors
distance_sensors = []
for i in range(16):
    sensor = robot.getDevice(f'so{i}')
    if sensor:
        sensor.enable(TIME_STEP)
        distance_sensors.append(sensor)

print(f"{ICON} Sensors: {len(distance_sensors)} distance, GPS={'✅' if GPS_ENABLED else '❌'}, Compass={'✅' if COMPASS_ENABLED else '❌'}")

# ============================================
# CALIBRATED WAREHOUSE ZONES
# ============================================

# Based on your actual calibration measurements
# PICKUP_ZONES = [
    # {"id": "pickup_A", "x": -3.02, "y": 0.20, "radius": 0.6},
    # {"id": "pickup_B", "x": -3.14, "y": 0.19, "radius": 0.6},
    # {"id": "pickup_C", "x": -2.92, "y": 0.19, "radius": 0.6},
# ]

PICKUP_ZONES = [
    # {"id": "pickup_A", "x": -3.038,  "z": 0.1941, "radius": 0.6},
    {"id": "pickup_A", "x": 0.2825, "z": -84.9721, "radius": 84.9713},
    {"id": "pickup_B", "x": -3.0552, "z": 0.1952, "radius": 0.6},
    {"id": "pickup_C", "x": -3.0569, "z": 0.1955, "radius": 0.6},
]

SHELF_ZONES = [
    {"id": "shelf_1", "x": 1.53, "z": 0.20, "radius": 0.6},
    {"id": "shelf_2", "x": 2.03, "z": 0.19, "radius": 0.6},
    {"id": "shelf_3", "x": 1.69, "z": 0.19, "radius": 0.6},
]

DELIVERY_ZONES = [
    {"id": "delivery_north", "x": -0.07, "z": 0.19, "radius": 0.6},
    {"id": "delivery_south", "x": -0.11, "z": 0.19, "radius": 0.6},
]

CHARGING_STATIONS = [
    {"id": "charger_1", "x": 3.71146, "z": 0.178767, "radius": 0.6},
    {"id": "charger_2", "x": 4.09787, "z": 1.69041, "radius": 0.6},
    
]

GPS_OFFSET = {'x': -0.0002, 'z': -0.0002}

# ============================================
# NAVIGATION PARAMETERS
# ============================================

MAX_SPEED = 5.24
WHEEL_BASE = 0.33

# PID gains (reduced for smoother control)
KP_ANGULAR = 2.0
KD_ANGULAR = 0.08

GOAL_TOLERANCE = 0.5  # 50cm tolerance (increased from 40cm)
OBSTACLE_THRESHOLD = 750
CRUISE_SPEED = 3.0

# ============================================
# STATE VARIABLES
# ============================================

SIMULATION_RUN_ID = None
RUN_NUMBER = 1

task_state = "INITIALIZING"
battery_level = 100.0
BATTERY_DRAIN_RATE = 0.008
BATTERY_CHARGE_RATE = 0.3
CRITICAL_BATTERY = 15.0

tasks_completed = 0
task_failures = 0
total_distance_traveled = 0.0
total_energy_consumed = 0.0

current_pickup = None
current_shelf = None
current_delivery = None
current_charger = None

task_start_time = 0.0
wait_counter = 0
startup_delay = random.randint(20, 50)

last_position = None
previous_heading_error = 0.0
stuck_counter = 0
recovery_attempts = 0

# ============================================
# BACKEND INITIALIZATION
# ============================================

def initialize_backend():
    global SIMULATION_RUN_ID, RUN_NUMBER
    
    if not BACKEND_AVAILABLE:
        return
    
    try:
        response = requests.get(f"{AI_SERVER_URL}/api/runs/next-number", timeout=2)
        if response.status_code == 200:
            RUN_NUMBER = response.json().get("run_number", 1)
        
        response = requests.post(
            f"{BACKEND_URL}/api/simulations/start",
            json={"scenario_name": f"warehouse_run_{RUN_NUMBER}"},
            timeout=3
        )
        
        if response.status_code == 200:
            SIMULATION_RUN_ID = response.json().get("run_id")
            print(f"{ICON} Connected: Run #{RUN_NUMBER}, DB ID: {SIMULATION_RUN_ID[:8]}")
    
    except Exception as e:
        print(f"{ICON} Backend init error: {e}")

time.sleep(random.uniform(0.05, 0.3))
initialize_backend()

# ============================================
# NAVIGATION FUNCTIONS
# ============================================

def get_gps_position():
    if not GPS_ENABLED or not gps:
        return 0.0, 0.0
    try:
        vals = gps.getValues()
        # return vals[0] , vals[2]
        return vals[0] - GPS_OFFSET['x'], vals[2] - GPS_OFFSET['z']
    except:
        return 0.0, 0.0

def get_compass_heading():
    if not COMPASS_ENABLED or not compass:
        return 0.0
    try:
        north_vector = compass.getValues()
        heading = math.atan2(north_vector[0], north_vector[2])
        return heading
    except:
        return 0.0

def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle

def euclidean_distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)
    

def detect_obstacles():
    """Returns (left_obs, right_obs, front_clear) using distance conversion"""
    MIN_DISTANCE = 0.8  # meters - obstacle must be closer than this to matter
    MAX_SENSOR_VALUE = 1024.0  # maximum value the sensors can return
    
    left_threat = 0.0
    right_threat = 0.0
    front_threat = 0.0
    
    # Front-left sensors (0-3)
    for i in range(4):
        sensor_value = distance_sensors[i].getValue()
        
        # Ignore zero/very low readings (noise/shadows)
        if sensor_value < 50:
            continue
            
        # Convert to actual distance in meters (from C code formula)
        distance = 5.0 * (1.0 - (sensor_value / MAX_SENSOR_VALUE))
        
        # If obstacle is close enough, calculate threat level
        if distance < MIN_DISTANCE:
            threat = 1.0 - (distance / MIN_DISTANCE)  # closer = higher threat
            left_threat += threat
            front_threat = max(front_threat, threat)
    
    # Front-right sensors (4-7)
    for i in range(4, 8):
        sensor_value = distance_sensors[i].getValue()
        
        if sensor_value < 50:
            continue
            
        distance = 5.0 * (1.0 - (sensor_value / MAX_SENSOR_VALUE))
        
        if distance < MIN_DISTANCE:
            threat = 1.0 - (distance / MIN_DISTANCE)
            right_threat += threat
            front_threat = max(front_threat, threat)
    
    # Obstacle detected if cumulative threat exceeds threshold
    left_obstacle = left_threat > 0.5
    right_obstacle = right_threat > 0.5
    front_clear = front_threat < 0.3
    
    return left_obstacle, right_obstacle, front_clear

def navigate_to_goal(goal):
    """PID navigation with obstacle avoidance"""
    global previous_heading_error
    
    if not goal:
        return 0.0, 0.0
    
    current_pos = get_gps_position()
    current_heading = get_compass_heading()
    goal_pos = (goal['x'], goal['z'])
    distance = euclidean_distance(current_pos, goal_pos)
    
    # Reached goal
    if distance < GOAL_TOLERANCE:
        return 0.0, 0.0
    
    # Check obstacles
    left_obs, right_obs, front_clear = detect_obstacles()
    
    # REACTIVE: Obstacle avoidance
    if not front_clear:
        if left_obs and not right_obs:
            return CRUISE_SPEED * 0.6, -CRUISE_SPEED * 0.6
        elif right_obs and not left_obs:
            return -CRUISE_SPEED * 0.6, CRUISE_SPEED * 0.6
        else:
            return -CRUISE_SPEED * 0.4, CRUISE_SPEED * 0.4
    
    # DELIBERATIVE: Navigate to goal
    dx = goal_pos[0] - current_pos[0]
    dy = goal_pos[1] - current_pos[1]
    desired_heading = math.atan2(dx, dy)
    
    heading_error = normalize_angle(desired_heading - current_heading)
    
    # PID control
    angular_velocity = (KP_ANGULAR * heading_error) + \
                       (KD_ANGULAR * (heading_error - previous_heading_error))
    
    previous_heading_error = heading_error
    
    # Reduce speed when turning or near goal
    if abs(heading_error) > math.pi / 4:
        linear_velocity = CRUISE_SPEED * 0.5
    elif abs(heading_error) > math.pi / 6:
        linear_velocity = CRUISE_SPEED * 0.7
    else:
        linear_velocity = CRUISE_SPEED
    
    if distance < 1.0:
        linear_velocity *= (distance / 1.0)
    
    # Differential drive
    left_speed = linear_velocity - (angular_velocity * WHEEL_BASE / 2.0)
    right_speed = linear_velocity + (angular_velocity * WHEEL_BASE / 2.0)
    
    left_speed = max(min(left_speed, MAX_SPEED), -MAX_SPEED)
    right_speed = max(min(right_speed, MAX_SPEED), -MAX_SPEED)
    
    return left_speed, right_speed

def is_in_zone(zone):
    """Check if robot is within zone - using generous radius"""
    if not zone:
        return False
    
    current_pos = get_gps_position()
    zone_pos = (zone['x'], zone['z'])
    distance = euclidean_distance(current_pos, zone_pos)
    
    # Zone reached if within radius
    return distance < zone.get('radius', 0.5)

# ============================================
# TASK MANAGEMENT
# ============================================

def request_task_assignment():
    global current_pickup, current_shelf, current_delivery
    global task_state, wait_counter, task_start_time, recovery_attempts
    
    recovery_attempts = 0  # Reset on new task
    
    if not BACKEND_AVAILABLE:
        current_pickup = random.choice(PICKUP_ZONES)
        current_shelf = random.choice(SHELF_ZONES)
        current_delivery = random.choice(DELIVERY_ZONES)
    else:
        try:
            current_pos = get_gps_position()
            
            # Get pickup
            response = requests.post(
                f"{AI_SERVER_URL}/api/allocator/assign-optimal",
                json={
                    "robot_id": ROBOT_NAME,
                    "current_position": {"x": current_pos[0], "y": current_pos[1]},
                    "target_type": "pickup",
                    "available_options": PICKUP_ZONES
                },
                timeout=2
            )
            
            if response.status_code == 200:
                current_pickup = response.json().get("assigned_target", random.choice(PICKUP_ZONES))
            else:
                current_pickup = random.choice(PICKUP_ZONES)
            
            # Get shelf
            response = requests.post(
                f"{AI_SERVER_URL}/api/allocator/assign-optimal",
                json={
                    "robot_id": ROBOT_NAME,
                    "current_zone": current_pickup['id'],
                    "target_type": "shelf",
                    "available_options": SHELF_ZONES
                },
                timeout=2
            )
            
            if response.status_code == 200:
                current_shelf = response.json().get("assigned_target", random.choice(SHELF_ZONES))
            else:
                current_shelf = random.choice(SHELF_ZONES)
            
            # Get delivery
            response = requests.post(
                f"{AI_SERVER_URL}/api/allocator/assign-optimal",
                json={
                    "robot_id": ROBOT_NAME,
                    "current_zone": current_shelf['id'],
                    "target_type": "delivery",
                    "available_options": DELIVERY_ZONES
                },
                timeout=2
            )
            
            if response.status_code == 200:
                current_delivery = response.json().get("assigned_target", random.choice(DELIVERY_ZONES))
            else:
                current_delivery = random.choice(DELIVERY_ZONES)
        
        except Exception as e:
            current_pickup = random.choice(PICKUP_ZONES)
            current_shelf = random.choice(SHELF_ZONES)
            current_delivery = random.choice(DELIVERY_ZONES)
    
    task_state = "GOING_TO_PICKUP"
    wait_counter = 0
    task_start_time = robot.getTime()
    
    print(f"\n{ICON} ━━━ TASK #{tasks_completed + 1} ━━━")
    print(f"{ICON} Route: {current_pickup['id']} → {current_shelf['id']} → {current_delivery['id']}\n")

def report_task_completion(success=True):
    if not BACKEND_AVAILABLE:
        return
    
    task_duration = robot.getTime() - task_start_time
    
    try:
        requests.post(
            f"{AI_SERVER_URL}/api/tasks/complete",
            json={
                "robot_id": ROBOT_NAME,
                "run_number": RUN_NUMBER,
                "task_number": tasks_completed,
                "pickup": current_pickup['id'] if current_pickup else None,
                "shelf": current_shelf['id'] if current_shelf else None,
                "delivery": current_delivery['id'] if current_delivery else None,
                "duration": task_duration,
                "energy_used": total_energy_consumed,
                "failures": task_failures,
                "success": success
            },
            timeout=2
        )
    except:
        pass

def send_telemetry():
    if not BACKEND_AVAILABLE or not SIMULATION_RUN_ID:
        return
    
    x, y = get_gps_position()
    
    goal = None
    if task_state == "GOING_TO_PICKUP":
        goal = current_pickup
    elif task_state == "GOING_TO_SHELF":
        goal = current_shelf
    elif task_state == "GOING_TO_DELIVERY":
        goal = current_delivery
    elif task_state == "GOING_TO_CHARGE":
        goal = current_charger
    
    distance_to_goal = euclidean_distance((x, y), (goal['x'], goal['z'])) if goal else 0
    
    telemetry = {
        "robot_id": ROBOT_NAME,
        "run_id": SIMULATION_RUN_ID,
        "robot_icon": ICON,
        "position_x": round(x, 4),
        "position_y": round(y, 4),
        "position_z": 0,
        "battery": round(battery_level, 2),  # Will be mapped to battery_level by server
        "task_state": task_state,
        "status": "active",
        "current_goal": goal['id'] if goal else None,
        "distance_to_goal": round(distance_to_goal, 3),
        "tasks_completed": tasks_completed,
        "task_failures": task_failures,
        "total_energy": round(total_energy_consumed, 3),
    }
    
    try:
        requests.post(
            f"{AI_SERVER_URL}/api/monitor/telemetry",
            json=telemetry,
            timeout=0.5
        )
        
        requests.post(
            f"{BACKEND_URL}/api/telemetry/{SIMULATION_RUN_ID}",
            json=telemetry,
            timeout=0.5
        )
    except:
        pass

# ============================================
# STUCK DETECTION (IMPROVED)
# ============================================

def detect_and_recover_stuck():
    global stuck_counter, last_position, task_failures, recovery_attempts
    
    current_pos = get_gps_position()
    
    if last_position:
        movement = euclidean_distance(last_position, current_pos)
        
        # Only count as stuck if in motion AND not moving
        if movement < 0.005 and task_state.startswith("GOING_"):
            stuck_counter += 1
            
            # Increased threshold to 250 steps (~25 seconds)
            if stuck_counter > 250:
                stuck_counter = 0
                task_failures += 1
                recovery_attempts += 1
                
                # Give up after 5 recovery attempts
                if recovery_attempts > 5:
                    print(f"{ICON} ❌ Task failed after 5 recovery attempts - reassigning")
                    recovery_attempts = 0
                    request_task_assignment()
                    return True
                
                print(f"{ICON} 🚨 STUCK - Recovery attempt #{recovery_attempts}")
                
                if BACKEND_AVAILABLE:
                    try:
                        requests.post(
                            f"{AI_SERVER_URL}/api/robots/stuck",
                            json={
                                "robot_id": ROBOT_NAME,
                                "position": {"x": current_pos[0], "y": current_pos[1]},
                                "task_state": task_state,
                                "failures": task_failures
                            },
                            timeout=1
                        )
                    except:
                        pass
                
                perform_recovery()
                return True
        else:
            stuck_counter = 0
    
    last_position = current_pos
    return False

def perform_recovery():
    """Smarter recovery maneuver"""
    # Reverse
    left_motor.setVelocity(-MAX_SPEED * 0.6)
    right_motor.setVelocity(-MAX_SPEED * 0.6)
    for _ in range(40):
        robot.step(TIME_STEP)
    
    # Random turn direction
    if random.random() > 0.5:
        left_motor.setVelocity(MAX_SPEED * 0.8)
        right_motor.setVelocity(-MAX_SPEED * 0.8)
    else:
        left_motor.setVelocity(-MAX_SPEED * 0.8)
        right_motor.setVelocity(MAX_SPEED * 0.8)
    
    for _ in range(30):
        robot.step(TIME_STEP)

# ============================================
# STATE MACHINE
# ============================================

def update_state_machine():
    global task_state, battery_level, wait_counter, tasks_completed
    global current_charger, total_energy_consumed, total_distance_traveled
    
    current_pos = get_gps_position()
    if last_position:
        total_distance_traveled += euclidean_distance(last_position, current_pos)
    
    if detect_and_recover_stuck():
        return
    
    if battery_level < CRITICAL_BATTERY and task_state not in ["GOING_TO_CHARGE", "CHARGING"]:
        print(f"{ICON} ⚠️  LOW BATTERY: {battery_level:.1f}%")
        current_charger = min(CHARGING_STATIONS, 
                             key=lambda c: euclidean_distance(current_pos, (c['x'], c['z'])))
        task_state = "GOING_TO_CHARGE"
        return
    
    # STATE MACHINE
    
    if task_state == "INITIALIZING":
        left_motor.setVelocity(0.0)
        right_motor.setVelocity(0.0)
        wait_counter += 1
        
        if wait_counter > startup_delay:
            request_task_assignment()
    
    elif task_state == "GOING_TO_PICKUP":
        l, r = navigate_to_goal(current_pickup)
        left_motor.setVelocity(l)
        right_motor.setVelocity(r)
        
        if is_in_zone(current_pickup):
            task_state = "AT_PICKUP"
            wait_counter = 0
            left_motor.setVelocity(0.0)
            right_motor.setVelocity(0.0)
            print(f"{ICON} ✅ At {current_pickup['id']}")
    
    elif task_state == "AT_PICKUP":
        wait_counter += 1
        if wait_counter > 40:
            task_state = "GOING_TO_SHELF"
            wait_counter = 0
            print(f"{ICON} 📦 Loaded → {current_shelf['id']}")
    
    elif task_state == "GOING_TO_SHELF":
        l, r = navigate_to_goal(current_shelf)
        left_motor.setVelocity(l)
        right_motor.setVelocity(r)
        
        if is_in_zone(current_shelf):
            task_state = "AT_SHELF"
            wait_counter = 0
            left_motor.setVelocity(0.0)
            right_motor.setVelocity(0.0)
            print(f"{ICON} ✅ At {current_shelf['id']}")
    
    elif task_state == "AT_SHELF":
        wait_counter += 1
        if wait_counter > 40:
            task_state = "GOING_TO_DELIVERY"
            wait_counter = 0
            print(f"{ICON} 📦 Stored → {current_delivery['id']}")
    
    elif task_state == "GOING_TO_DELIVERY":
        l, r = navigate_to_goal(current_delivery)
        left_motor.setVelocity(l)
        right_motor.setVelocity(r)
        
        if is_in_zone(current_delivery):
            task_state = "AT_DELIVERY"
            wait_counter = 0
            left_motor.setVelocity(0.0)
            right_motor.setVelocity(0.0)
            print(f"{ICON} ✅ At {current_delivery['id']}")
    
    elif task_state == "AT_DELIVERY":
        wait_counter += 1
        if wait_counter > 40:
            tasks_completed += 1
            task_duration = robot.getTime() - task_start_time
            
            print(f"\n{ICON} ═══════════════════════════")
            print(f"{ICON} ✅ TASK #{tasks_completed} DONE")
            print(f"{ICON} Time: {task_duration:.1f}s")
            print(f"{ICON} Battery: {battery_level:.1f}%")
            print(f"{ICON} ═══════════════════════════\n")
            
            report_task_completion(success=True)
            wait_counter = 0
            
            if battery_level > CRITICAL_BATTERY:
                request_task_assignment()
            else:
                current_charger = min(CHARGING_STATIONS,
                                    key=lambda c: euclidean_distance(current_pos, (c['x'], c['y'])))
                task_state = "GOING_TO_CHARGE"
    
    elif task_state == "GOING_TO_CHARGE":
        l, r = navigate_to_goal(current_charger)
        left_motor.setVelocity(l)
        right_motor.setVelocity(r)
        
        if is_in_zone(current_charger):
            task_state = "CHARGING"
            left_motor.setVelocity(0.0)
            right_motor.setVelocity(0.0)
            print(f"{ICON} ⚡ Charging at {current_charger['id']}")
    
    elif task_state == "CHARGING":
        battery_level += BATTERY_CHARGE_RATE
        
        if battery_level >= 100.0:
            battery_level = 100.0
            print(f"{ICON} 🔋 Charged!")
            request_task_assignment()

# ============================================
# MAIN LOOP
# ============================================

print(f"\n{ICON} {'='*60}")
print(f"{ICON} WAREHOUSE SYSTEM - Run #{RUN_NUMBER}")
print(f"{ICON} Calibrated zones loaded")
print(f"{ICON} {'='*60}\n")

telemetry_counter = 0

while robot.step(TIME_STEP) != -1:
    
    if task_state != "CHARGING":
        battery_level -= BATTERY_DRAIN_RATE
        total_energy_consumed += BATTERY_DRAIN_RATE
    
    update_state_machine()
    
    telemetry_counter += 1
    if telemetry_counter >= 200:
        send_telemetry()
        telemetry_counter = 0