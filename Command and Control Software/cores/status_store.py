"""
Status Store Module
Handles status values for sensors and servos from both serial (APC220) and WiFi sources.
Supports flexible telemetry data with individual status indicators.
"""

import threading
import socket
import json
import time
from typing import Optional, Dict, Any, Callable

# Default status values for individual sensors
status_LiDAR        = 1
status_MS5611       = 1
status_BNO085       = 0
status_GPS          = 0
status_THERMISTOR   = 0
status_CAMERA       = 0
status_SERVO_1      = 0
status_SERVO_2      = 0
status_SERVO_3      = 0
status_SERVO_4      = 0
status_SERVO_5      = 0
status_SERVO_6      = 0
status_SERVO_7      = 0
status              = 0 

class SystemStatusStore:
    """
    Stores and manages status values for all sensors and servos.
    Supports data from both serial (APC220) and WiFi sources.
    Each sensor/servo has its own status value (0=red, 1=green, etc.).
    """
    
    # Sensor name mapping (for easy lookup)
    SENSOR_NAMES = ["LiDAR", "MS5611", "BNO085", "GPS", "THERMISTOR", "CAMERA"]
    
    def __init__(self, n_sensors=6, n_servos=7):
        """
        Initialize status store.
        
        Args:
            n_sensors: Number of sensors
            n_servos: Number of servos
        """
        self.n_sensors = n_sensors
        self.n_servos = n_servos
        
        # Initialize sensor states (individual values for each sensor)
        # 0 = red (off/error), 1 = green (on/ok), other values = custom states
        self.sensor_states = [0] * n_sensors
        self.servo_states = [0] * n_servos
        
        # Store sensor values in dictionary for flexible access
        self.sensor_values = {
            "LiDAR": 0,
            "MS5611": 0,
            "BNO085": 0,
            "GPS": 0,
            "THERMISTOR": 0,
            "CAMERA": 0
        }
        
        # Store servo values
        self.servo_values = {f"SERVO_{i+1}": 0 for i in range(n_servos)}
        
        # Store additional telemetry data (for future extensibility)
        self.telemetry_data = {}
        
        # Thread safety (use RLock for reentrant locking)
        self.lock = threading.RLock()
        
        # Callbacks for status updates
        self.on_status_update: Optional[Callable] = None
    
    def set_status_update_callback(self, callback: Callable[[], None]):
        """Set callback function to be called when status is updated."""
        self.on_status_update = callback
    
    def update_sensor(self, sensor_name: str, value: Any):
        """
        Update individual sensor status.
        
        Args:
            sensor_name: Name of sensor (e.g., "LiDAR", "MS5611")
            value: Status value (0=red, 1=green, etc.)
        """
        with self.lock:
            if sensor_name in self.sensor_values:
                self.sensor_values[sensor_name] = value
                
                # Update corresponding index in sensor_states list
                try:
                    idx = self.SENSOR_NAMES.index(sensor_name)
                    if idx < len(self.sensor_states):
                        # Convert value to 1 (green) or 0 (red)
                        # Handle various value types: int, float, bool, str
                        if isinstance(value, (int, float)):
                            self.sensor_states[idx] = 1 if value != 0 else 0
                        else:
                            self.sensor_states[idx] = 1 if bool(value) else 0
                except ValueError:
                    pass
                
                if self.on_status_update:
                    self.on_status_update()
    
    def update_servo(self, servo_name: str, value: Any):
        """
        Update individual servo status.
        
        Args:
            servo_name: Name of servo (e.g., "SERVO_1")
            value: Status value (0=red, 1=green, etc.)
        """
        with self.lock:
            if servo_name in self.servo_values:
                self.servo_values[servo_name] = value
                
                # Update corresponding index in servo_states list
                try:
                    servo_num = int(servo_name.split("_")[1]) - 1
                    if 0 <= servo_num < len(self.servo_states):
                        # Convert value to 1 (green) or 0 (red)
                        # Handle various value types: int, float, bool, str
                        if isinstance(value, (int, float)):
                            self.servo_states[servo_num] = 1 if value != 0 else 0
                        else:
                            self.servo_states[servo_num] = 1 if bool(value) else 0
                except (ValueError, IndexError):
                    pass
                
                if self.on_status_update:
                    self.on_status_update()
    
    def update_all_sensors(self, sensor_updates: Dict[str, Any]):
        """Update multiple sensors at once."""
        with self.lock:
            should_callback = False
            for sensor_name, value in sensor_updates.items():
                if sensor_name in self.sensor_values:
                    old_value = self.sensor_values[sensor_name]
                    self.sensor_values[sensor_name] = value
                    
                    # Update corresponding index in sensor_states list
                    try:
                        idx = self.SENSOR_NAMES.index(sensor_name)
                        if idx < len(self.sensor_states):
                            # Convert value to 1 or 0 (green or red)
                            # Handle various value types: int, float, bool, str
                            if isinstance(value, (int, float)):
                                new_state = 1 if value != 0 else 0
                            else:
                                new_state = 1 if bool(value) else 0
                            self.sensor_states[idx] = new_state
                            should_callback = True
                    except ValueError:
                        pass
            
            # Trigger callback once after all updates
            if should_callback and self.on_status_update:
                self.on_status_update()
    
    def update_all_servos(self, servo_updates: Dict[str, Any]):
        """Update multiple servos at once."""
        with self.lock:
            should_callback = False
            for servo_name, value in servo_updates.items():
                if servo_name in self.servo_values:
                    self.servo_values[servo_name] = value
                    
                    # Update corresponding index in servo_states list
                    try:
                        servo_num = int(servo_name.split("_")[1]) - 1
                        if 0 <= servo_num < len(self.servo_states):
                            # Convert value to 1 or 0 (green or red)
                            # Handle various value types: int, float, bool, str
                            if isinstance(value, (int, float)):
                                new_state = 1 if value != 0 else 0
                            else:
                                new_state = 1 if bool(value) else 0
                            self.servo_states[servo_num] = new_state
                            should_callback = True
                    except (ValueError, IndexError):
                        pass
            
            # Trigger callback once after all updates
            if should_callback and self.on_status_update:
                self.on_status_update()
    
    def update_telemetry(self, telemetry_dict: Dict[str, Any]):
        """Update telemetry data (for future extensibility)."""
        with self.lock:
            self.telemetry_data.update(telemetry_dict)
            if self.on_status_update:
                self.on_status_update()
    
    def get_sensor_status(self, sensor_name: str) -> int:
        """Get current status value for a sensor."""
        with self.lock:
            return self.sensor_values.get(sensor_name, 0)
    
    def get_servo_status(self, servo_name: str) -> int:
        """Get current status value for a servo."""
        with self.lock:
            return self.servo_values.get(servo_name, 0)
    
    def get_all_status(self) -> tuple:
        """Get all sensor and servo states as lists."""
        with self.lock:
            return (self.sensor_states.copy(), self.servo_states.copy())


