import threading
from flask import Flask, jsonify, render_template_string
import paho.mqtt.client as mqtt
import json
import time
import random

# --- MQTT Configuration ---
# Uses the same credentials as your Arduino
MQTT_BROKER = "127.0.0.1"  # Running on the same Mac, so localhost is best
MQTT_PORT = 1883
MQTT_USER = "ujju"
MQTT_PASS = "Oli*16620"
# We will subscribe to all topics under "home/laundry/"
MQTT_TOPIC = "home/laundry/#"

# --- Global State Management ---
# This dictionary will store the latest state of all devices.
# We use a lock to make it thread-safe, as MQTT and Flask run in different threads.
device_states = {}
state_lock = threading.Lock()

# --- NEW: List of fake nodes to simulate ---
FAKE_NODE_NAMES = ["fake_dryer_1", "fake_washer_2", "fake_dryer_2"]

# --- Flask App Initialization ---
app = Flask(__name__)

# --- MQTT Client Setup ---

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when the client connects to the broker."""
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the topic once connected
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback when a REAL message is received."""
    try:
        topic_parts = msg.topic.split('/')
        payload = msg.payload.decode('utf-8')
        
        # We expect topics like: "home/laundry/node_1/machine_state"
        if len(topic_parts) == 4:
            device_name = topic_parts[2]  # e.g., "node_1"
            state_type = topic_parts[3]   # e.g., "machine_state"
            
            print(f"[MQTT] Received: {device_name} -> {state_type} = {payload}")
            
            # Update the global state dictionary safely
            with state_lock:
                if device_name not in device_states:
                    device_states[device_name] = {}
                device_states[device_name][state_type] = payload
                
    except Exception as e:
        print(f"Error processing message: {e}")

def setup_mqtt():
    """Initializes and starts the MQTT client."""
    # We use MQTT v5, but v3.1.1 (the default) is also fine.
    # Using CallbackAPIVersion.VERSION2 for paho-mqtt 2.0+
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return
    
    # loop_start() runs the client in a separate background thread.
    # This is *essential* for use with Flask.
    client.loop_start()

# --- NEW: Background Simulation Thread ---

def simulate_fake_nodes():
    """
    A background thread function that simulates data for fake devices.
    This makes the dashboard look populated and active.
    """
    # Initialize fake states
    with state_lock:
        for name in FAKE_NODE_NAMES:
            if name not in device_states:
                device_states[name] = {
                    'machine_state': random.choice(['ON', 'OFF']),
                    'door_state': random.choice(['Open', 'Closed'])
                }
    
    # Loop forever, randomly updating one node
    while True:
        try:
            # Update every 3-8 seconds
            time.sleep(random.uniform(3.0, 8.0))
            
            node_name = random.choice(FAKE_NODE_NAMES)
            
            with state_lock:
                # 50% chance to toggle machine state
                if random.random() < 0.5:
                    current_state = device_states[node_name]['machine_state']
                    new_state = 'OFF' if current_state == 'ON' else 'ON'
                    device_states[node_name]['machine_state'] = new_state
                    print(f"[SIM] {node_name}: Machine state -> {new_state}")
                
                # 30% chance to toggle door state
                if random.random() < 0.3:
                    current_state = device_states[node_name]['door_state']
                    new_state = 'Closed' if current_state == 'Open' else 'Open'
                    device_states[node_name]['door_state'] = new_state
                    print(f"[SIM] {node_name}: Door state -> {new_state}")

        except Exception as e:
            print(f"Error in simulation thread: {e}")
            time.sleep(5) # Don't spam errors

# --- Flask Web Routes ---

# Simple HTML template for the dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Laundry Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
        }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: #f8f9fa; 
            color: #343a40;
            margin: 0;
            padding: 16px;
        }
        header {
            max-width: 900px;
            margin: 0 auto 24px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { 
            color: #212529;
            font-weight: 700;
            margin: 0;
        }
        .live-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            font-weight: 500;
            color: #6c757d;
        }
        .live-dot {
            width: 10px;
            height: 10px;
            background-color: #28a745;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            max-width: 900px;
            margin: 0 auto;
        }
        .device {
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            padding: 20px 24px;
            transition: all 0.3s ease;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .device h2 {
            margin: 0 0 16px 0;
            color: #004a99;
            font-weight: 600;
            font-size: 1.25em;
            text-transform: capitalize;
        }
        .state {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 1em;
            margin-bottom: 12px;
        }
        .state:last-child {
            margin-bottom: 0;
        }
        .state-name {
            font-weight: 500;
            color: #495057;
            text-transform: capitalize;
        }
        .state-value {
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.9em;
            min-width: 70px;
            text-align: center;
        }
        /* Dynamic styles based on value */
        .state-value[data-value="ON"] {
            background-color: #d4edda;
            color: #155724;
        }
        .state-value[data-value="Open"] {
            background-color: #cce5ff;
            color: #004085;
        }
        .state-value[data-value="OFF"] {
            background-color: #f8d7da;
            color: #721c24;
        }
        .state-value[data-value="Closed"] {
            background-color: #e2e3e5;
            color: #343a40;
        }
        .waiting {
            grid-column: 1 / -1;
            text-align: center;
            font-style: italic;
            color: #888;
            padding: 40px;
            background: #fff;
            border-radius: 12px;
        }
        #refresh-status {
            text-align: center;
            font-size: 0.8em;
            color: #aaa;
            margin-top: 24px;
            grid-column: 1 / -1;
        }
    </style>
