import sys
import time
import threading
import serial
import keyboard

# ---------------- Configuration ----------------
SERIAL_PORT = "COM5"  # <- Check your device manager
BAUDRATE = 9600
NUM_SERVOS = 6

# ---------------- Serial Connection ----------------
try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    time.sleep(2) # Allow MCU to reset
except serial.SerialException as e:
    print(f"[ERROR] Could not open serial port {SERIAL_PORT}: {e}")
    sys.exit(1)
    
general_directions_demonstration = ['L', 'R', 'R', 'L', 'L', 'R']
servo_indices = [0, 1, 2, 3, 4]

# ---------------- Tank Controller (Existing) --------jkjjj--------
class TankController:
    def __init__(self, serial_obj):
        self.ser            = serial_obj
        self.max_pwm        = 255
        self.exp_factor     = 1.8
        self.smooth_step    = 0.08
        self.turn_base      = 0.7
        self.boost_factor   = 1.5
        self.slow_factor    = 0.5

        self.current_left   = 0.0
        self.current_right  = 0.0
        self.manual_left    = 0.0
        self.manual_right   = 0.0

        self.mode           = "Neutral"
        self.key_states     = {"W": False, "S": False, "A": False, "D": False}

    def apply_exponential(self, v: float) -> int:
        sign = 1 if v >= 0 else -1
        pwm = sign * int((abs(v) ** self.exp_factor) * self.max_pwm)
        return max(-self.max_pwm, min(self.max_pwm, pwm))

    def compute_targets(self):
        fwd, turn = 0.0, 0.0
        factor = 1.0

        # Keyboard detection
        self.key_states = {"W": False, "S": False, "A": False, "D": False}
        if keyboard.is_pressed("w"): fwd += 1; self.key_states["W"] = True
        if keyboard.is_pressed("s"): fwd -= 1; self.key_states["S"] = True
        if keyboard.is_pressed("a"): turn += 1; self.key_states["A"] = True
        if keyboard.is_pressed("d"): turn -= 1; self.key_states["D"] = True

        if keyboard.is_pressed("shift"): factor = self.boost_factor; self.mode = "BOOST"
        elif keyboard.is_pressed("ctrl"): factor = self.slow_factor; self.mode = "SLOW"
        else: self.mode = "Neutral"

        adaptive_turn = self.turn_base * (1 - 0.5 * abs(fwd))
        if fwd != 0:
            left = fwd + turn * adaptive_turn * abs(fwd)
            right = fwd - turn * adaptive_turn * abs(fwd)
        elif turn != 0:
            left = -turn * self.turn_base
            right = turn * self.turn_base
        else:
            left, right = 0.0, 0.0

        left = max(-1, min(1, left)) * factor
        right = max(-1, min(1, right)) * factor

        tl = self.apply_exponential(left)
        tr = self.apply_exponential(right)
        return tl, tr

    def smooth(self, cur, tgt):
        diff = tgt - cur
        if abs(diff) < 1: return float(tgt)
        return cur + diff * self.smooth_step

    def update(self):
        tl, tr = self.compute_targets()
        self.current_left = self.smooth(self.current_left, tl)
        self.current_right = self.smooth(self.current_right, tr)
        try:
            self.ser.write(f"{int(self.current_left)},{int(self.current_right)}\n".encode())
        except Exception:
            pass

    def stop(self):
        try:
            self.ser.write(b"0,0\n")
        except Exception:
            pass
        self.current_left = 0.0
        self.current_right = 0.0

