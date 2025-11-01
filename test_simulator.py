"""
Test script to simulate sensor data for testing without Arduino hardware
Usage: python test_simulator.py
"""

import requests
import time
import random
import math

BASE_URL = "http://localhost:5000/api"

def simulate_sensor_data(machine_id, is_running):
    """Generate simulated sensor data"""
    if is_running:
        # Simulate vibration (high magnitude)
        base = 5000
        ax = random.uniform(-base, base)
        ay = random.uniform(-base, base)
        az = random.uniform(-base, base)
    else:
        # Simulate idle state (low magnitude)
        base = 500
        ax = random.uniform(-base, base)
        ay = random.uniform(-base, base)
        az = random.uniform(-base, base)
    
    magnitude = math.sqrt(ax**2 + ay**2 + az**2)
    return ax, ay, az, magnitude

def test_api_endpoints():
    """Test all API endpoints"""
    print("=" * 50)
    print("Testing Laundriuno API Endpoints")
    print("=" * 50)
    
    # Test machine status
    print("\n1. Testing GET /api/machines")
    try:
        response = requests.get(f"{BASE_URL}/machines")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test available machines
    print("\n2. Testing GET /api/machines/available")
    try:
        response = requests.get(f"{BASE_URL}/machines/available")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test statistics
    print("\n3. Testing GET /api/statistics")
    try:
        response = requests.get(f"{BASE_URL}/statistics?days=7")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test best times
    print("\n4. Testing GET /api/best-times")
    try:
        response = requests.get(f"{BASE_URL}/best-times?days=7")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test availability
    print("\n5. Testing GET /api/availability")
    try:
        response = requests.get(f"{BASE_URL}/availability?days=7")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {len(data)} hourly entries")
        if len(data) > 0:
            print(f"Sample: {data[0]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test monitoring status
    print("\n6. Testing GET /api/monitoring/status")
    try:
        response = requests.get(f"{BASE_URL}/monitoring/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("API Testing Complete")
    print("=" * 50)

def show_sensor_simulation():
    """Show simulated sensor readings"""
    print("\n" + "=" * 50)
    print("Simulated Sensor Data Examples")
    print("=" * 50)
    
    print("\nMachine 1 - IDLE:")
    ax, ay, az, mag = simulate_sensor_data(1, False)
    print(f"  Acceleration: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f}")
    print(f"  Magnitude: {mag:.2f}")
    
    print("\nMachine 1 - RUNNING:")
    ax, ay, az, mag = simulate_sensor_data(1, True)
    print(f"  Acceleration: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f}")
    print(f"  Magnitude: {mag:.2f}")
    
    print("\nNote: Threshold is typically 1000")
    print("Values > 1000 indicate machine is running")

if __name__ == "__main__":
    print("Laundriuno API Test Utility")
    print("\nMake sure the Flask app is running on http://localhost:5000")
    print("Press Ctrl+C to exit\n")
    
    try:
        input("Press Enter to test API endpoints...")
        test_api_endpoints()
        
        input("\nPress Enter to see simulated sensor data...")
        show_sensor_simulation()
        
        print("\n✓ Testing complete!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to Flask app")
        print("Make sure the app is running: python app.py")
