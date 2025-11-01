"""
MQTT Interface Module for Laundriuno System

This module provides MQTT-based communication between the Flask backend server
and Arduino devices equipped with IMU sensors. MQTT (Message Queuing Telemetry
Transport) is a lightweight publish-subscribe messaging protocol ideal for IoT
applications.

Architecture:
    - Arduino devices publish sensor readings to MQTT topics
    - Flask backend subscribes to these topics and processes data
    - Supports multiple Arduino devices simultaneously
    - Provides connection management and error handling

MQTT Topic Structure:
    - Sensor data: laundriuno/sensor/{machine_id}/data
    - Status updates: laundriuno/sensor/{machine_id}/status
    - Control commands: laundriuno/control/{machine_id}/command

Message Format:
    Sensor data messages are JSON formatted:
    {
        "machine_id": 1,
        "ax": 1234.56,
        "ay": 789.01,
        "az": 456.78,
        "timestamp": 1635724800
    }

Dependencies:
    - paho-mqtt: Python MQTT client library
    - threading: For background MQTT event loop
    - json: For message parsing
    - datetime: For timestamp handling

Author: Laundriuno System
Version: 1.0.0
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime
from models import db, Machine, MachineSession, SensorReading
import math


class MQTTInterface:
    """
    MQTT Interface for Laundriuno System
    
    This class manages MQTT communication between the Flask backend and Arduino
    sensors. It handles connection management, message processing, and state
    detection for laundry machines.
    
    Attributes:
        broker_host (str): MQTT broker hostname or IP address
        broker_port (int): MQTT broker port (default: 1883)
        vibration_threshold (float): Threshold for detecting machine running state
        client (mqtt.Client): Paho MQTT client instance
        running (bool): Flag indicating if monitoring is active
        thread (Thread): Background thread for MQTT loop
        
    Example:
        >>> mqtt_interface = MQTTInterface(
        ...     broker_host="localhost",
        ...     broker_port=1883,
        ...     vibration_threshold=1000
        ... )
        >>> mqtt_interface.start_monitoring(app)
    """
    
    def __init__(self, broker_host, broker_port, vibration_threshold):
        """
        Initialize MQTT Interface
        
        Sets up the MQTT client with connection parameters and configures
        callback functions for connection events and message handling.
        
        Args:
            broker_host (str): MQTT broker hostname (e.g., 'localhost', '192.168.1.100')
            broker_port (int): MQTT broker port number (typically 1883 for non-TLS)
            vibration_threshold (float): Vibration magnitude threshold above which
                                        a machine is considered to be running
        
        Returns:
            None
            
        Note:
            The client is created but not connected. Call connect() or 
            start_monitoring() to establish connection.
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.vibration_threshold = vibration_threshold
        self.client = None
        self.running = False
        self.thread = None
        self.app = None
        
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for MQTT connection events
        
        This internal method is called automatically by the Paho MQTT client
        when a connection attempt completes. It handles both successful and
        failed connection attempts.
        
        Args:
            client (mqtt.Client): The MQTT client instance
            userdata: User-defined data passed to callbacks (unused)
            flags (dict): Response flags from the broker
            rc (int): Connection result code:
                0: Success
                1: Incorrect protocol version
                2: Invalid client identifier
                3: Server unavailable
                4: Bad username or password
                5: Not authorized
        
        Returns:
            None
            
        Side Effects:
            - Prints connection status to console
            - Subscribes to sensor data topic on successful connection
            
        Note:
            The wildcard '#' in the topic subscription means we receive
            messages from all machine IDs.
        """
        if rc == 0:
            print(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to all sensor data topics (wildcard: all machine IDs)
            client.subscribe("laundriuno/sensor/+/data")
            print("Subscribed to topic: laundriuno/sensor/+/data")
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback for incoming MQTT messages
        
        This internal method is called automatically when a message is received
        on a subscribed topic. It parses the message, extracts sensor data,
        and processes it to update machine states.
        
        Args:
            client (mqtt.Client): The MQTT client instance
            userdata: User-defined data passed to callbacks (unused)
            msg (mqtt.MQTTMessage): The received message containing:
                - topic (str): The message topic
                - payload (bytes): The message payload (JSON data)
                - qos (int): Quality of Service level
                - retain (bool): Retain flag
        
        Returns:
            None
            
        Side Effects:
            - Parses JSON payload
            - Calls process_sensor_data() to update database
            - Prints error messages for invalid data
            
        Message Format:
            Expected JSON structure:
            {
                "machine_id": <int>,
                "ax": <float>,      # X-axis acceleration
                "ay": <float>,      # Y-axis acceleration
                "az": <float>,      # Z-axis acceleration
                "timestamp": <int>  # Unix timestamp (optional)
            }
            
        Error Handling:
            - Catches JSON decode errors
            - Catches missing required fields
            - Prints error messages but continues processing
        """
        try:
            # Decode the message payload from bytes to string
            payload = msg.payload.decode('utf-8')
            
            # Parse JSON data
            data = json.loads(payload)
            
            # Validate required fields are present
            if all(key in data for key in ['machine_id', 'ax', 'ay', 'az']):
                # Process the sensor data
                self.process_sensor_data(data, self.app)
            else:
                print(f"Invalid message format: {data}")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON message: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback for MQTT disconnection events
        
        This internal method is called when the client disconnects from the
        broker, either intentionally or due to network issues.
        
        Args:
            client (mqtt.Client): The MQTT client instance
            userdata: User-defined data passed to callbacks (unused)
            rc (int): Disconnection result code:
                0: Successful disconnection (client.disconnect() called)
                >0: Unexpected disconnection
        
        Returns:
            None
            
        Side Effects:
            - Prints disconnection status to console
            
        Note:
            If rc > 0, it indicates an unexpected disconnection, which might
            require reconnection logic in production environments.
        """
        if rc == 0:
            print("Disconnected from MQTT broker successfully")
        else:
            print(f"Unexpected disconnection from MQTT broker, code: {rc}")
    
    def connect(self):
        """
        Establish connection to MQTT broker
        
        Creates a new MQTT client instance, registers callback functions,
        and attempts to connect to the configured broker.
        
        Args:
            None
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Side Effects:
            - Creates self.client (mqtt.Client instance)
            - Registers callback functions (_on_connect, _on_message, _on_disconnect)
            - Attempts connection to broker
            - Prints connection status
            
        Connection Process:
            1. Create MQTT client with unique client ID
            2. Register event callbacks
            3. Attempt connection to broker
            4. Return success/failure status
            
        Error Handling:
            Catches all exceptions during connection and returns False
            
        Example:
            >>> mqtt_interface = MQTTInterface("localhost", 1883, 1000)
            >>> if mqtt_interface.connect():
            ...     print("Connected successfully")
        """
        try:
            # Create MQTT client with unique client ID based on timestamp
            client_id = f"laundriuno_backend_{int(time.time())}"
            self.client = mqtt.Client(client_id)
            
            # Register callback functions
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnect from MQTT broker
        
        Cleanly disconnects the MQTT client from the broker and stops the
        network loop.
        
        Args:
            None
        
        Returns:
            None
            
        Side Effects:
            - Calls client.disconnect() if client exists
            - Stops the MQTT network loop
            - Prints disconnection message
            
        Note:
            This method is safe to call even if not connected. It checks
            for client existence before attempting disconnection.
            
        Example:
            >>> mqtt_interface.disconnect()
            Disconnected from MQTT broker
        """
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            print("Disconnected from MQTT broker")
    
    def calculate_vibration_magnitude(self, ax, ay, az):
        """
        Calculate vibration magnitude from acceleration values
        
        Computes the Euclidean magnitude of the 3D acceleration vector. This
        magnitude represents the overall vibration intensity of the machine.
        
        Args:
            ax (float): Acceleration in X-axis (m/s² or arbitrary units)
            ay (float): Acceleration in Y-axis (m/s² or arbitrary units)
            az (float): Acceleration in Z-axis (m/s² or arbitrary units)
        
        Returns:
            float: Vibration magnitude calculated as sqrt(ax² + ay² + az²)
            
        Mathematical Formula:
            magnitude = √(ax² + ay² + az²)
            
        Example:
            >>> mqtt_interface.calculate_vibration_magnitude(1000, 500, 800)
            1346.29
            
        Note:
            The units of the result match the units of the input values.
            Typically, accelerometer values are in m/s² or milli-g.
        """
        return math.sqrt(ax**2 + ay**2 + az**2)
    
    def process_sensor_data(self, data, app):
        """
        Process incoming sensor data and update machine states
        
        This is the core processing method that:
        1. Stores the raw sensor reading in the database
        2. Calculates vibration magnitude
        3. Determines if the machine is running or idle
        4. Updates machine state if changed
        5. Creates or ends machine usage sessions
        
        Args:
            data (dict): Sensor data dictionary containing:
                - machine_id (int): Unique machine identifier
                - ax (float): X-axis acceleration
                - ay (float): Y-axis acceleration
                - az (float): Z-axis acceleration
            app (Flask): Flask application instance for database context
        
        Returns:
            None
            
        Side Effects:
            - Creates SensorReading record in database
            - Updates Machine.is_running status
            - Updates Machine.last_status_change timestamp
            - Creates new MachineSession when machine starts
            - Ends current MachineSession when machine stops
            - Commits all changes to database
            - Prints state change messages to console
            
        State Detection Logic:
            1. Calculate vibration: magnitude = √(ax² + ay² + az²)
            2. Compare to threshold:
               - magnitude > threshold → Machine is RUNNING
               - magnitude ≤ threshold → Machine is IDLE
            3. Detect state change:
               - IDLE → RUNNING: Start new session
               - RUNNING → IDLE: End current session
        
        Database Operations:
            - INSERT into sensor_reading (always)
            - UPDATE machine SET is_running, last_status_change (on state change)
            - INSERT into machine_session (on start)
            - UPDATE machine_session SET end_time, duration (on stop)
            
        Example:
            >>> data = {
            ...     'machine_id': 1,
            ...     'ax': 2000.0,
            ...     'ay': 1500.0,
            ...     'az': 1800.0
            ... }
            >>> mqtt_interface.process_sensor_data(data, flask_app)
            Machine Machine 1 started
        """
        with app.app_context():
            # Extract sensor values
            machine_id = data['machine_id']
            ax, ay, az = data['ax'], data['ay'], data['az']
            
            # Calculate vibration magnitude
            vibration = self.calculate_vibration_magnitude(ax, ay, az)
            
            # Store sensor reading in database
            reading = SensorReading(
                machine_id=machine_id,
                acceleration_x=ax,
                acceleration_y=ay,
                acceleration_z=az,
                vibration_magnitude=vibration,
                timestamp=datetime.now()
            )
            db.session.add(reading)
            
            # Get machine record from database
            machine = Machine.query.get(machine_id)
            if not machine:
                # Machine doesn't exist in database, skip processing
                print(f"Warning: Machine ID {machine_id} not found in database")
                return
            
            # Determine if machine is running based on vibration threshold
            is_running = vibration > self.vibration_threshold
            
            # Check if machine state has changed
            if is_running != machine.is_running:
                # State has changed - update machine record
                machine.is_running = is_running
                machine.last_status_change = datetime.now()
                
                if is_running:
                    # Machine just started - create new session
                    session = MachineSession(
                        machine_id=machine_id,
                        start_time=datetime.now()
                    )
                    db.session.add(session)
                    print(f"Machine {machine.name} started")
                    
                else:
                    # Machine just stopped - end current session
                    # Find the most recent session without an end time
                    session = MachineSession.query.filter_by(
                        machine_id=machine_id,
                        end_time=None
                    ).first()
                    
                    if session:
                        # Calculate session duration and update record
                        session.end_time = datetime.now()
                        session.duration = int(
                            (session.end_time - session.start_time).total_seconds()
                        )
                        print(f"Machine {machine.name} stopped (duration: {session.duration}s)")
            
            # Commit all database changes
            db.session.commit()
    
    def monitoring_loop(self, app):
        """
        Main monitoring loop running in background thread
        
        This method runs continuously in a separate thread, maintaining the
        MQTT connection and processing incoming messages. It's the heart of
        the real-time monitoring system.
        
        Args:
            app (Flask): Flask application instance for database context
        
        Returns:
            None
            
        Behavior:
            - Stores Flask app reference for database operations
            - Starts MQTT network loop (blocking call)
            - Runs until self.running becomes False
            - Handles MQTT events and callbacks
            
        Thread Safety:
            This method is designed to run in a separate thread. The MQTT
            client handles its own thread safety, and database operations
            use Flask's app context for thread-local database sessions.
            
        MQTT Loop:
            The loop_forever() method:
            - Handles network traffic
            - Processes callbacks (on_message, on_connect, etc.)
            - Manages automatic reconnection
            - Blocks until client.disconnect() is called
            
        Note:
            This method blocks indefinitely. Call stop_monitoring() to exit.
            
        Example:
            This method is typically called internally by start_monitoring()
            and runs in a background thread.
        """
        self.app = app
        # Start MQTT network loop (blocks until disconnect)
        self.client.loop_forever()
    
    def start_monitoring(self, app):
        """
        Start MQTT monitoring in background thread
        
        Initiates the monitoring system by connecting to the MQTT broker and
        starting a background thread to handle messages. This is the main
        entry point for beginning machine monitoring.
        
        Args:
            app (Flask): Flask application instance for database context
        
        Returns:
            bool: True if monitoring started successfully, False otherwise
            
        Process:
            1. Check if already running (prevent duplicate starts)
            2. Connect to MQTT broker
            3. Create and start background thread
            4. Set running flag
            5. Print status message
            
        Side Effects:
            - Creates self.thread (Thread instance)
            - Sets self.running = True
            - Starts background MQTT loop
            - Connects to MQTT broker
            
        Thread Configuration:
            - Thread target: monitoring_loop()
            - Daemon: True (thread exits when main program exits)
            - Started immediately upon creation
            
        Error Handling:
            Returns False if connection fails, True on success
            
        Example:
            >>> mqtt_interface = MQTTInterface("localhost", 1883, 1000)
            >>> if mqtt_interface.start_monitoring(flask_app):
            ...     print("Monitoring started")
            ... else:
            ...     print("Failed to start monitoring")
        """
        if self.running:
            # Already running, don't start again
            print("Monitoring already running")
            return False
        
        # Connect to MQTT broker
        if not self.connect():
            return False
        
        # Set running flag
        self.running = True
        
        # Start background thread for MQTT loop
        self.thread = threading.Thread(target=self.monitoring_loop, args=(app,))
        self.thread.daemon = True  # Thread exits when main program exits
        self.thread.start()
        
        print("MQTT monitoring started")
        return True
    
    def stop_monitoring(self):
        """
        Stop MQTT monitoring and clean up resources
        
        Gracefully shuts down the monitoring system by disconnecting from
        the MQTT broker and stopping the background thread.
        
        Args:
            None
        
        Returns:
            None
            
        Process:
            1. Clear running flag
            2. Disconnect from MQTT broker (stops loop_forever())
            3. Wait for thread to terminate (with timeout)
            4. Print status message
            
        Side Effects:
            - Sets self.running = False
            - Disconnects MQTT client
            - Waits for background thread to finish (max 5 seconds)
            - Prints stop message
            
        Thread Cleanup:
            Uses thread.join(timeout=5) to wait for graceful shutdown.
            After 5 seconds, continues even if thread hasn't finished.
            
        Safety:
            Safe to call multiple times or when not running. Checks are
            performed internally.
            
        Example:
            >>> mqtt_interface.stop_monitoring()
            MQTT monitoring stopped
        """
        self.running = False
        
        # Disconnect from MQTT broker (this stops loop_forever())
        if self.client:
            self.disconnect()
        
        # Wait for thread to finish (with timeout)
        if self.thread:
            self.thread.join(timeout=5)
        
        print("MQTT monitoring stopped")