# ---------------- Robotic Hand Driver ----------------
class RoboticHand:
    def __init__(self, serial_obj, num_servos=6):
        self.ser = serial_obj
        self.num_servos = num_servos
        # Track estimated angles for UI only; assumes open loop control
        self.angles = [90.0] * num_servos 
        self.sensitivity = [1.0] * num_servos
        self.lock = threading.Lock()

    def send_step(self, idx: int, direction: str):
        """Sends a single incremental step command."""
        with self.lock:
            cmd = f"S{idx+1}{direction}\n"
            try:
                self.ser.write(cmd.encode())
            except Exception:
                pass
            
            # Update local estimation
            delta = self.sensitivity[idx]
            if direction == "L":
                self.angles[idx] = max(0.0, self.angles[idx] - delta)
            elif direction == "R":
                self.angles[idx] = min(180.0, self.angles[idx] + delta)

    def stop_servo(self, idx: int):
        """Sends neutral command to stop servo movement."""
        # Note: Depending on MCU code, 'N' might stop movement or detach
        with self.lock:
            cmd = f"S{idx+1}N\n"
            try:
                self.ser.write(cmd.encode())
            except Exception:
                pass

# ---------------- Automation API ----------------
class HandAutomationAPI:
    """
    Manages automated scripts for the robotic hand.
    Adheres to safety principle: Automation can be overridden or stopped immediately.
    """
    def __init__(self, hand_obj: RoboticHand):
        self.hand = hand_obj
        self.active_thread = None
        self.stop_flag = threading.Event()
        self.current_status = "Manual"

    def _run_sequence(self, sequence_func, name):
        """Wrapper to run a sequence in a thread safely."""
        self.current_status = f"Auto: {name}"
        try:
            sequence_func()
        except Exception as e:
            print(f"[AUTO ERROR] {e}")
        finally:
            # Ensure all servos stop when sequence finishes or is aborted
            for i in range(self.hand.num_servos):
                self.hand.stop_servo(i)
            self.current_status = "Manual"
            self.stop_flag.clear()

    def start_script(self, script_name):
        """Public API to trigger a script by name."""
        if self.active_thread and self.active_thread.is_alive():
            return # Ignore if already running

        target_func = None
        if script_name == "WAVE":
            target_func = self.sequence_wave
        elif script_name == "GRAB":
            target_func = self.sequence_grab_lift
        elif script_name == "HOME":
            target_func = self.sequence_home
        elif script_name == "TESTALL":
            target_func = self.test_all_servos_at_once
        elif script_name == "TESTALL_AUTO":
            target_func = self.test_all_servos_at_once_at_same_time
        elif script_name == "TESTGRAB":
            target_func = self.test_hand_grabbing_manuever

        if target_func:
            self.stop_flag.clear()
            self.active_thread = threading.Thread(target=self._run_sequence, args=(target_func, script_name))
            self.active_thread.daemon = True
            self.active_thread.start()

    def abort(self):
        """Immediately signals any running automation to stop."""
        if self.active_thread and self.active_thread.is_alive():
            self.stop_flag.set()
            self.active_thread.join(timeout=0.5)

    def _move_duration(self, servo_idx, direction, duration_sec):
        """Helper: Moves a servo for a set time, checking for abort signal."""
        start_time = time.time()
        while time.time() - start_time < duration_sec:
            if self.stop_flag.is_set():
                return
            self.hand.send_step(servo_idx, direction)
            time.sleep(0.05) # Rate limiter for serial cmds
        self.hand.stop_servo(servo_idx)
        
    def _move_all_duration(self, servo_indices, direction, duration_sec):
        """
        Moves a list of servos simultaneously using a single control loop.
        This eliminates the need for threading and locks.
        """
        start_time = time.time()
        
        # Master Loop: Controls the timing for the entire group
        while time.time() - start_time < duration_sec:
            
            # Critical Safety Check
            if self.stop_flag.is_set():
                return

            # Rapidly iterate through all servos to send one step each
            for servo_idx in servo_indices:
                self.hand.send_step(servo_idx, direction)
            
            # Rate limiter: Determines the speed of the movement
            # 0.05s delay shared across the group
            time.sleep(0.05) 

        # Stop all servos safely after duration ends
        for servo_idx in servo_indices:
            self.hand.stop_servo(servo_idx)

    # --- Automation Script 1: Wave ---
    def sequence_wave(self):
        """Oscillates the base/wrist servo to simulate a wave."""
        # Servo 3 is wrist
        target_servo = 3 
        for _ in range(3): # Repeat 3 times
            if self.stop_flag.is_set(): break
            self._move_duration(target_servo, 'L', 1)
            time.sleep(1)
            self._move_duration(target_servo, 'R', 1)
            time.sleep(1)

    # --- Automation Script 2: Grab and Lift ---
    def sequence_grab_lift(self):
        """Opens claw, lowers arm, grabs, and lifts."""
        # Mapping (Hypothetical based on standard arm configs):
        # Servo 1 (idx 1): Shoulder/Lift
        # Servo 4 (idx 4): Claw/Gripper
        
        # 1. Open Gripper
        self._move_duration(4, 'L', 1.0) 
        time.sleep(0.2)
        
        # 2. Lower Arm
        self._move_duration(1, 'R', 0.8) # Adjust 'R' or 'L' based on mechanics
        time.sleep(0.2)
        
        # 3. Close Gripper (Grab)
        self._move_duration(4, 'R', 1.2) # Duration slightly longer to ensure grip
        time.sleep(0.2)
        
        # 4. Lift Arm
        self._move_duration(1, 'L', 0.8)
        
    def test_all_servos_at_once_at_same_time(self):
        """
        Executes simultaneous movement for servos 0-4 using a single loop.
        """
        automation_direction = ['R', 'L', 'R', 'L', 'L', 'R']

        for direction in automation_direction:
            if self.stop_flag.is_set(): break
            
            # Pass the list of servos to the master loop
            self._move_all_duration(servo_indices, direction, 1.0)
            
            time.sleep(1)
            
    def test_hand_grabbing_manuever(self):
        """
        Test hand grabbing capability
        """
        grabber_movement_sequence  = ['R', 'L']
        wrist_movement_sequence    = ['R']
        shoulder_movement_sequence = ['L', 'R'] 
        
        # START WITH THE SHOULDER MOVEMENT
        for direction in shoulder_movement_sequence[0]:       
            if self.stop_flag.is_set(): break
            self._move_all_duration(0, direction, 1.0)
            time.sleep(1)
            
        # START MOVEMENT WITH THE WRIST TO ALIGN HORIZONTALLY            
        for direction in wrist_movement_sequence[0]:
            if self.stop_flag.is_set(): break
            self._move_all_duration(0, direction, 1.0)
            time.sleep(1)
            
        # START PICKING
        for direction in grabber_movement_sequence[0]:
            if self.stop_flag.is_set(): break
            self._move_all_duration(0, direction, 1.0)
            time.sleep(1)
            
        # RETRACT THE SHOULDER
        for direction in shoulder_movement_sequence[1]:       
            if self.stop_flag.is_set(): break
            self._move_all_duration(0, direction, 1.0)
            time.sleep(1)
            
    def test_all_servos_at_once(self):
        """Test every servo in one ago automation"""
        
        # Shoulder Horizontal
        for direction in general_directions_demonstration:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(0, direction, 1.0)
            time.sleep(1)

        # Shoulder Vertical5
        verticalShoulder_directions = ['R', 'L']
        for direction in verticalShoulder_directions:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(1, direction, 1.0)
            time.sleep(1)
            
        # Elbow
        for direction in general_directions_demonstration:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(2, direction, 1.0)
            time.sleep(1)
            
        # Wrist
        for direction in general_directions_demonstration:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(3, direction, 1.0)
            time.sleep(1)
        
        # Hands
        for direction in general_directions_demonstration:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(4, direction, 1.0)
            time.sleep(1)
            
    # --- Automation Script 3: Home/Reset ---
    def sequence_home(self):
        """ default the servos to neutral position """
        
        # Elbow
        for direction in general_directions_demonstration[0]:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(2, direction, 1.5)
            time.sleep(1.5)
            
        # Wrist
        for direction in general_directions_demonstration[0]:
            if self.stop_flag.is_set(): break  # Critical Safety Check
            self._move_duration(3, direction, 1.0)
            time.sleep(1)
        

