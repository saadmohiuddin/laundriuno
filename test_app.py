"""
Simple test to verify Flask API endpoints work correctly
This can be run without an Arduino connected
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_store import DataStore
from app.arduino_interface import ArduinoInterface
import json

def test_data_store():
    """Test the DataStore functionality"""
    print("Testing DataStore...")
    
    store = DataStore(num_machines=4)
    
    # Test initial state
    status = store.get_all_status()
    assert len(status) == 4, "Should have 4 machines"
    assert all(not m['in_use'] for m in status), "All machines should be free initially"
    print("✓ Initial state correct")
    
    # Test updating machine status
    store.update_machine_status(0, True)
    machine = store.get_machine_status(0)
    assert machine['in_use'] == True, "Machine 0 should be in use"
    assert machine['total_uses'] == 1, "Machine 0 should have 1 use"
    print("✓ Status updates work")
    
    # Test statistics
    stats = store.get_statistics()
    assert stats['machines_in_use'] == 1, "Should have 1 machine in use"
    assert stats['machines_free'] == 3, "Should have 3 machines free"
    assert stats['total_uses'] == 1, "Should have 1 total use"
    print("✓ Statistics calculation works")
    
    # Test history
    history = store.get_machine_history(0)
    assert len(history) > 0, "Should have history entries"
    print("✓ History tracking works")
    
    print("✅ DataStore tests passed!\n")

def test_arduino_interface():
    """Test Arduino interface without actual hardware"""
    print("Testing ArduinoInterface (without hardware)...")
    
    store = DataStore(num_machines=4)
    arduino = ArduinoInterface(port='/dev/ttyUSB0', baud_rate=9600, data_store=store)
    
    # Test initial state
    assert not arduino.is_connected(), "Should not be connected without hardware"
    print("✓ Connection state correct")
    
    # Test message parsing
    arduino._parse_message("MACHINE:0:IN_USE")
    machine = store.get_machine_status(0)
    assert machine['in_use'] == True, "Machine should be in use after parsing"
    print("✓ Message parsing works")
    
    arduino._parse_message("MACHINE:0:FREE")
    machine = store.get_machine_status(0)
    assert machine['in_use'] == False, "Machine should be free after parsing"
    print("✓ Status change parsing works")
    
    print("✅ ArduinoInterface tests passed!\n")

def test_flask_app():
    """Test Flask application without running server"""
    print("Testing Flask app structure...")
    
    # Import the Flask app instance
    from main import app as flask_app
    
    # Check that routes are registered
    assert flask_app is not None, "Flask app should exist"
    
    # Get the list of registered routes
    routes = [str(rule) for rule in flask_app.url_map.iter_rules()]
    
    expected_routes = [
        '/api/status',
        '/api/machine/<int:machine_id>',
        '/api/history/<int:machine_id>',
        '/api/stats',
        '/api/arduino/connect',
        '/api/arduino/disconnect',
        '/api/arduino/status',
        '/'
    ]
    
    for route in expected_routes:
        # Check if route exists (normalize the format)
        route_base = route.split('<')[0].rstrip('/')
        found = any(route_base in r for r in routes)
        assert found, f"Route {route} should be registered"
    
    print("✓ All expected routes registered")
    print("✅ Flask app tests passed!\n")

if __name__ == '__main__':
    print("="*60)
    print("Running Laundriuno Test Suite")
    print("="*60 + "\n")
    
    try:
        test_data_store()
        test_arduino_interface()
        test_flask_app()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
