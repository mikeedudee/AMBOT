class SystemStatusStore:
    def __init__(self, n_sensors=6, n_servos=7):
        self.sensor_states = [0] * n_sensors
        self.servo_states = [0] * n_servos

# Create a single instance for global use
status_store = SystemStatusStore()
