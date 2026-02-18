"""
╔══════════════════════════════════════════════════════════════════════╗
║         ZONE CALIBRATION TOOL  —  FOR YOUR DELIVERY ROBOT           ║
║         Finds correct X / Z values for all your zones               ║
╠══════════════════════════════════════════════════════════════════════╣
║  QUICK SETUP (AUTO-CALIBRATION)                                      ║
║  1. In Webots Scene Tree, click your robot                           ║
║  2. Look at "translation" field (e.g., "0 0.1 0")                    ║
║  3. Set ROBOT_START_X to the 1st number, ROBOT_START_Z to 3rd       ║
║  4. Run this controller - it auto-calibrates on startup!             ║
║  5. Drive around and press E at zone edges, P to log each zone       ║
║  6. Press Q to save - done!                                          ║
╠══════════════════════════════════════════════════════════════════════╣
║  KEYBOARD CONTROLS                                                   ║
║  Arrow Keys   Drive the robot                                        ║
║  E            Mark an edge point of the current zone object          ║
║  P            Log current zone (auto-fits circle from edge points)   ║
║  N            Cycle to next zone name                                ║
║  + / -        Increase / decrease manual radius (fallback)           ║
║  R            Print all zones logged so far                          ║
║  Q            Save and quit                                          ║
║  C            Manual calibration (if AUTO_CALIBRATE is False)        ║
╚══════════════════════════════════════════════════════════════════════╝

  WHY YOU NEED THIS:
  ─────────────────
  In Webots the ground plane is X and Z  (NOT X and Y).
  Y is height (up/down).  Your current zone dicts use "x" and "y"
  but "y" should actually be "z".  This tool reads the GPS correctly
  (gps[0] = X,  gps[2] = Z)  and outputs the right values so your
  robot can actually detect when it is inside a zone.

  NOTE: Make sure your robot has devices named exactly:
        'gps'         → GPS sensor
        'compass'     → Compass sensor
        'left wheel'  → left drive motor
        'right wheel' → right drive motor
  Change the names below if yours differ.
"""

from controller import Robot, Keyboard
import math, json
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# DEVICE NAMES — change these if your robot uses different names
# ─────────────────────────────────────────────────────────────────────────────
GPS_DEVICE     = 'gps'
COMPASS_DEVICE = 'compass'
LEFT_MOTOR     = 'left wheel'
RIGHT_MOTOR    = 'right wheel'
MAX_SPEED      = 5.24

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-CALIBRATION SETUP
# Set this to your robot's STARTING position from the Webots Scene Tree.
# When the robot starts, it will automatically calibrate the GPS offset.
# 
# HOW TO SET THIS UP:
# 1. In Webots Scene Tree, click your robot node
# 2. Look at the "translation" field (should show 3 numbers like: 0 0.1 0)
# 3. Copy the 1st number to ROBOT_START_X below
# 4. Copy the 3rd number to ROBOT_START_Z below
# 5. Run the calibration tool - it will auto-calibrate on startup!
# ─────────────────────────────────────────────────────────────────────────────
AUTO_CALIBRATE = True          # Set to False to use manual calibration (press C)
ROBOT_START_X = 0.0            # ← SET THIS: Robot's starting Translation X
ROBOT_START_Z = 0.0            # ← SET THIS: Robot's starting Translation Z

# ─────────────────────────────────────────────────────────────────────────────
# ZONE NAMES  —  These match YOUR zone IDs exactly, in order.
# Press N to cycle through them one by one while calibrating.
# ─────────────────────────────────────────────────────────────────────────────
ZONE_NAMES = [
    # Pickup zones
    "pickup_A",
    "pickup_B",
    "pickup_C",
    # Shelf zones
    "shelf_1",
    "shelf_2",
    "shelf_3",
    # Delivery zones
    "delivery_north",
    "delivery_south",
    # Charging stations
    "charger_1",
    "charger_2",
]

# ─────────────────────────────────────────────────────────────────────────────
# ROBOT SETUP
# ─────────────────────────────────────────────────────────────────────────────
robot    = Robot()
ts       = int(robot.getBasicTimeStep())

keyboard = Keyboard()
keyboard.enable(ts)