# ---------------- Input Monitor ----------------
def input_monitor(hand: RoboticHand, automator: HandAutomationAPI):
    """
    Handles both Manual and Automated inputs.
    """
    key_map = {
        'u': (0, 'L'), 'y': (0, 'R'),
        'j': (1, 'L'), 'h': (1, 'R'),
        'n': (2, 'L'), 'm': (2, 'R'),
        'o': (3, 'L'), 'i': (3, 'R'),
        'l': (4, 'L'), 'k': (4, 'R')
    }
    pressed = {k: False for k in key_map.keys()}
    
    while True:
        if keyboard.is_pressed("esc"):
            break

        # -- Automation Triggers --
        # Only allow starting auto if not already running
        if not automator.active_thread or not automator.active_thread.is_alive():
            if keyboard.is_pressed("1"):
                automator.start_script("WAVE")
                time.sleep(0.2) # Debounce
            elif keyboard.is_pressed("2"):
                automator.start_script("GRAB")
                time.sleep(0.2)
            elif keyboard.is_pressed("3"):
                automator.start_script("HOME")
                time.sleep(0.2)
            elif keyboard.is_pressed("4"):
                automator.start_script("TESTALL")
                time.sleep(0.2)
            elif keyboard.is_pressed("5"):
                automator.start_script("TESTALL_AUTO")
                time.sleep(0.2)
            elif keyboard.is_pressed("6"):
                automator.start_script("TESTGRAB")
        
        # -- Manual Override --
        # If any manual key is pressed, ABORT automation immediately
        any_manual_active = False
        for k, (idx, direction) in key_map.items():
            try:
                if keyboard.is_pressed(k):
                    any_manual_active = True
                    # Safety Rule: Immediate manual override
                    if automator.current_status.startswith("Auto"):
                        automator.abort()
                    
                    if not pressed[k]:
                        hand.send_step(idx, direction)
                        pressed[k] = True
                else:
                    if pressed[k]:
                        hand.stop_servo(idx)
                        pressed[k] = False
            except RuntimeError:
                pass
        
        # If we are in automation mode, we don't need to poll manual keys as aggressively
        time.sleep(0.01)