class WiFiStatusReceiver:
    """
    Receives status data from WiFi connection.
    Connects to a WiFi server and updates status_store with received data.
    """
    
    def __init__(self, status_store: SystemStatusStore, host: str = "192.168.4.1", 
                 port: int = 8888, timeout: float = 1.0):
        """
        Initialize WiFi status receiver.
        
        Args:
            status_store: Instance of SystemStatusStore to update
            host: WiFi server hostname/IP address
            port: WiFi server port
            timeout: Connection timeout in seconds
        """
        self.status_store = status_store
        self.host = host
        self.port = port
        self.timeout = timeout
        
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_running = False
        self.receive_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.packets_received = 0
        self.parse_errors = 0
        
        # Callbacks
        self.on_error_callback: Optional[Callable] = None
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback function to be called on errors."""
        self.on_error_callback = callback
    
    def connect(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        """
        Connect to WiFi server.
        
        Args:
            host: Hostname/IP (if None, uses self.host)
            port: Port (if None, uses self.port)
        
        Returns:
            True if connected successfully, False otherwise
        """
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            print(f"Connected to WiFi server at {self.host}:{self.port}")
            
            # Start receiving thread
            self.start_receiving()
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to connect to WiFi server {self.host}:{self.port}: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from WiFi server."""
        self.is_running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
        
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        self.is_connected = False
        print(f"Disconnected from WiFi server")
    
    def start_receiving(self):
        """Start background thread to receive data from WiFi."""
        if self.is_running:
            return
        
        self.is_running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        print("Started WiFi data receiving thread")
    
    def stop_receiving(self):
        """Stop receiving thread."""
        self.is_running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
    
    def _receive_loop(self):
        """Main loop for receiving data from WiFi (runs in background thread)."""
        buffer = b""
        
        while self.is_running and self.is_connected:
            try:
                if self.socket:
                    # Receive data
                    try:
                        data = self.socket.recv(4096)
                        if not data:
                            break
                        
                        buffer += data
                        
                        # Process complete messages (assuming JSON format)
                        while b'\n' in buffer or b'}' in buffer:
                            try:
                                # Try to find JSON object
                                if b'}' in buffer:
                                    json_end = buffer.find(b'}') + 1
                                    json_str = buffer[:json_end].decode('utf-8', errors='ignore')
                                    buffer = buffer[json_end:]
                                    
                                    # Try to parse and update status
                                    self._parse_and_update(json_str)
                                    self.packets_received += 1
                                    
                                elif b'\n' in buffer:
                                    line = buffer[:buffer.find(b'\n')].decode('utf-8', errors='ignore')
                                    buffer = buffer[buffer.find(b'\n')+1:]
                                    
                                    if line.strip():
                                        self._parse_and_update(line)
                                        self.packets_received += 1
                            except Exception as e:
                                self.parse_errors += 1
                                if self.on_error_callback:
                                    self.on_error_callback(e)
                                
                    except socket.timeout:
                        continue
                    except socket.error as e:
                        print(f"Socket error: {e}")
                        self.is_connected = False
                        break
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.parse_errors += 1
                print(f"Unexpected error in WiFi receive loop: {e}")
                if self.on_error_callback:
                    self.on_error_callback(e)
                self.is_connected = False
                break
    
    def _parse_and_update(self, data_string: str):
        """
        Parse data string and update status_store.
        Supports JSON format and key-value pairs.
        """
        try:
            data_string = data_string.strip()
            
            # Try JSON format first
            if data_string.startswith('{') or data_string.startswith('['):
                try:
                    parsed_data = json.loads(data_string)
                    if isinstance(parsed_data, dict):
                        self._update_from_dict(parsed_data)
                    return
                except json.JSONDecodeError:
                    pass
            
            # Try key-value pairs (CSV format)
            # Format: "LiDAR=1,MS5611=0,BNO085=1" or "LiDAR:1,MS5611:0"
            if '=' in data_string or ':' in data_string:
                parsed_data = {}
                pairs = data_string.replace(':', '=').split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert value
                        try:
                            value = int(value)
                        except ValueError:
                            try:
                                value = float(value)
                            except ValueError:
                                value = 1 if value.upper() in ['TRUE', 'ON', 'YES'] else 0
                        
                        parsed_data[key] = value
                
                self._update_from_dict(parsed_data)
                
        except Exception as e:
            self.parse_errors += 1
            print(f"Parse error: {e}, Data: {data_string[:100]}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def _update_from_dict(self, data_dict: Dict[str, Any]):
        """Update status_store from dictionary of values."""
        sensor_updates = {}
        servo_updates = {}
        telemetry_updates = {}
        
        for key, value in data_dict.items():
            key_upper = key.upper()
            
            # Check if it's a servo
            if key_upper.startswith("SERVO"):
                servo_updates[key] = value
            # Check if it's a known sensor
            elif key in self.status_store.SENSOR_NAMES or key_upper in [s.upper() for s in self.status_store.SENSOR_NAMES]:
                sensor_name = key if key in self.status_store.SENSOR_NAMES else next(
                    s for s in self.status_store.SENSOR_NAMES if s.upper() == key_upper
                )
                sensor_updates[sensor_name] = value
            else:
                # Store as telemetry data
                telemetry_updates[key] = value
        
        # Update status store
        if sensor_updates:
            self.status_store.update_all_sensors(sensor_updates)
        if servo_updates:
            self.status_store.update_all_servos(servo_updates)
        if telemetry_updates:
            self.status_store.update_telemetry(telemetry_updates)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get communication statistics."""
        return {
            "packets_received": self.packets_received,
            "parse_errors": self.parse_errors,
            "is_connected": 1 if self.is_connected else 0,
            "is_running": 1 if self.is_running else 0
        }


# Create a single instance for global use
status_store = SystemStatusStore()