gps = robot.getDevice(GPS_DEVICE)
gps.enable(ts)

compass = robot.getDevice(COMPASS_DEVICE)
compass.enable(ts)

left_motor  = robot.getDevice(LEFT_MOTOR)
right_motor = robot.getDevice(RIGHT_MOTOR)
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

# ─────────────────────────────────────────────────────────────────────────────
# OFFSET CALIBRATION
#   In Webots, GPS world-frame coords may not match Translation coords
#   if your robot has a parent node with its own transform.
#   Press C while standing at a point whose Translation you know to fix this.
# ─────────────────────────────────────────────────────────────────────────────
offset_x = -3.40674
offset_z = 0.194976
calibrated = True

def gps_to_xz(gps_vals):
    """
    Returns the calibrated ground-plane position.
    gps_vals[0] = X axis
    gps_vals[1] = Y axis (height — we ignore this)
    gps_vals[2] = Z axis  ← this is your missing coordinate!
    """
    return gps_vals[0] - offset_x, gps_vals[2] - offset_z

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-CALIBRATE ON STARTUP (if enabled)
# ─────────────────────────────────────────────────────────────────────────────
if AUTO_CALIBRATE:
    # Wait a few steps for sensors to initialize
    for _ in range(5):
        robot.step(ts)
    
    initial_gps = gps.getValues()
    offset_x = initial_gps[0] - ROBOT_START_X
    offset_z = initial_gps[2] - ROBOT_START_Z
    calibrated = True
    
    wx, wz = gps_to_xz(initial_gps)
    print("\n" + "="*68)
    print("  ✓ AUTO-CALIBRATION COMPLETE")
    print("="*68)
    print(f"  GPS at startup:        X={initial_gps[0]:.4f}  Z={initial_gps[2]:.4f}")
    print(f"  Known robot position:  X={ROBOT_START_X:.4f}  Z={ROBOT_START_Z:.4f}")
    print(f"  Calculated offsets:    offset_x={offset_x:.4f}  offset_z={offset_z:.4f}")
    print(f"  Verification:          calibrated pos = ({wx:.4f}, {wz:.4f})")
    print(f"                         should match   = ({ROBOT_START_X}, {ROBOT_START_Z})")
    print("="*68 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# HEADING HELPER
# ─────────────────────────────────────────────────────────────────────────────
def get_heading(comp):
    cx, _, cz = comp
    deg = math.degrees(math.atan2(cx, cz))
    return (deg + 360) % 360

def cardinal(deg):
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(deg / 45) % 8]

# ─────────────────────────────────────────────────────────────────────────────
# CIRCLE FIT (Taubin least-squares)
#   Drive around an object pressing E at edge points.
#   This maths finds the best-fit circle through those points,
#   giving you the true centre (x, z) and radius automatically.
# ─────────────────────────────────────────────────────────────────────────────
def fit_circle(points):
    n = len(points)
    if n < 2:
        return None, None, None

    if n == 2:
        cx = (points[0][0] + points[1][0]) / 2
        cy = (points[0][1] + points[1][1]) / 2
        r  = math.hypot(points[1][0] - points[0][0],
                        points[1][1] - points[0][1]) / 2
        return cx, cy, r

    # Centroid shift for numerical stability
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    u  = [p[0] - mx for p in points]
    v  = [p[1] - my for p in points]
    z  = [u[i]**2 + v[i]**2 for i in range(n)]

    Suu = sum(u[i]**2   for i in range(n))
    Svv = sum(v[i]**2   for i in range(n))
    Suv = sum(u[i]*v[i] for i in range(n))
    Su  = sum(u[i]      for i in range(n))
    Sv  = sum(v[i]      for i in range(n))
    Suz = sum(u[i]*z[i] for i in range(n))
    Svz = sum(v[i]*z[i] for i in range(n))
    Sz  = sum(z[i]      for i in range(n))

    A = [
        [2*Suu, 2*Suv, Su],
        [2*Suv, 2*Svv, Sv],
        [2*Su,  2*Sv,  n ],
    ]
    rhs = [Suz + sum(u[i]*v[i]**2 for i in range(n)),
           Svz + sum(v[i]*u[i]**2 for i in range(n)),
           Sz]

    def det3(m):
        return (m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1])
              - m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0])
              + m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0]))

    D = det3(A)
    if abs(D) < 1e-10:
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        return (max(xs)+min(xs))/2+mx, (max(ys)+min(ys))/2+my, \
               math.hypot(max(xs)-min(xs), max(ys)-min(ys))/2

    def sub_col(m, col, vec):
        return [[vec[r] if c==col else m[r][c] for c in range(3)] for r in range(3)]

    uc = det3(sub_col(A, 0, rhs)) / D
    vc = det3(sub_col(A, 1, rhs)) / D
    dc = det3(sub_col(A, 2, rhs)) / D
    r  = math.sqrt(max(uc**2 + vc**2 - dc, 0.0))
    return uc + mx, vc + my, r

