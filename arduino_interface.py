import serial
import json
import time
import threading
from datetime import datetime
from models import db, Machine, MachineSession, SensorReading
import math

class ArduinoInterface:
    """Interface for communicating with Arduino IMU sensor"""
    
    def __init__(self, port, baud_rate, vibration_threshold, idle_timeout):
        self.port = port
        self.baud_rate = baud_rate
        self.vibration_threshold = vibration_threshold
        self.idle_timeout = idle_timeout
        self.serial_connection = None
        self.running = False
        self.thread = None
        
    def connect(self):
        """Establish connection with Arduino"""
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self):
        """Close connection with Arduino"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Disconnected from Arduino")
    
    def read_sensor_data(self):
        """Read sensor data from Arduino"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        try:
            if self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()
                # Expected format: machine_id,ax,ay,az
                parts = line.split(',')
                if len(parts) == 4:
                    return {
                        'machine_id': int(parts[0]),
                        'ax': float(parts[1]),
                        'ay': float(parts[2]),
                        'az': float(parts[3])
                    }
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error reading sensor data: {e}")
        
        return None
    
    def calculate_vibration_magnitude(self, ax, ay, az):
        """Calculate vibration magnitude from acceleration values"""
        return math.sqrt(ax**2 + ay**2 + az**2)
    
    def process_sensor_data(self, data, app):
        """Process sensor data and update machine status"""
        with app.app_context():
            machine_id = data['machine_id']
            ax, ay, az = data['ax'], data['ay'], data['az']
            vibration = self.calculate_vibration_magnitude(ax, ay, az)
            
            # Store sensor reading
            reading = SensorReading(
                machine_id=machine_id,
                acceleration_x=ax,
                acceleration_y=ay,
                acceleration_z=az,
                vibration_magnitude=vibration,
                timestamp=datetime.utcnow()
            )
            db.session.add(reading)
            
            # Get machine
            machine = Machine.query.get(machine_id)
            if not machine:
                return
            
            # Determine if machine is running based on vibration
            is_running = vibration > self.vibration_threshold
            
            # Update machine status if changed
            if is_running != machine.is_running:
                machine.is_running = is_running
                machine.last_status_change = datetime.utcnow()
                
                if is_running:
                    # Start new session
                    session = MachineSession(
                        machine_id=machine_id,
                        start_time=datetime.utcnow()
                    )
                    db.session.add(session)
                    print(f"Machine {machine.name} started")
                else:
                    # End current session
                    session = MachineSession.query.filter_by(
                        machine_id=machine_id,
                        end_time=None
                    ).first()
                    if session:
                        session.end_time = datetime.utcnow()
                        session.duration = int((session.end_time - session.start_time).total_seconds())
                        print(f"Machine {machine.name} stopped (duration: {session.duration}s)")
            
            db.session.commit()
    
    def monitoring_loop(self, app):
        """Main monitoring loop"""
        while self.running:
            data = self.read_sensor_data()
            if data:
                self.process_sensor_data(data, app)
            time.sleep(0.1)  # Small delay to prevent CPU overuse
    
    def start_monitoring(self, app):
        """Start monitoring in a background thread"""
        if self.running:
            return False
        
        if not self.connect():
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self.monitoring_loop, args=(app,))
        self.thread.daemon = True
        self.thread.start()
        print("Monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.disconnect()
        print("Monitoring stopped")
