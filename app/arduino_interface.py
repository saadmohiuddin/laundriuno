"""
Arduino Interface Module
Handles serial communication with Arduino
"""
import serial
import threading
import time
import logging

logger = logging.getLogger(__name__)

class ArduinoInterface:
    """Interface for communicating with Arduino via serial connection"""
    
    def __init__(self, port='/dev/ttyUSB0', baud_rate=9600, data_store=None):
        """
        Initialize Arduino interface
        
        Args:
            port: Serial port for Arduino connection
            baud_rate: Baud rate for serial communication
            data_store: DataStore instance for saving machine status
        """
        self.port = port
        self.baud_rate = baud_rate
        self.data_store = data_store
        self.serial_conn = None
        self.running = False
        self.reader_thread = None
        self._connected = False
        
    def connect(self):
        """
        Establish connection to Arduino
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Arduino on {self.port} at {self.baud_rate} baud...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            time.sleep(2)  # Wait for Arduino to reset
            
            # Wait for READY signal
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line == "READY":
                        logger.info("Arduino is ready")
                        break
            
            # Start reader thread
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.reader_thread.start()
            
            self._connected = True
            logger.info("Successfully connected to Arduino")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Arduino: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join(timeout=2)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from Arduino")
        self._connected = False
    
    def is_connected(self):
        """
        Check if connected to Arduino
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self.serial_conn and self.serial_conn.is_open
    
    def send_command(self, command):
        """
        Send command to Arduino
        
        Args:
            command: Command string to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_connected():
            logger.warning("Cannot send command: Not connected to Arduino")
            return False
            
        try:
            self.serial_conn.write(f"{command}\n".encode('utf-8'))
            logger.debug(f"Sent command to Arduino: {command}")
            return True
        except Exception as e:
            logger.error(f"Error sending command to Arduino: {e}")
            return False
    
    def request_status(self):
        """Request current status of all machines from Arduino"""
        return self.send_command("STATUS")
    
    def _read_loop(self):
        """Background thread for reading data from Arduino"""
        logger.info("Starting Arduino reader thread")
        
        while self.running:
            try:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        self._parse_message(line)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in reader loop: {e}")
                if not self.serial_conn or not self.serial_conn.is_open:
                    self._connected = False
                    break
        
        logger.info("Arduino reader thread stopped")
    
    def _parse_message(self, message):
        """
        Parse message from Arduino and update data store
        
        Message format: MACHINE:<id>:<status>
        Example: MACHINE:0:IN_USE or MACHINE:1:FREE
        """
        logger.debug(f"Received from Arduino: {message}")
        
        if message.startswith("MACHINE:"):
            try:
                parts = message.split(":")
                if len(parts) == 3:
                    machine_id = int(parts[1])
                    status = parts[2]
                    
                    in_use = (status == "IN_USE")
                    
                    if self.data_store:
                        self.data_store.update_machine_status(machine_id, in_use)
                        logger.info(f"Updated machine {machine_id}: {status}")
                    
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing message '{message}': {e}")
        elif message == "PONG":
            logger.debug("Received PONG from Arduino")
        elif message == "READY":
            logger.info("Arduino ready signal received")