def publish_sensor_data(broker_host, broker_port, machine_id, ax, ay, az):
    """
    Utility function to publish sensor data to MQTT broker
    
    This is a helper function that can be used by Arduino devices or
    testing scripts to publish sensor data to the MQTT broker. It creates
    a temporary client, publishes one message, and disconnects.
    
    Args:
        broker_host (str): MQTT broker hostname or IP address
        broker_port (int): MQTT broker port number
        machine_id (int): Unique identifier for the machine
        ax (float): Acceleration in X-axis
        ay (float): Acceleration in Y-axis
        az (float): Acceleration in Z-axis
    
    Returns:
        bool: True if publish successful, False otherwise
        
    Message Structure:
        Published as JSON to topic: laundriuno/sensor/{machine_id}/data
        {
            "machine_id": <machine_id>,
            "ax": <ax>,
            "ay": <ay>,
            "az": <az>,
            "timestamp": <current_unix_timestamp>
        }
    
    MQTT Configuration:
        - QoS: 1 (at least once delivery)
        - Retain: False (message not stored by broker)
        
    Error Handling:
        Catches all exceptions and returns False on failure
        
    Example:
        >>> publish_sensor_data("localhost", 1883, 1, 2000.0, 1500.0, 1800.0)
        True
        
    Note:
        This function is synchronous and blocks until publish completes.
        For high-frequency publishing, consider using a persistent client.
    """
    try:
        # Create temporary MQTT client
        client_id = f"laundriuno_publisher_{int(time.time())}"
        client = mqtt.Client(client_id)
        
        # Connect to broker
        client.connect(broker_host, broker_port, keepalive=60)
        
        # Prepare message payload
        payload = json.dumps({
            'machine_id': machine_id,
            'ax': ax,
            'ay': ay,
            'az': az,
            'timestamp': int(time.time())
        })
        
        # Publish message to appropriate topic
        topic = f"laundriuno/sensor/{machine_id}/data"
        result = client.publish(topic, payload, qos=1)
        
        # Wait for publish to complete
        result.wait_for_publish()
        
        # Disconnect from broker
        client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"Failed to publish sensor data: {e}")
        return False
