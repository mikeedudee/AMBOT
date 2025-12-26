"""
Keyboard Control Module
Handles keyboard input (WASD) for manual rover control.
Integrates with connection_port.py TankController and GlobalCommandGenerator.
"""

import threading
import time
from typing import Optional

try:
    import keyboard  # make sure 'keyboard' module is installed
    KEYBOARD_AVAILABLE = True
except ImportError:
    print("WARNING: 'keyboard' module not installed. Install with: pip install keyboard")
    KEYBOARD_AVAILABLE = False

from cores.connection_port import TankController, RoboticHand, GlobalCommandGenerator


class KeyboardControlManager:
    """
    Manages keyboard control for the rover.
    Integrates TankController and RoboticHand with keyboard input.
    """
    
    def __init__(self, connection_port=None, num_servos=6):
        """
        Initialize keyboard control manager.
        
        Args:
            connection_port: ConnectionPort instance for sending commands (optional)
            num_servos: Number of servos to control
        """
        self.connection_port = connection_port
        self.tank_controller = TankController()
        self.robotic_hand = RoboticHand(num_servos=num_servos)
        self.command_generator = GlobalCommandGenerator()
        
        self.is_running = False
        self.control_thread: Optional[threading.Thread] = None
        
        # Servo keyboard mapping (same as user's example)
        self.servo_key_map = {
            'y': (0, 'L'), 'u': (0, 'R'),
            'h': (1, 'L'), 'j': (1, 'R'),
            'n': (2, 'L'), 'm': (2, 'R'),
            'i': (3, 'L'), 'o': (3, 'R'),
            'k': (4, 'L'), 'l': (4, 'R'),
            'a': (5, 'L'), 's': (5, 'R')
        }
        
        # Track pressed keys to avoid repeat triggers
        self.servo_pressed = {k: False for k in self.servo_key_map.keys()}
    
    def set_connection_port(self, connection_port):
        """Set or update the connection port instance."""
        self.connection_port = connection_port
    
    def start(self):
        """Start keyboard control thread."""
        if not KEYBOARD_AVAILABLE:
            print("ERROR: Keyboard module not available. Cannot start keyboard control.")
            return False
        
        if self.is_running:
            return True
        
        self.is_running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("Keyboard control thread started.")
        return True
    
    def stop(self):
        """Stop keyboard control thread."""
        self.is_running = False
        
        # Stop tank
        self.tank_controller.stop()
        
        if self.control_thread:
            self.control_thread.join(timeout=2.0)
        
        print("Keyboard control stopped.")
    
    def _control_loop(self):
        """
        Main control loop that reads keyboard input and sends commands.
        Only active when enabled via external flags.
        """
        while self.is_running:
            time.sleep(0.05)  # Prevent 100% CPU usage
            
            # Check if we should process keyboard input
            # This will be checked by the caller via conditions
            
            # Read keyboard states for tank control
            key_states = {
                "W": keyboard.is_pressed("w") if KEYBOARD_AVAILABLE else False,
                "S": keyboard.is_pressed("s") if KEYBOARD_AVAILABLE else False,
                "A": keyboard.is_pressed("a") if KEYBOARD_AVAILABLE else False,
                "D": keyboard.is_pressed("d") if KEYBOARD_AVAILABLE else False,
                "shift": keyboard.is_pressed("shift") if KEYBOARD_AVAILABLE else False,
                "ctrl": keyboard.is_pressed("ctrl") if KEYBOARD_AVAILABLE else False,
            }
            
            # Update tank controller
            left_pwm, right_pwm = self.tank_controller.update(key_states)
            
            # Handle servo control
            servo_commands = []
            for k, (idx, direction) in self.servo_key_map.items():
                try:
                    if KEYBOARD_AVAILABLE and keyboard.is_pressed(k):
                        if not self.servo_pressed[k]:
                            cmd = self.robotic_hand.send_step(idx, direction)
                            servo_commands.append(cmd)
                            self.servo_pressed[k] = True
                    else:
                        if self.servo_pressed[k]:
                            self.robotic_hand.stop_servo(idx)
                            self.servo_pressed[k] = False
                except RuntimeError:
                    pass
            
            # Generate and send command
            if self.connection_port and self.connection_port.is_connected:
                motor_cmd = self.command_generator.generate_motor_command(left_pwm, right_pwm)
                
                if servo_commands:
                    combined_cmd = self.command_generator.generate_combined_command(
                        left_pwm, right_pwm, servo_commands
                    )
                    self.connection_port.send_command(combined_cmd)
                else:
                    self.connection_port.send_command(motor_cmd)
            
            # Check for exit
            if KEYBOARD_AVAILABLE and keyboard.is_pressed("esc"):
                self.tank_controller.stop()
                break


