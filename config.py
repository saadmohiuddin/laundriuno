"""
Configuration Module for Laundriuno System

This module manages all configuration settings for the Laundriuno application.
It loads environment variables from a .env file and provides default values
for all configuration parameters.

Configuration Categories:
    - Flask: Web framework settings
    - Database: SQLAlchemy database connection
    - Arduino: Serial communication parameters (legacy)
    - MQTT: Message broker connection settings
    - Machine: Detection and monitoring parameters

Environment Variables:
    All settings can be overridden using environment variables. See .env.example
    for a complete list of available configuration options.

Usage:
    from config import Config
    app.config.from_object(Config)

Author: Laundriuno System
Version: 1.0.0
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows configuration without modifying code
load_dotenv()


class Config:
    """
    Application Configuration Class
    
    This class defines all configuration parameters for the Laundriuno system.
    Values are loaded from environment variables with sensible defaults for
    development environments.
    
    Attributes:
        SECRET_KEY (str): Flask secret key for session security
        SQLALCHEMY_DATABASE_URI (str): Database connection string
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): SQLAlchemy event system flag
        ARDUINO_PORT (str): Serial port for Arduino connection (legacy)
        ARDUINO_BAUD_RATE (int): Serial communication speed (legacy)
        MQTT_BROKER_HOST (str): MQTT broker hostname or IP
        MQTT_BROKER_PORT (int): MQTT broker port number
        USE_MQTT (bool): Flag to enable MQTT mode vs serial mode
        NUM_MACHINES (int): Number of machines to monitor
        VIBRATION_THRESHOLD (int): Threshold for machine running detection
    
    Example:
        >>> config = Config()
        >>> print(config.MQTT_BROKER_HOST)
        'localhost'
    """
    
    # Flask Framework Configuration
    # -----------------------------
    
    # SECRET_KEY: Used for signing session cookies and CSRF tokens
    # In production, MUST be set to a random, secure value
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database Configuration
    # ----------------------
    
    # SQLALCHEMY_DATABASE_URI: Database connection string
    # Format: dialect://username:password@host:port/database
    # Examples:
    #   SQLite: sqlite:///laundriuno.db
    #   PostgreSQL: postgresql://user:pass@localhost/laundriuno
    #   MySQL: mysql://user:pass@localhost/laundriuno
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///laundriuno.db'
    
    # SQLALCHEMY_TRACK_MODIFICATIONS: Disable event system (not needed)
    # Setting to False reduces memory overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Arduino Serial Communication Settings (Legacy)
    # ----------------------------------------------
    # These settings are used when USE_MQTT is False
    
    # ARDUINO_PORT: Serial port where Arduino is connected
    # Common values:
    #   Linux: /dev/ttyUSB0, /dev/ttyACM0
    #   macOS: /dev/tty.usbserial-*, /dev/tty.usbmodem*
    #   Windows: COM3, COM4, COM5, etc.
    ARDUINO_PORT = os.environ.get('ARDUINO_PORT') or '/dev/ttyUSB0'
    
    # ARDUINO_BAUD_RATE: Serial communication speed in bits per second
    # Must match the value in Arduino sketch
    # Common values: 9600, 19200, 38400, 57600, 115200
    ARDUINO_BAUD_RATE = int(os.environ.get('ARDUINO_BAUD_RATE') or 9600)
    
    # MQTT Broker Configuration
    # -------------------------
    # These settings are used when USE_MQTT is True
    
    # MQTT_BROKER_HOST: Hostname or IP address of MQTT broker
    # Common values:
    #   localhost: For local Mosquitto broker
    #   test.mosquitto.org: Public test broker (not for production)
    #   broker.hivemq.com: Public HiveMQ broker (not for production)
    #   Custom IP: Your organization's MQTT broker
    MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST') or 'localhost'
    
    # MQTT_BROKER_PORT: Port number for MQTT broker
    # Standard ports:
    #   1883: MQTT (unencrypted)
    #   8883: MQTT over TLS/SSL (encrypted)
    #   8080: MQTT over WebSockets
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT') or 1883)
    
    # USE_MQTT: Toggle between MQTT and serial communication modes
    # True: Use MQTT broker for communication
    # False: Use direct serial connection (legacy)
    USE_MQTT = os.environ.get('USE_MQTT', 'true').lower() == 'true'
    
    # Machine Monitoring Configuration
    # --------------------------------
    
    # NUM_MACHINES: Total number of laundry machines to monitor
    # Each machine should have a unique ID from 1 to NUM_MACHINES
    # Adjust based on your deployment size
    NUM_MACHINES = int(os.environ.get('NUM_MACHINES') or 4)
    
    # VIBRATION_THRESHOLD: Threshold for detecting machine running state
    # Vibration magnitude above this value indicates machine is running
    # Units depend on accelerometer configuration (typically m/s² * 1000)
    # Adjust based on your specific machine vibration characteristics
    # Typical range: 500-2000 for washing machines
    VIBRATION_THRESHOLD = int(os.environ.get('VIBRATION_THRESHOLD') or 1000)