# ─────────────────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────────────────
name_idx      = 0
current_name  = ZONE_NAMES[name_idx]
manual_radius = 0.60          # default matches your current radius values
edge_points   = []
logged_zones  = {}            # keyed by zone id
step_count    = 0

# ─────────────────────────────────────────────────────────────────────────────
# STARTUP BANNER
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*68)
print("  DELIVERY ROBOT — ZONE CALIBRATION TOOL")
print("="*68)
print("  Your current zone 'y' values (0.19 / 0.20) are actually HEIGHT.")
print("  This tool finds the correct X and Z ground-plane values.")
print("-"*68)
if AUTO_CALIBRATE and calibrated:
    print("  ✓ Auto-calibration is ACTIVE - you can drive immediately!")
    print("  STEP 1  Drive to each zone object edge → press E (3+ times)")
    print("  STEP 2  Press P to log that zone → repeat for all 10 zones")
    print("  STEP 3  Press N to move to next zone name before each object")
    print("  STEP 4  Press Q to save zones_output.py — paste into your code")
else:
    print("  STEP 1  Drive to a spot whose Translation you know → press C")
    print("  STEP 2  Drive to each zone object edge → press E  (3+ times)")
    print("  STEP 3  Press P to log that zone  →  repeat for all 10 zones")
    print("  STEP 4  Press N to move to next zone name before each object")
    print("  STEP 5  Press Q to save zones_output.py — paste into your code")