def start_keyboard_control_thread(toolbar):
    """
    Start a separate thread to handle manual keyboard control.
    This function maintains backward compatibility with existing code.

    Parameters:
        toolbar: instance of BottomToolbar containing serial connection,
                 manual_mode_active flag, selected_manual_idx, and serial_port/connection_port
    """
    # Check if toolbar has connection_port, otherwise use serial_port
    connection_port = getattr(toolbar, 'connection_port', None)
    
    # If no connection_port, create a simple wrapper or use serial_port directly
    if connection_port is None and hasattr(toolbar, 'serial_port'):
        # For backward compatibility, we'll use a simple approach
        # The actual sending will be handled in the loop
        pass
    
    # Initialize keyboard control manager
    if not hasattr(toolbar, '_keyboard_manager'):
        num_servos = 6  # Default
        toolbar._keyboard_manager = KeyboardControlManager(
            connection_port=connection_port,
            num_servos=num_servos
        )
    
    # Create wrapper thread that checks toolbar conditions
    if toolbar._keyboard_thread is None or not toolbar._keyboard_thread.is_alive():
        toolbar._keyboard_thread = threading.Thread(
            target=_keyboard_control_loop_wrapper, args=(toolbar,), daemon=True
        )
        toolbar._keyboard_thread.start()
        print("Keyboard control thread started.")


def _keyboard_control_loop_wrapper(toolbar):
    """
    Wrapper loop that checks toolbar conditions before enabling keyboard control.
    Maintains compatibility with existing toolbar structure.
    """
    while True:
        time.sleep(0.05)
        
        # Check if manual mode is active and keyboard control is selected
        if not getattr(toolbar, 'manual_mode_active', False) or \
           getattr(toolbar, 'selected_manual_idx', None) != 0:
            continue
        
        # Check connection
        connection_port = getattr(toolbar, 'connection_port', None)
        serial_port = getattr(toolbar, 'serial_port', None)
        
        if connection_port is None and (serial_port is None or not serial_port.is_open):
            continue
        
        # Initialize keyboard manager if needed
        if not hasattr(toolbar, '_keyboard_manager'):
            toolbar._keyboard_manager = KeyboardControlManager(
                connection_port=connection_port,
                num_servos=6
            )
            toolbar._keyboard_manager.start()
        elif not toolbar._keyboard_manager.is_running:
            toolbar._keyboard_manager.set_connection_port(connection_port)
            toolbar._keyboard_manager.start()
        
        # Run one iteration of keyboard control
        if KEYBOARD_AVAILABLE:
            try:
                # Read keyboard states
                key_states = {
                    "W": keyboard.is_pressed("w"),
                    "S": keyboard.is_pressed("s"),
                    "A": keyboard.is_pressed("a"),
                    "D": keyboard.is_pressed("d"),
                    "shift": keyboard.is_pressed("shift"),
                    "ctrl": keyboard.is_pressed("ctrl"),
                }
                
                # Update tank controller
                left_pwm, right_pwm = toolbar._keyboard_manager.tank_controller.update(key_states)
                
                # Handle servo control
                servo_commands = []
                for k, (idx, direction) in toolbar._keyboard_manager.servo_key_map.items():
                    try:
                        if keyboard.is_pressed(k):
                            if not toolbar._keyboard_manager.servo_pressed[k]:
                                cmd = toolbar._keyboard_manager.robotic_hand.send_step(idx, direction)
                                servo_commands.append(cmd)
                                toolbar._keyboard_manager.servo_pressed[k] = True
                        else:
                            if toolbar._keyboard_manager.servo_pressed[k]:
                                toolbar._keyboard_manager.robotic_hand.stop_servo(idx)
                                toolbar._keyboard_manager.servo_pressed[k] = False
                    except RuntimeError:
                        pass
                
                # Send command via connection_port or serial_port
                if connection_port and connection_port.is_connected:
                    motor_cmd = toolbar._keyboard_manager.command_generator.generate_motor_command(
                        left_pwm, right_pwm
                    )
                    
                    if servo_commands:
                        combined_cmd = toolbar._keyboard_manager.command_generator.generate_combined_command(
                            left_pwm, right_pwm, servo_commands
                        )
                        connection_port.send_command(combined_cmd)
                    else:
                        connection_port.send_command(motor_cmd)
                elif serial_port and serial_port.is_open:
                    # Fallback to direct serial for backward compatibility
                    cmd_string = f"{left_pwm},{right_pwm}\n"
                    try:
                        serial_port.write(cmd_string.encode())
                    except Exception as e:
                        print(f"Serial write error: {e}")
                
                # Check for exit
                if keyboard.is_pressed("esc"):
                    toolbar._keyboard_manager.tank_controller.stop()
                    break
                    
            except Exception as e:
                print(f"Keyboard control error: {e}")


def _calculate_tank_command(fwd, bwd, left, right, boost, slow):
    """
    Legacy function for backward compatibility.
    Returns a single value for tank movement based on keys pressed.
    Note: This is now handled by TankController, but kept for compatibility.
    """
    speed = 100  # base speed
    if boost:
        speed *= 2
    if slow:
        speed //= 2

    cmd = 0
    if fwd:
        cmd += speed
    if bwd:
        cmd -= speed
    if left:
        cmd -= 20  # example turn adjustment
    if right:
        cmd += 20

    return cmd
