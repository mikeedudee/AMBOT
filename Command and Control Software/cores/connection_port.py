"""
Connection Port Module
Handles serial communication with APC220 USB port and parses microcontroller data.
Designed to be flexible and extensible for future sensor/data additions.
"""

import serial
import serial.tools.list_ports
import threading
import time
import json
import re
from typing import Optional, Callable, Dict, Any


class ConnectionPort:
    """
    Manages serial connection to APC220 USB port and parses incoming data.
    Automatically updates status_store with parsed status values.
    """
    
    # Default sensor and servo name mappings
    # These can be customized based on your microcontroller's data format
    SENSOR_NAME_MAPPING = {
        "LiDAR": ["LiDAR", "LIDAR", "lidar", "L"],
        "MS5611": ["MS5611", "ms5611", "M"],
        "BNO085": ["BNO085", "bno085", "BNO", "bno", "B"],
        "GPS": ["GPS", "gps", "G"],
        "THERMISTOR": ["THERMISTOR", "thermistor", "TEMP", "temp", "T"],
        "CAMERA": ["CAMERA", "camera", "CAM", "cam", "C"]
    }
    
    SERVO_NAME_PATTERN = r"SERVO[_\s]?(\d+)"
    
    def __init__(self, status_store, port: Optional[str] = None, baudrate: int = 9600,
                 timeout: float = 1.0, data_format: str = "auto"):
        """
        Initialize connection port.
        
        Args:
            status_store: Instance of SystemStatusStore to update
            port: Serial port name (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
                  If None, will attempt to auto-detect APC220
            baudrate: Serial communication baud rate (default: 9600)
            timeout: Read timeout in seconds
            data_format: Data format expected ("json", "csv", "auto")
        """
        self.status_store = status_store
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.data_format = data_format
        
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_running = False
        self.read_thread: Optional[threading.Thread] = None
        
        # Buffer for incomplete data packets
        self.data_buffer = ""
        
        # Statistics
        self.packets_received = 0
        self.packets_parsed = 0
        self.parse_errors = 0
        
        # Callbacks for data updates (for future extensibility)
        self.on_data_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
    
    def set_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback function to be called when new data is parsed."""
        self.on_data_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback function to be called on errors."""
        self.on_error_callback = callback
    
    def detect_apc220_port(self) -> Optional[str]:
        """
        Attempt to auto-detect APC220 USB port.
        This is a simple implementation - you may need to customize based on your hardware.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Common APC220 identifiers (customize as needed)
            if any(identifier in port.description.upper() for identifier in 
                   ["APC220", "CH340", "CP210", "FTDI", "USB SERIAL"]):
                return port.device
        # If no specific match, return first available port
        if ports:
            return ports[0].device
        return None
    
    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> bool:
        """
        Connect to serial port.
        
        Args:
            port: Port name (if None, uses self.port_name or auto-detects)
            baudrate: Baud rate (if None, uses self.baudrate)
        
        Returns:
            True if connected successfully, False otherwise
        """
        if port is not None:
            self.port_name = port
        if baudrate is not None:
            self.baudrate = baudrate
        
        # Auto-detect port if not specified
        if self.port_name is None:
            self.port_name = self.detect_apc220_port()
            if self.port_name is None:
                print("ERROR: No serial port found. Please specify port manually.")
                return False
        
        try:
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_connected = True
            print(f"Connected to {self.port_name} at {self.baudrate} baud")
            
            # Start reading thread
            self.start_reading()
            return True
            
        except serial.SerialException as e:
            print(f"ERROR: Failed to connect to {self.port_name}: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        self.is_running = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        self.is_connected = False
        print(f"Disconnected from {self.port_name}")
    
    def start_reading(self):
        """Start background thread to read data from serial port."""
        if self.is_running:
            return
        
        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        print("Started data reading thread")
    
    def stop_reading(self):
        """Stop reading thread."""
        self.is_running = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
    
    def _read_loop(self):
        """Main loop for reading data from serial port (runs in background thread)."""
        while self.is_running and self.is_connected:
            try:
                if self.serial_port and self.serial_port.is_open:
                    # Read available data
                    if self.serial_port.in_waiting > 0:
                        raw_data = self.serial_port.readline()
                        try:
                            # Decode bytes to string
                            data_string = raw_data.decode('utf-8', errors='ignore').strip()
                            if data_string:
                                self.packets_received += 1
                                self._parse_and_update(data_string)
                        except UnicodeDecodeError:
                            # Try alternative encoding
                            try:
                                data_string = raw_data.decode('ascii', errors='ignore').strip()
                                if data_string:
                                    self.packets_received += 1
                                    self._parse_and_update(data_string)
                            except Exception as e:
                                self.parse_errors += 1
                                if self.on_error_callback:
                                    self.on_error_callback(e)
                    else:
                        time.sleep(0.01)  # Small delay when no data available
                else:
                    time.sleep(0.1)
                    
            except serial.SerialException as e:
                self.parse_errors += 1
                print(f"Serial read error: {e}")
                if self.on_error_callback:
                    self.on_error_callback(e)
                self.is_connected = False
                break
            except Exception as e:
                self.parse_errors += 1
                print(f"Unexpected error in read loop: {e}")
                if self.on_error_callback:
                    self.on_error_callback(e)
    
    def _parse_and_update(self, data_string: str):
        """
        Parse data string and update status_store.
        Supports multiple formats: JSON, CSV, and custom formats.
        """
        try:
            # Determine format if auto
            format_type = self.data_format
            if format_type == "auto":
                format_type = self._detect_format(data_string)
            
            # Parse based on format
            if format_type == "json":
                parsed_data = self._parse_json(data_string)
            elif format_type == "csv":
                parsed_data = self._parse_csv(data_string)
            else:
                parsed_data = self._parse_custom(data_string)
            
            if parsed_data:
                self._update_status_store(parsed_data)
                self.packets_parsed += 1
                
                # Call custom callback if set
                if self.on_data_callback:
                    self.on_data_callback(parsed_data)
                    
        except Exception as e:
            self.parse_errors += 1
            print(f"Parse error: {e}, Data: {data_string[:100]}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def _detect_format(self, data_string: str) -> str:
        """Auto-detect data format."""
        data_string = data_string.strip()
        if data_string.startswith('{') or data_string.startswith('['):
            return "json"
        elif ',' in data_string or '|' in data_string:
            return "csv"
        else:
            return "custom"
    
    def _parse_json(self, data_string: str) -> Dict[str, Any]:
        """Parse JSON format data."""
        try:
            return json.loads(data_string)
        except json.JSONDecodeError:
            # Try to extract JSON from potentially malformed data
            json_match = re.search(r'\{[^}]*\}', data_string)
            if json_match:
                return json.loads(json_match.group())
            raise
    
    def _parse_csv(self, data_string: str) -> Dict[str, Any]:
        """
        Parse CSV format data.
        Expected format examples:
        - "LiDAR,1,MS5611,1,BNO085,1,..." (key-value pairs)
        - "STATUS,LiDAR,1,MS5611,0,..." (header followed by values)
        - "LiDAR=1,MS5611=0,..." (key=value pairs)
        """
        parsed = {}
        
        # Try key=value format first
        if '=' in data_string:
            pairs = re.split(r'[,;|\s]+', data_string)
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed[key.strip()] = self._convert_value(value.strip())
            return parsed
        
        # Try comma-separated key-value pairs
        parts = re.split(r'[,;|\s]+', data_string.strip())
        
        # If even number of parts, assume key-value pairs
        if len(parts) % 2 == 0:
            for i in range(0, len(parts), 2):
                key = parts[i].strip()
                value = self._convert_value(parts[i+1].strip())
                parsed[key] = value
        else:
            # Single values - assume it's status bits in order
            sensor_names = list(self.SENSOR_NAME_MAPPING.keys())
            for i, value in enumerate(parts):
                if i < len(sensor_names):
                    parsed[sensor_names[i]] = self._convert_value(value.strip())
        
        return parsed
    
    def _parse_custom(self, data_string: str) -> Dict[str, Any]:
        """
        Parse custom format data.
        You can extend this method to support your specific microcontroller format.
        """
        parsed = {}
        
        # Example: Try to extract key-value patterns
        # Pattern: "SENSOR_NAME:VALUE" or "SENSOR_NAME VALUE"
        patterns = [
            (r'(\w+)[:=]\s*(\d+)', 1, 2),  # KEY:VALUE or KEY=VALUE
            (r'(\w+)\s+(\d+)', 1, 2),      # KEY VALUE
        ]
        
        for pattern, key_group, value_group in patterns:
            matches = re.finditer(pattern, data_string)
            for match in matches:
                key = match.group(key_group)
                value = self._convert_value(match.group(value_group))
                parsed[key] = value
        
        # If no matches, try to match against known sensor names
        if not parsed:
            for sensor_name, aliases in self.SENSOR_NAME_MAPPING.items():
                for alias in aliases:
                    pattern = rf'{re.escape(alias)}[:\s=]+(\d+)'
                    match = re.search(pattern, data_string, re.IGNORECASE)
                    if match:
                        parsed[sensor_name] = self._convert_value(match.group(1))
        
        return parsed
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        value = value.strip()
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try boolean
        if value.upper() in ['TRUE', '1', 'ON', 'YES']:
            return 1
        elif value.upper() in ['FALSE', '0', 'OFF', 'NO']:
            return 0
        
        # Return as string
        return value
    
    def _update_status_store(self, parsed_data: Dict[str, Any]):
        """
        Update status_store with parsed data.
        Maps parsed keys to sensor/servo names and updates accordingly.
        """
        sensor_updates = {}
        servo_updates = {}
        additional_data = {}
        
        for key, value in parsed_data.items():
            key_upper = key.upper()
            
            # Check if it's a servo
            servo_match = re.match(self.SERVO_NAME_PATTERN, key_upper)
            if servo_match:
                servo_num = servo_match.group(1)
                servo_name = f"SERVO_{servo_num}"
                servo_updates[servo_name] = value
                continue
            
            # Check if it matches a sensor name
            sensor_matched = False
            for sensor_name, aliases in self.SENSOR_NAME_MAPPING.items():
                if key == sensor_name or key_upper in [a.upper() for a in aliases]:
                    sensor_updates[sensor_name] = value
                    sensor_matched = True
                    break
            
            # If not matched, store as additional data (for future extensibility)
            if not sensor_matched:
                additional_data[key] = value
        
        # Update status store
        if sensor_updates:
            self.status_store.update_all_sensors(sensor_updates)
        
        if servo_updates:
            self.status_store.update_all_servos(servo_updates)
        
        # Store additional data (for future use)
        if additional_data:
            # Store in a generic "raw_data" key or expand as needed
            for key, value in additional_data.items():
                # Try to associate with closest sensor/servo or store globally
                # This is flexible for future additions
                pass
    
    def send_command(self, command: str) -> bool:
        """
        Send command to microcontroller via serial port.
        
        Args:
            command: Command string to send
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
            return False
        
        try:
            self.serial_port.write((command + '\n').encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """Get communication statistics."""
        return {
            "packets_received": self.packets_received,
            "packets_parsed": self.packets_parsed,
            "parse_errors": self.parse_errors,
            "is_connected": 1 if self.is_connected else 0,
            "is_running": 1 if self.is_running else 0
        }


# ---------------- Tank Controller ----------------

class TankController:
    """
    Tank controller for rover movement control.
    Supports WASD keyboard input with smooth acceleration and tank-style turning.
    Generates commands that can be sent via serial connection.
    """
    
    def __init__(self, max_pwm: int = 255, exp_factor: float = 1.8, 
                 smooth_step: float = 0.08, turn_base: float = 0.7,
                 boost_factor: float = 1.5, slow_factor: float = 0.5):
        """
        Initialize tank controller.
        
        Args:
            max_pwm: Maximum PWM value (0-255)
            exp_factor: Exponential factor for speed curve
            smooth_step: Smoothing step size (0.0-1.0)
            turn_base: Base turn factor
            boost_factor: Speed multiplier when boost is active
            slow_factor: Speed multiplier when slow mode is active
        """
        self.max_pwm = max_pwm
        self.exp_factor = exp_factor
        self.smooth_step = smooth_step
        self.turn_base = turn_base
        self.boost_factor = boost_factor
        self.slow_factor = slow_factor
        
        self.current_left = 0.0
        self.current_right = 0.0
        self.manual_left = 0.0
        self.manual_right = 0.0
        self.mode = "Neutral"
        self.key_states = {"W": False, "S": False, "A": False, "D": False}
    
    def apply_exponential(self, v: float) -> int:
        """
        Apply exponential curve to speed value for smoother control.
        
        Args:
            v: Normalized speed value (-1.0 to 1.0)
        
        Returns:
            PWM value (-max_pwm to max_pwm)
        """
        sign = 1 if v >= 0 else -1
        pwm = sign * int((abs(v) ** self.exp_factor) * self.max_pwm)
        return max(-self.max_pwm, min(self.max_pwm, pwm))
    
    def compute_targets(self, key_states: Dict[str, bool]) -> tuple:
        """
        Compute target left and right motor speeds from keyboard states.
        
        Args:
            key_states: Dictionary with "W", "S", "A", "D", "shift", "ctrl" keys
        
        Returns:
            Tuple of (left_target, right_target) as PWM values
        """
        fwd, turn = 0.0, 0.0
        factor = 1.0
        
        # Keyboard detection
        self.key_states = {
            "W": key_states.get("W", False),
            "S": key_states.get("S", False),
            "A": key_states.get("A", False),
            "D": key_states.get("D", False)
        }
        
        if key_states.get("W", False):
            fwd += 1
        if key_states.get("S", False):
            fwd -= 1
        if key_states.get("A", False):
            turn -= 1
        if key_states.get("D", False):
            turn += 1
        
        if key_states.get("shift", False):
            factor = self.boost_factor
            self.mode = "BOOST"
        elif key_states.get("ctrl", False):
            factor = self.slow_factor
            self.mode = "SLOW"
        else:
            self.mode = "Neutral"
        
        # Tank-style turning (adaptive based on forward speed)
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
        
        # Manual override
        if abs(self.manual_left) > 1e-6 or abs(self.manual_right) > 1e-6:
            left = max(-1, min(1, self.manual_left))
            right = max(-1, min(1, self.manual_right))
        
        tl = self.apply_exponential(left)
        tr = self.apply_exponential(right)
        
        return tl, tr
    
    def smooth(self, cur: float, tgt: float) -> float:
        """
        Smooth interpolation between current and target values.
        
        Args:
            cur: Current value
            tgt: Target value
        
        Returns:
            Smoothed value
        """
        diff = tgt - cur
        if abs(diff) < 1:
            return float(tgt)
        return cur + diff * self.smooth_step
    
    def update(self, key_states: Dict[str, bool]) -> tuple:
        """
        Update controller state and return current PWM values.
        
        Args:
            key_states: Dictionary with key states
        
        Returns:
            Tuple of (left_pwm, right_pwm) as integers
        """
        tl, tr = self.compute_targets(key_states)
        self.current_left = self.smooth(self.current_left, tl)
        self.current_right = self.smooth(self.current_right, tr)
        return int(self.current_left), int(self.current_right)
    
    def stop(self) -> tuple:
        """
        Stop the tank (set both motors to zero).
        
        Returns:
            Tuple of (0, 0)
        """
        self.current_left = 0.0
        self.current_right = 0.0
        self.manual_left = 0.0
        self.manual_right = 0.0
        return (0, 0)
    
    def set_manual_override(self, left: float, right: float):
        """
        Set manual override values for left and right motors.
        
        Args:
            left: Left motor value (-1.0 to 1.0)
            right: Right motor value (-1.0 to 1.0)
        """
        self.manual_left = max(-1.0, min(1.0, left))
        self.manual_right = max(-1.0, min(1.0, right))
    
    def clear_manual_override(self):
        """Clear manual override values."""
        self.manual_left = 0.0
        self.manual_right = 0.0


# ---------------- Robotic Hand Controller ----------------

class RoboticHand:
    """
    Robotic hand/arm controller for servo control.
    Manages multiple servos with individual angle control.
    """
    
    def __init__(self, num_servos: int = 6, default_sensitivity: float = 1.0):
        """
        Initialize robotic hand controller.
        
        Args:
            num_servos: Number of servos
            default_sensitivity: Default sensitivity (angle change per step)
        """
        self.num_servos = num_servos
        self.angles = [90.0] * num_servos
        self.sensitivity = [default_sensitivity] * num_servos
        self.lock = threading.Lock()
    
    def send_step(self, idx: int, direction: str) -> str:
        """
        Generate servo step command.
        
        Args:
            idx: Servo index (0-based)
            direction: Direction ("L" for left/decrease, "R" for right/increase, "N" for neutral)
        
        Returns:
            Command string to send to rover
        """
        with self.lock:
            if direction == "L":
                self.angles[idx] = max(0.0, self.angles[idx] - self.sensitivity[idx])
            elif direction == "R":
                self.angles[idx] = min(180.0, self.angles[idx] + self.sensitivity[idx])
            # "N" means neutral/stop - don't change angle
            
            cmd = f"S{idx+1}{direction}"
            return cmd
    
    def stop_servo(self, idx: int) -> str:
        """
        Stop servo (send neutral command).
        
        Args:
            idx: Servo index (0-based)
        
        Returns:
            Command string
        """
        return self.send_step(idx, "N")
    
    def set_angle(self, idx: int, angle: float) -> str:
        """
        Set servo to specific angle.
        
        Args:
            idx: Servo index (0-based)
            angle: Target angle (0-180)
        
        Returns:
            Command string
        """
        with self.lock:
            self.angles[idx] = max(0.0, min(180.0, angle))
            return f"S{idx+1}A{int(self.angles[idx])}"


# ---------------- Global Command Generator ----------------

class GlobalCommandGenerator:
    """
    Global command generator that creates standardized command strings
    for the rover. Can be used by any control mode (keyboard, remote, autonomous, etc.).
    """
    
    @staticmethod
    def generate_motor_command(left_pwm: int, right_pwm: int) -> str:
        """
        Generate motor command string.
        Format: "M{left_pwm},{right_pwm}"
        
        Args:
            left_pwm: Left motor PWM value (-255 to 255)
            right_pwm: Right motor PWM value (-255 to 255)
        
        Returns:
            Command string
        """
        return f"M{left_pwm},{right_pwm}"
    
    @staticmethod
    def generate_servo_command(servo_idx: int, angle: int) -> str:
        """
        Generate servo command string.
        Format: "S{servo_num}A{angle}"
        
        Args:
            servo_idx: Servo index (0-based)
            angle: Target angle (0-180)
        
        Returns:
            Command string
        """
        return f"S{servo_idx+1}A{angle}"
    
    @staticmethod
    def generate_servo_step_command(servo_idx: int, direction: str) -> str:
        """
        Generate servo step command string.
        Format: "S{servo_num}{direction}" where direction is L, R, or N
        
        Args:
            servo_idx: Servo index (0-based)
            direction: Direction ("L", "R", or "N")
        
        Returns:
            Command string
        """
        return f"S{servo_idx+1}{direction}"
    
    @staticmethod
    def generate_stop_command() -> str:
        """
        Generate stop command (stop all motors).
        Format: "STOP"
        
        Returns:
            Command string
        """
        return "STOP"
    
    @staticmethod
    def generate_combined_command(left_pwm: int, right_pwm: int, 
                                   servo_commands: Optional[list] = None) -> str:
        """
        Generate combined command with motors and servos.
        Format: "M{left},{right}|S1A{angle1}|S2A{angle2}|..."
        
        Args:
            left_pwm: Left motor PWM value
            right_pwm: Right motor PWM value
            servo_commands: Optional list of servo command strings
        
        Returns:
            Combined command string
        """
        cmd = GlobalCommandGenerator.generate_motor_command(left_pwm, right_pwm)
        
        if servo_commands:
            cmd += "|" + "|".join(servo_commands)
        
        return cmd
    
    @staticmethod
    def parse_command(command: str) -> Dict[str, Any]:
        """
        Parse command string back into components (for testing/debugging).
        
        Args:
            command: Command string
        
        Returns:
            Dictionary with parsed components
        """
        parsed = {}
        
        parts = command.split("|")
        for part in parts:
            part = part.strip()
            if part.startswith("M"):
                # Motor command: M{left},{right}
                try:
                    values = part[1:].split(",")
                    parsed["left_pwm"] = int(values[0])
                    parsed["right_pwm"] = int(values[1])
                except (ValueError, IndexError):
                    pass
            elif part.startswith("S"):
                # Servo command: S{num}{action}
                try:
                    servo_num = int(part[1])
                    action = part[2:]
                    parsed[f"servo_{servo_num}"] = action
                except (ValueError, IndexError):
                    pass
            elif part == "STOP":
                parsed["stop"] = True
        
        return parsed
