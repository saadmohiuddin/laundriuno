import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///laundriuno.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Arduino settings
    ARDUINO_PORT = os.environ.get('ARDUINO_PORT') or '/dev/ttyUSB0'
    ARDUINO_BAUD_RATE = int(os.environ.get('ARDUINO_BAUD_RATE') or 9600)
    
    # Machine settings
    NUM_MACHINES = int(os.environ.get('NUM_MACHINES') or 4)
    VIBRATION_THRESHOLD = int(os.environ.get('VIBRATION_THRESHOLD') or 1000)
    IDLE_TIMEOUT = int(os.environ.get('IDLE_TIMEOUT') or 300)  # seconds