# ---------------- Main Execution ----------------
def main():
    tank = TankController(ser)
    hand = RoboticHand(ser, NUM_SERVOS)
    automator = HandAutomationAPI(hand)

    # Start input thread
    input_thread = threading.Thread(target=input_monitor, args=(hand, automator), daemon=True)
    input_thread.start()

    print("="*60)
    print("   AETHER AEROSPACE | ROVER CONTROL SYSTEM v2.0   ")
    print("="*60)
    print("CONTROLS:")
    print(" [WASD] Tank Drive | [Shift/Ctrl] Boost/Slow")
    print(" [u/y, j/h, etc] Manual Hand Control")
    print(" [1] AUTO: Wave Sequence")
    print(" [2] AUTO: Grab & Lift")
    print(" [3] AUTO: Home/Reset")
    print(" [ESC] Emergency Stop & Exit")
    print("="*60)

    try:
        while True:
            if keyboard.is_pressed("esc"):
                automator.abort() # Ensure thread stops
                tank.stop()
                print("\n[SYSTEM] Shutting down...")
                break

            tank.update()

            # Status Display
            servo_str = " | ".join([f"S{i+1}:{hand.angles[i]:>5.1f}" for i in range(NUM_SERVOS)])
            status_line = (f"\r[{automator.current_status[:10]:<10}] "
                           f"L:{int(tank.current_left):>4} R:{int(tank.current_right):>4} | "
                           f"{servo_str}")
            
            sys.stdout.write(status_line)
            sys.stdout.flush()
            
            time.sleep(0.05)

    except KeyboardInterrupt:
        tank.stop()
        print("\n[SYSTEM] Interrupted.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()