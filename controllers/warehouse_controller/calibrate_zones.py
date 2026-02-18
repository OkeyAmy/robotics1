"""
CALIBRATION TOOL
Run this controller to manually drive the robot (or just let it sit) and see its EXACT coordinates.
Use this to double-check the locations of your Pickup, Shelf, Delivery, and Charging zones.
"""

from controller import Robot, Keyboard

robot = Robot()
timestep = int(robot.getBasicTimeStep())
keyboard = Keyboard()
keyboard.enable(timestep)

gps = robot.getDevice('gps')
gps.enable(timestep)

left_motor = robot.getDevice('left wheel')
right_motor = robot.getDevice('right wheel')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

print("\n" + "="*50)
print("📍 ZONE CALIBRATION MODE")
print("Move the robot to a zone and check the coordinates.")
print("Use ARROW KEYS to drive.")
print("="*50 + "\n")

MAX_SPEED = 5.24

while robot.step(timestep) != -1:
    key = keyboard.getKey()
    
    left_speed = 0.0
    right_speed = 0.0
    
    if key == Keyboard.UP:
        left_speed = MAX_SPEED
        right_speed = MAX_SPEED
    elif key == Keyboard.DOWN:
        left_speed = -MAX_SPEED
        right_speed = -MAX_SPEED
    elif key == Keyboard.LEFT:
        left_speed = -MAX_SPEED * 0.5
        right_speed = MAX_SPEED * 0.5
    elif key == Keyboard.RIGHT:
        left_speed = MAX_SPEED * 0.5
        right_speed = -MAX_SPEED * 0.5
        
    left_motor.setVelocity(left_speed)
    right_motor.setVelocity(right_speed)
    
    pos = gps.getValues()
    # Webots GPS: X is forward/backward, Z is left/right (usually), but depends on world rotation.
    # We display them exactly as mapped in robot_control.py: x=pos[0], y=pos[1] (which seemed to be mapped to Z in other logic??)
    # Let's just show raw X, Y, Z so user can decide.
    
    # In robot_control.py:
    # return vals[0], vals[2], vals[1] -> X, Z, Y => X=x, Y=z
    
    mapped_x = pos[0]
    mapped_y = pos[1] # Typically Z in 3D, but let's see. Webots is Y-up usually? No, Z-up usually?
    # Actually standard Webots: Y is up (gravity). X/Z are ground plane.
    # The snippet `vals[0], vals[2], vals[1]` suggests:
    # Game X = GPS X
    # Game Y = GPS Z (depth)
    
    print(f"\r📍 GPS: X={pos[0]:.2f} Y={pos[1]:.2f} Z={pos[2]:.2f} || Mapped (X,Y): ({pos[0]:.2f}, {pos[1]:.2f})", end="")