print("="*68)
print(f"\n  Starting with zone: [{current_name}]")
print(f"  Remaining zones   : {ZONE_NAMES[1:]}\n")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
while robot.step(ts) != -1:
    step_count += 1
    key = keyboard.getKey()

    # ── Drive controls ───────────────────────────────────────────────────────
    ls = rs = 0.0
    if   key == Keyboard.UP:    ls = rs =  MAX_SPEED
    elif key == Keyboard.DOWN:  ls = rs = -MAX_SPEED
    elif key == Keyboard.LEFT:  ls = -MAX_SPEED*0.5; rs =  MAX_SPEED*0.5
    elif key == Keyboard.RIGHT: ls =  MAX_SPEED*0.5; rs = -MAX_SPEED*0.5
    left_motor.setVelocity(ls)
    right_motor.setVelocity(rs)

    # ── Read sensors ─────────────────────────────────────────────────────────
    raw     = gps.getValues()
    heading = get_heading(compass.getValues())
    rx, rz  = gps_to_xz(raw)   # calibrated ground-plane position
    ry      = raw[1]            # height (Y) — just for display

    # ── Live HUD (updates every 8 steps) ─────────────────────────────────────
    if step_count % 8 == 0:
        cal_tag  = "CAL-OK ✓" if calibrated else "NOT-CAL ✗"
        edge_tag = f"{len(edge_points)} edges" if edge_points else "no edges"
        logged   = len(logged_zones)
        print(
            f"\r  Pos: X={rx:7.3f}  Z={rz:7.3f}  Y(height)={ry:.3f}"
            f"  |  {heading:5.1f}° {cardinal(heading):<2}"
            f"  |  [{cal_tag}] [{edge_tag}] [{current_name}]"
            f"  |  {logged}/{len(ZONE_NAMES)} logged   ",
            end="", flush=True
        )

    # ── C — Calibrate offset ─────────────────────────────────────────────────
    if key in (ord('C'), ord('c')):
        print("\n\n  CALIBRATE: Stand the robot at a spot whose Translation you know.")
        print("  Open Webots Scene Tree → click the robot/floor/any node")
        print("  → look at its Translation field → you need the X and Z values.\n")
        try:
            tx = float(input("  Known Translation X: "))
            tz = float(input("  Known Translation Z: "))
        except ValueError:
            print("  ✗ Invalid input — calibration skipped.\n")
        else:
            cur      = gps.getValues()
            offset_x = cur[0] - tx
            offset_z = cur[2] - tz
            calibrated = True
            wx, wz = gps_to_xz(cur)
            print(f"\n  ✓ Offsets saved:  offset_x={offset_x:.4f}  offset_z={offset_z:.4f}")
            print(f"  Verification: calibrated position = ({wx:.4f}, {wz:.4f})")
            print(f"  Should match your known value    = ({tx}, {tz})\n")

    # ── E — Mark edge point ───────────────────────────────────────────────────
    elif key in (ord('E'), ord('e')):
        ex, ez = gps_to_xz(gps.getValues())
        edge_points.append((ex, ez))
        n = len(edge_points)
        if n >= 2:
            cx, cz, r = fit_circle(edge_points)
            fit_info = (f"  → fitted centre=({cx:.3f}, {cz:.3f})  radius={r:.3f} m"
                        if cx is not None else "")
        else:
            fit_info = "  → need 1 more point for first estimate"
        print(f"\n  EDGE [{n}] at X={ex:.4f}  Z={ez:.4f}{fit_info}\n")

    # ── P — Log zone ──────────────────────────────────────────────────────────
    elif key in (ord('P'), ord('p')):
        if len(edge_points) >= 2:
            cx, cz, radius = fit_circle(edge_points)
            method = f"circle-fit from {len(edge_points)} edge points"
        elif len(edge_points) == 1:
            cx, cz = edge_points[0]
            radius = manual_radius
            method = "single edge point + manual radius"
        else:
            cx, cz = gps_to_xz(gps.getValues())
            radius = manual_radius
            method = "robot centre + manual radius"

        logged_zones[current_name] = {
            "id":     current_name,
            "x":      round(cx, 4),
            "z":      round(cz, 4),
            "radius": round(radius, 4),
            "_method": method,
        }
        edge_points = []   # reset for next zone

        print(f"\n\n  ✅ ✅ ✅  ZONE SAVED  ✅ ✅ ✅")
        print(f"  {current_name:20s}  x={logged_zones[current_name]['x']:8.4f}  "
              f"z={logged_zones[current_name]['z']:8.4f}  "
              f"radius={logged_zones[current_name]['radius']:.4f} m")
        print(f"  ({method})")
        print(f"  Progress: {len(logged_zones)}/{len(ZONE_NAMES)} zones complete")
        
        remaining = [n for n in ZONE_NAMES if n not in logged_zones]
        if remaining:
            print(f"  Still needed: {remaining[:3]}{'...' if len(remaining) > 3 else ''}")
        else:
            print(f"  🎉 ALL ZONES DONE! Press Q to save.")
        print()

        # Auto-advance to next zone name
        if name_idx + 1 < len(ZONE_NAMES):
            name_idx    += 1
            current_name = ZONE_NAMES[name_idx]
            print(f"  → Auto-advanced to next zone: [{current_name}]\n")

    # ── + / - — Adjust manual radius ─────────────────────────────────────────
    elif key in (ord('+'), ord('=')):
        manual_radius = round(manual_radius + 0.05, 2)
        print(f"\n  Manual radius → {manual_radius:.2f} m\n")
    elif key == ord('-'):
        manual_radius = max(0.05, round(manual_radius - 0.05, 2))
        print(f"\n  Manual radius → {manual_radius:.2f} m\n")

    # ── N — Next zone name ────────────────────────────────────────────────────
    elif key in (ord('N'), ord('n')):
        name_idx     = (name_idx + 1) % len(ZONE_NAMES)
        current_name = ZONE_NAMES[name_idx]
        edge_points  = []
        print(f"\n  Zone → [{current_name}]  (edge points reset)\n")

    # ── R — Print report ──────────────────────────────────────────────────────
    elif key in (ord('R'), ord('r')):
        missing = [n for n in ZONE_NAMES if n not in logged_zones]
        print("\n" + "-"*60)
        print(f"  {len(logged_zones)}/{len(ZONE_NAMES)} ZONES LOGGED")
        print("-"*60)
        for zid, z in logged_zones.items():
            print(f"  {zid:20s}  x={z['x']:8.4f}  z={z['z']:8.4f}  "
                  f"r={z['radius']:.4f} m")
        if missing:
            print(f"\n  Still needed: {missing}")
        print("-"*60 + "\n")

    # ── Q — Save and quit ─────────────────────────────────────────────────────
    elif key in (ord('Q'), ord('q')):
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ── JSON backup ──────────────────────────────────────────────────────
        jfile = f"zones_{ts_str}.json"
        with open(jfile, "w") as f:
            json.dump({
                "offset": {"offset_x": offset_x, "offset_z": offset_z},
                "zones":  logged_zones
            }, f, indent=2)

        # ── Python snippet  (drop-in replacement for your zone dicts) ────────
        pfile = "zones_output.py"
        with open(pfile, "w") as f:
            f.write("# ═══════════════════════════════════════════════════════════════════\n")
            f.write("# AUTO-GENERATED ZONE COORDINATES\n")
            f.write("# Copy and paste these directly into your robot controller\n")
            f.write("# ═══════════════════════════════════════════════════════════════════\n\n")
            
            # Check if any zones were logged
            if not logged_zones:
                f.write("# ⚠️  ⚠️  ⚠️  NO ZONES WERE LOGGED!  ⚠️  ⚠️  ⚠️\n\n")
                f.write("# You pressed Q without logging any zones.\n")
                f.write("# To log zones, you must:\n")
                f.write("#   1. Drive to each zone object\n")
                f.write("#   2. Press E at 3+ points around the edge\n")
                f.write("#   3. Press P to log that zone\n")
                f.write("#   4. Repeat for all 10 zones\n")
                f.write("#   5. Then press Q to save\n\n")
                f.write(f"# Your GPS offset was calculated: offset_x={offset_x:.4f}, offset_z={offset_z:.4f}\n")
                f.write("# Re-run the calibration tool and remember to press P after each zone!\n")
            else:
                f.write(f"# Zones logged: {len(logged_zones)}/{len(ZONE_NAMES)}\n")
                f.write(f"# GPS Offset: offset_x={offset_x:.4f}, offset_z={offset_z:.4f}\n\n")

                # Helper to write one group in familiar format
                def write_group(name, ids):
                    entries = [logged_zones[i] for i in ids if i in logged_zones]
                    if not entries:
                        f.write(f"# {name} = []  # ← NOT CALIBRATED YET\n\n")
                        return
                    f.write(f"{name} = [\n")
                    for z in entries:
                        f.write(f"    {{\"id\": \"{z['id']}\", "
                                f"\"x\": {z['x']}, "
                                f"\"z\": {z['z']}, "
                                f"\"radius\": {z['radius']}}},\n")
                    f.write("]\n\n")

                write_group("PICKUP_ZONES",      ["pickup_A","pickup_B","pickup_C"])
                write_group("SHELF_ZONES",       ["shelf_1","shelf_2","shelf_3"])
                write_group("DELIVERY_ZONES",    ["delivery_north","delivery_south"])
                write_group("CHARGING_STATIONS", ["charger_1","charger_2"])
                
                f.write("# ═══════════════════════════════════════════════════════════════════\n")
                f.write("# HOW TO USE:\n")
                f.write("# 1. Copy the zone lists above\n")
                f.write("# 2. Paste them into your robot controller\n")
                f.write("# 3. They replace your existing PICKUP_ZONES, SHELF_ZONES, etc.\n")
                f.write("# ═══════════════════════════════════════════════════════════════════\n")

        print(f"\n\n  ✓ Saved JSON  → {jfile}")
        print(f"  ✓ Saved zones → {pfile}")
        print("\n  Open zones_output.py — it has your corrected zone dicts.")
        print("  Replace your old PICKUP_ZONES / SHELF_ZONES / etc. with these.\n")
        break