</head>
<body>
    <header>
        <h1>Laundry Monitor</h1>
        <div class="live-indicator">
            <span class="live-dot"></span>
            <span>Live</span>
        </div>
    </header>
    
    <div class="container" id="devices-container">
        <!-- Device states will be injected here -->
    </div>
    <div id="refresh-status"></div>

    <script>
        function fetchStates() {
            fetch('/api/states')
                .then(response => response.json())
                .then(data => {
                    const devicesContainer = document.getElementById('devices-container');
                    
                    if (Object.keys(data).length === 0) {
                        if (!document.querySelector('.waiting')) {
                            devicesContainer.innerHTML = '<p class="waiting">Waiting for device data...</p>';
                        }
                        return;
                    }

                    // --- Sort keys so "node_1" (real) is always first ---
                    const sortedDeviceNames = Object.keys(data).sort((a, b) => {
                        if (a.includes('node_1')) return -1;
                        if (b.includes('node_1')) return 1;
                        return a.localeCompare(b);
                    });
                    
                    let hasRealData = false;

                    for (const deviceName of sortedDeviceNames) {
                        // Find or create device element
                        let deviceElement = document.getElementById(deviceName);
                        if (!deviceElement) {
                            deviceElement = document.createElement('div');
                            deviceElement.className = 'device';
                            deviceElement.id = deviceName;
                            
                            let deviceHTML = `<h2>${deviceName.replace('_', ' ')}</h2>`;
                            const states = data[deviceName];
                            for (const stateType in states) {
                                deviceHTML += `<div class="state" data-state-type="${stateType}"></div>`;
                            }
                            deviceElement.innerHTML = deviceHTML;
                            
                            // If this is the first item, remove the "waiting" message
                            const waitingMessage = devicesContainer.querySelector('.waiting');
                            if (waitingMessage) {
                                waitingMessage.remove();
                            }
                            devicesContainer.appendChild(deviceElement);
                        }
                        
                        // Update states within the device element
                        const states = data[deviceName];
                        for (const stateType in states) {
                            const stateValue = states[stateType];
                            const cleanStateType = stateType.replace('machine_', '').replace('_', ' ');
                            
                            const stateElement = deviceElement.querySelector(`.state[data-state-type="${stateType}"]`);
                            const stateHTML = `
                                <span class="state-name">${cleanStateType}</span>
                                <span class="state-value" data-value="${stateValue}">${stateValue}</span>
                            `;
                            // Only update if content is different to avoid flicker
                            if (stateElement.innerHTML !== stateHTML) {
                                stateElement.innerHTML = stateHTML;
                            }
                        }
                        
                        if(deviceName.includes('node_1')) hasRealData = true;
                    }
                    
                    // Update the refresh status
                    const status = document.getElementById('refresh-status');
                    status.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
                    
                    // Update header for real node
                    const header = document.querySelector('h1');
                    if(hasRealData){
                         header.textContent = "Laundry Monitor (node_1 Online)";
                    } else {
                         header.textContent = "Laundry Monitor (Simulation)";
                    }
                })
                .catch(error => {
                    console.error('Error fetching states:', error);
                    const devicesContainer = document.getElementById('devices-container');
                    devicesContainer.innerHTML = '<p class="waiting">Error connecting to server.</p>';
                });
        }
        
        // --- Added helper to capitalize state names ---
        String.prototype.title = function() {
            return this.charAt(0).toUpperCase() + this.slice(1);
        }

        // Fetch new data every 2 seconds
        setInterval(fetchStates, 2000);
        // Fetch immediately on load
        document.addEventListener('DOMContentLoaded', fetchStates);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serves the main HTML dashboard."""
    # The HTML template is rendered directly from the string
    return HTML_TEMPLATE

@app.route('/api/states')
def api_states():
    """Provides a JSON API endpoint for the front-end to fetch data."""
    with state_lock:
        # Return a *copy* of the state dictionary
        current_states = device_states.copy()
    return jsonify(current_states)

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting MQTT client...")
    setup_mqtt()
    
    # --- NEW: Start the simulation thread ---
    print("Starting device simulation thread...")
    sim_thread = threading.Thread(target=simulate_fake_nodes, daemon=True)
    sim_thread.start()
    # --- End NEW ---
    
    print("Starting Flask web server on http://127.0.0.1:5000")
    # We must run with use_reloader=False. 
    # If the reloader is on, it runs the setup code twice,
    # which creates two MQTT clients that fight each other.
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8081)