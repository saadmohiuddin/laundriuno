# Building IoT Projects: A Learning Guide Using Laundriuno

This guide explains the key concepts, design patterns, and implementation techniques used in the Laundriuno system. Use this as a learning resource to build your own IoT monitoring projects.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Concepts](#key-concepts)
3. [System Architecture Patterns](#system-architecture-patterns)
4. [Implementation Walkthrough](#implementation-walkthrough)
5. [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
6. [Reusable Code Patterns](#reusable-code-patterns)
7. [Extending for Your Own Projects](#extending-for-your-own-projects)

---

## Project Overview

### What We're Building

Laundriuno is an IoT system that monitors laundry machines using vibration sensors and provides intelligent recommendations about when to do laundry. This type of project teaches fundamental concepts applicable to any IoT monitoring system.

### Learning Objectives

By studying this project, you'll learn:
- How to collect sensor data from physical devices
- How to process and store time-series data
- How to build REST APIs for IoT data
- How to implement real-time monitoring dashboards
- How to use message queuing for IoT communication
- How to analyze patterns in time-series data
- How to make predictions based on historical data

---

## Key Concepts

### 1. Sensor Data Collection

**Concept:** IoT systems start with sensors that measure physical phenomena.

**In Laundriuno:**
- We use an MPU6050 IMU (Inertial Measurement Unit) sensor
- It measures acceleration in 3 axes (X, Y, Z)
- Readings are taken at regular intervals (sampling rate)

**Applicable to other projects:**
- Temperature monitoring: Use DHT22 or DS18B20 sensors
- Light monitoring: Use photoresistors or light sensors
- Motion detection: Use PIR sensors
- Sound monitoring: Use microphone modules

**Key Code Pattern:**

```python
# Generic sensor reading pattern
def read_sensor_data(self):
    """
    Pattern for reading from any sensor
    1. Check if connection is valid
    2. Read raw data
    3. Parse and validate
    4. Return structured data
    """
    if not self.is_connected():
        return None
    
    try:
        raw_data = self.connection.read()
        parsed_data = self.parse(raw_data)
        if self.validate(parsed_data):
            return parsed_data
    except Exception as e:
        self.handle_error(e)
    
    return None
```

### 2. State Detection from Sensor Data

**Concept:** Raw sensor data needs to be interpreted to determine system state.

**In Laundriuno:**
- We calculate vibration magnitude: `magnitude = √(ax² + ay² + az²)`
- Compare to threshold: `is_running = magnitude > threshold`
- Track state changes (idle → running, running → idle)

**Mathematical Background:**

The Euclidean magnitude formula gives us the overall intensity of vibration:
```
magnitude = √(x² + y² + z²)
```

This works because:
- Each axis contributes to total vibration
- Squaring removes negative values
- Square root gives back original scale
- Result is always positive

**Applicable to other projects:**
- Temperature threshold: `is_overheating = temp > max_temp`
- Occupancy detection: `is_occupied = motion_count > threshold`
- Light-based automation: `should_turn_on = light_level < threshold`

**Key Code Pattern:**

```python
# Generic threshold-based state detection
def detect_state(self, sensor_value, threshold):
    """
    Pattern for threshold-based state detection
    1. Calculate derived metric from raw data
    2. Compare to threshold
    3. Detect state changes
    4. Log transitions
    """
    current_state = sensor_value > threshold
    
    if current_state != self.previous_state:
        self.on_state_change(self.previous_state, current_state)
        self.previous_state = current_state
    
    return current_state
```

### 3. Communication Protocols

**Concept:** IoT devices need to communicate data to backend systems.

**Two Approaches Demonstrated:**

#### Serial Communication (Simple)
```
Arduino --[USB Cable]--> Computer --[Direct Connection]--> Flask App
```

**Pros:**
- Simple setup
- Reliable
- No network configuration

**Cons:**
- Physical cable required
- One device per port
- Limited range

#### MQTT (Publish-Subscribe)
```
Arduino --[WiFi]--> MQTT Broker --[Network]--> Flask App
                        ↓
                   Other Subscribers
```

**Pros:**
- Wireless
- Multiple subscribers
- Scalable
- Industry standard

**Cons:**
- Requires MQTT broker
- Network dependency
- More complex setup

**When to Use Each:**

| Use Serial When | Use MQTT When |
|----------------|---------------|
| Prototyping | Production deployment |
| Single sensor | Multiple sensors |
| No WiFi available | Network available |
| Simple testing | Need scalability |

### 4. Database Design for Time-Series Data

**Concept:** IoT generates time-stamped data that needs efficient storage.

**Database Schema Design:**

```sql
-- Entity: What device/machine
CREATE TABLE machine (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50),
    is_running BOOLEAN,
    last_status_change DATETIME
);

-- Event: What happened and when
CREATE TABLE machine_session (
    id INTEGER PRIMARY KEY,
    machine_id INTEGER REFERENCES machine(id),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration INTEGER
);

-- Measurement: Detailed sensor data
CREATE TABLE sensor_reading (
    id INTEGER PRIMARY KEY,
    machine_id INTEGER REFERENCES machine(id),
    timestamp DATETIME NOT NULL,
    acceleration_x FLOAT,
    acceleration_y FLOAT,
    acceleration_z FLOAT,
    vibration_magnitude FLOAT
);
```

**Design Principles:**

1. **Separate entities from events**: Machines are entities, sessions are events
2. **Index timestamps**: Critical for time-series queries
3. **Store both raw and derived**: Keep raw (ax, ay, az) and calculated (magnitude)
4. **Denormalize when needed**: Store duration for quick queries

**Applicable to other projects:**
- Weather station: stations (entity) + readings (event)
- Energy monitor: devices (entity) + consumption (measurement)
- Security system: zones (entity) + triggers (event)

### 5. REST API Design

**Concept:** APIs provide programmatic access to IoT data.

**Resource-Based URL Structure:**

```
/api/machines              # Collection
/api/machines/<id>         # Specific resource
/api/machines/<id>/history # Sub-resource
```

**HTTP Methods:**
- `GET`: Retrieve data (read-only)
- `POST`: Create or trigger action
- `PUT`: Update resource
- `DELETE`: Remove resource

**In Laundriuno:**

```python
# Status endpoints (GET)
GET /api/machines                   # List all
GET /api/machines/1                 # Get one
GET /api/machines/available         # Filtered list

# Analytics endpoints (GET with parameters)
GET /api/statistics?days=7          # Query with filter
GET /api/best-times?days=7          # Derived data

# Control endpoints (POST)
POST /api/monitoring/start          # Trigger action
POST /api/monitoring/stop           # Trigger action
```

**Key Design Pattern:**

```python
@app.route('/api/resource', methods=['GET'])
def get_resource():
    """
    Standard REST endpoint pattern:
    1. Validate input parameters
    2. Query database
    3. Transform data for API
    4. Return JSON response
    5. Include appropriate status codes
    """
    # Parse parameters
    param = request.args.get('param', default=default_value, type=int)
    
    # Query data
    data = Service.get_data(param)
    
    # Transform for API
    response = [transform(item) for item in data]
    
    # Return JSON
    return jsonify(response), 200
```

### 6. Background Processing

**Concept:** IoT systems need continuous monitoring independent of user requests.

**Threading Pattern:**

```python
class MonitoringInterface:
    def start_monitoring(self, app):
        """
        Background processing pattern:
        1. Create separate thread
        2. Mark as daemon (exits with main)
        3. Pass application context
        4. Start non-blocking loop
        """
        self.running = True
        self.thread = threading.Thread(
            target=self.monitoring_loop,
            args=(app,)
        )
        self.thread.daemon = True
        self.thread.start()
    
    def monitoring_loop(self, app):
        """Continuous loop with application context"""
        while self.running:
            with app.app_context():
                self.process_data()
            time.sleep(interval)
```

**Why This Matters:**
- Web requests shouldn't block on sensor reads
- Monitoring continues even when no one is viewing dashboard
- Graceful shutdown when application stops

**Applicable to other projects:**
- Continuous temperature logging
- Periodic API polling
- Real-time alert checking
- Scheduled data cleanup

### 7. Data Analytics and Pattern Recognition

**Concept:** Historical data reveals patterns that enable predictions.

**Time-Series Analysis Pattern:**

```python
def analyze_pattern(self, days=7):
    """
    Pattern recognition in time-series data:
    1. Define time window
    2. Aggregate by relevant period
    3. Calculate statistics
    4. Identify patterns
    5. Make predictions
    """
    # Step 1: Define window
    start_date = datetime.now() - timedelta(days=days)
    
    # Step 2: Query data in window
    data = query_data(start_date)
    
    # Step 3: Aggregate by hour/day/week
    aggregated = {}
    for record in data:
        hour = record.timestamp.hour
        aggregated[hour] = aggregated.get(hour, 0) + 1
    
    # Step 4: Identify patterns
    # Find peaks, valleys, trends
    peak_hours = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
    low_hours = sorted(aggregated.items(), key=lambda x: x[1])
    
    # Step 5: Make recommendation
    return low_hours[:5]  # Return 5 least busy times
```

**Statistical Concepts Used:**

1. **Aggregation**: Count events per time period
2. **Averaging**: Calculate mean availability
3. **Ranking**: Sort by usage frequency
4. **Trend Analysis**: Identify busiest/quietest times

**Applicable to other projects:**
- Energy consumption patterns → when to run appliances
- Traffic patterns → best commute times
- Weather patterns → predict conditions
- User behavior → optimize service availability

---

## System Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────┐
│     Presentation Layer              │  (Web UI, REST API)
├─────────────────────────────────────┤
│     Application Logic Layer         │  (Analytics, State Management)
├─────────────────────────────────────┤
│     Data Access Layer              │  (SQLAlchemy Models)
├─────────────────────────────────────┤
│     Communication Layer            │  (MQTT/Serial Interface)
├─────────────────────────────────────┤
│     Hardware Layer                 │  (Arduino + Sensors)
└─────────────────────────────────────┘
```

**Benefits of Layering:**
1. **Separation of Concerns**: Each layer has one responsibility
2. **Testability**: Mock lower layers for testing
3. **Flexibility**: Swap implementations (MQTT ↔ Serial)
4. **Maintainability**: Changes isolated to relevant layer

### Event-Driven Pattern

**State Change Events:**

```python
# Event: Machine state changed
if is_running != machine.is_running:
    # Trigger event handlers
    self.on_state_change(machine, is_running)
```

**Event Handler Pattern:**

```python
def on_state_change(self, machine, new_state):
    """
    Event handler pattern:
    1. Update entity state
    2. Record event in database
    3. Trigger notifications
    4. Update analytics
    """
    # Update state
    machine.is_running = new_state
    machine.last_status_change = datetime.now()
    
    # Record event
    if new_state:
        self.start_session(machine)
    else:
        self.end_session(machine)
    
    # Could trigger notifications, webhooks, etc.
```

### Publisher-Subscriber Pattern (MQTT)

**Decouples data producers from consumers:**

```
Publisher (Arduino)     Broker (Mosquitto)     Subscriber (Flask)
      |                       |                         |
      |---(publish)---------->|                         |
      |                       |---(deliver)------------>|
      |                       |                         |
```

**Why This Pattern:**
- Multiple subscribers can receive same data
- Publishers don't need to know about subscribers
- Broker handles message queuing and reliability
- Scales better than point-to-point

---

## Implementation Walkthrough

### Step 1: Hardware Setup and Sensor Reading

**Learning: How to interface with physical sensors**

```cpp
// Arduino sketch structure
void setup() {
    // Initialize once
    Serial.begin(115200);
    mpu.begin();
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
}

void loop() {
    // Repeat forever
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Process data
    float ax = a.acceleration.x;
    float ay = a.acceleration.y;
    float az = a.acceleration.z;
    
    // Send data
    publishData(ax, ay, az);
    
    // Wait before next reading
    delay(100);
}
```

**Key Concepts:**
- **setup()**: One-time initialization
- **loop()**: Continuous execution
- **Sampling rate**: Balance between data quality and overhead
- **Data formatting**: Structure data before sending

### Step 2: Communication Layer

**Learning: Two approaches to data transmission**

#### Approach A: Serial (Simple)

```python
class SerialInterface:
    def read_sensor_data(self):
        """Simple text-based protocol"""
        if self.serial.in_waiting > 0:
            line = self.serial.readline().decode('utf-8')
            # Parse CSV: "machine_id,ax,ay,az"
            parts = line.split(',')
            return {
                'machine_id': int(parts[0]),
                'ax': float(parts[1]),
                'ay': float(parts[2]),
                'az': float(parts[3])
            }
```

**Protocol Design:**
- Simple CSV format
- Easy to debug (human readable)
- Low overhead
- No external dependencies

#### Approach B: MQTT (Scalable)

```python
class MQTTInterface:
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        self.process_sensor_data(data)
```

**Protocol Design:**
- JSON format (structured)
- Topic-based routing
- Quality of Service levels
- Network-based (wireless)

**Choosing the Right Protocol:**
```
Start with Serial → Prototype works → Switch to MQTT for production
```

### Step 3: Data Processing Pipeline

**Learning: How to transform raw sensor data into useful information**

```python
def process_sensor_data(self, data, app):
    """
    Data processing pipeline:
    Raw Data → Calculation → State Detection → Database → Events
    """
    with app.app_context():
        # Step 1: Extract raw data
        ax, ay, az = data['ax'], data['ay'], data['az']
        
        # Step 2: Calculate derived metrics
        vibration = math.sqrt(ax**2 + ay**2 + az**2)
        
        # Step 3: Store raw + derived
        reading = SensorReading(
            acceleration_x=ax,
            acceleration_y=ay,
            acceleration_z=az,
            vibration_magnitude=vibration
        )
        db.session.add(reading)
        
        # Step 4: Determine state
        is_running = vibration > self.threshold
        
        # Step 5: Detect state changes
        if is_running != machine.is_running:
            self.handle_state_change(machine, is_running)
        
        # Step 6: Commit to database
        db.session.commit()
```

**Pipeline Pattern Benefits:**
- Each step has clear input/output
- Easy to test individual steps
- Can add steps without changing others
- Can parallelize independent steps

### Step 4: Database Schema and ORM

**Learning: How to model IoT data with SQLAlchemy**

```python
class Machine(db.Model):
    """
    Entity model - represents a physical thing
    Primary key: id
    State fields: is_running, last_status_change
    Relationships: sessions (one-to-many)
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_running = db.Column(db.Boolean, default=False)
    last_status_change = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship: One machine has many sessions
    sessions = db.relationship('MachineSession', backref='machine')
```

**ORM Benefits:**
- Write Python instead of SQL
- Automatic schema creation
- Relationship management
- Query building

**Querying Patterns:**

```python
# Simple query
machine = Machine.query.get(1)

# Filtered query
available = Machine.query.filter_by(is_running=False).all()

# Complex query with joins
sessions = MachineSession.query\
    .filter(MachineSession.machine_id == 1)\
    .filter(MachineSession.start_time >= start_date)\
    .order_by(MachineSession.start_time.desc())\
    .all()
```

### Step 5: REST API Implementation

**Learning: How to build IoT data APIs with Flask**

```python
@app.route('/api/machines', methods=['GET'])
def get_machines():
    """
    REST endpoint pattern:
    1. Receive HTTP request
    2. Call service layer
    3. Transform data to JSON
    4. Return response
    """
    # Service layer handles business logic
    machines = AnalyticsService.get_machine_status()
    
    # jsonify() converts Python dict to JSON
    return jsonify(machines), 200
```

**URL Design Patterns:**

```
GET  /api/machines              # Collection
GET  /api/machines/1            # Resource
GET  /api/machines/available    # Filtered collection
GET  /api/machines/1/history    # Sub-resource

POST /api/monitoring/start      # Action (not REST purist, but practical)
```

**Query Parameters:**

```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    # Parse query string: /api/statistics?days=7
    days = request.args.get('days', default=7, type=int)
    stats = AnalyticsService.get_usage_statistics(days)
    return jsonify(stats)
```

### Step 6: Analytics and Recommendations

**Learning: How to extract insights from time-series data**

```python
def get_best_times(self, days=7):
    """
    Recommendation algorithm:
    1. Collect historical data
    2. Aggregate by time period
    3. Rank by metric
    4. Return top/bottom N
    """
    # Step 1: Get data in time window
    start_date = datetime.now() - timedelta(days=days)
    sessions = MachineSession.query.filter(
        MachineSession.start_time >= start_date
    ).all()
    
    # Step 2: Count sessions per hour
    hour_counts = {hour: 0 for hour in range(24)}
    for session in sessions:
        hour = session.start_time.hour
        hour_counts[hour] += 1
    
    # Step 3: Rank (ascending = least busy)
    ranked = sorted(hour_counts.items(), key=lambda x: x[1])
    
    # Step 4: Return top 5
    return ranked[:5]
```

**Algorithm Design Principles:**
- Start with simple algorithms
- Optimize based on real data
- Consider edge cases (no data, all busy, etc.)
- Make results actionable

### Step 7: Web Dashboard

**Learning: How to create real-time monitoring interfaces**

```javascript
// Frontend pattern: Fetch and Update
async function loadData() {
    // Fetch from multiple endpoints
    await Promise.all([
        loadMachines(),
        loadStatistics(),
        loadBestTimes()
    ]);
    
    // Update UI
    updateLastUpdateTime();
}

// Auto-refresh pattern
setInterval(loadData, 30000);  // Refresh every 30 seconds
```

**AJAX Pattern:**

```javascript
async function loadMachines() {
    try {
        const response = await fetch('/api/machines');
        const machines = await response.json();
        
        // Update DOM
        const container = document.getElementById('machines-grid');
        container.innerHTML = machines.map(renderMachine).join('');
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage();
    }
}
```

---

## Design Decisions and Trade-offs

### Decision 1: SQLite vs PostgreSQL

**Chosen: SQLite (with upgrade path)**

**Reasoning:**
- Simple setup (no server)
- File-based (easy backup)
- Sufficient for 1-10 machines
- Can migrate to PostgreSQL later

**When to Upgrade:**
- More than 10 machines
- Multiple concurrent users
- Need advanced features
- Remote database access

**Migration Path:**

```python
# Just change DATABASE_URL in .env
# From: sqlite:///laundriuno.db
# To: ******localhost/laundriuno
```

### Decision 2: Threading vs Async

**Chosen: Threading**

**Reasoning:**
- Simpler to understand
- Works with blocking I/O (serial)
- Sufficient for this use case
- Flask has good threading support

**Alternative: Async/Await**

```python
# Would use:
import asyncio
async def monitor():
    while True:
        await process_data()
        await asyncio.sleep(0.1)
```

**When to Use Async:**
- High concurrency needed
- Many I/O operations
- WebSocket connections
- Real-time push updates

### Decision 3: Polling vs Webhooks

**Chosen: Polling (dashboard refreshes)**

**Reasoning:**
- Simpler implementation
- Works with any HTTP server
- No persistent connections needed
- 30-second refresh acceptable

**Alternative: WebSockets**

```python
# Would use:
from flask_socketio import SocketIO
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    emit('status_update', get_current_status())
```

**When to Use WebSockets:**
- Need real-time updates (< 1 second)
- Many concurrent viewers
- Bidirectional communication needed

### Decision 4: Threshold vs Machine Learning

**Chosen: Simple threshold**

**Reasoning:**
- Easy to understand and tune
- Fast computation
- Works reliably
- No training data needed

**Alternative: ML Classification**

```python
# Would use:
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier()
model.fit(training_data, labels)
prediction = model.predict(sensor_reading)
```

**When to Use ML:**
- Complex patterns
- Multiple sensor types
- Different machine types
- Lots of training data available

---

## Reusable Code Patterns

### Pattern 1: Configuration Management

```python
# Load from environment with defaults
class Config:
    SETTING = os.environ.get('SETTING') or 'default_value'
    NUMERIC = int(os.environ.get('NUMERIC') or 123)
    BOOLEAN = os.environ.get('BOOLEAN', 'true').lower() == 'true'
```

**Why This Pattern:**
- Environment variables for production
- Defaults for development
- Type conversion in one place
- Easy to override in deployment

### Pattern 2: Database Session Management

```python
with app.app_context():
    # Database operations here
    db.session.add(record)
    db.session.commit()
```

**Why This Pattern:**
- Ensures proper Flask context
- Automatic cleanup
- Thread-safe
- Handles transactions

### Pattern 3: Error Handling in APIs

```python
@app.route('/api/resource/<int:id>')
def get_resource(id):
    try:
        resource = Service.get(id)
        if not resource:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(resource), 200
    except Exception as e:
        log_error(e)
        return jsonify({'error': 'Internal error'}), 500
```

**Why This Pattern:**
- Graceful error handling
- Appropriate status codes
- Consistent error format
- Logging for debugging

### Pattern 4: Retry Logic

```python
def connect_with_retry(self, max_attempts=5):
    """Retry connection with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            self.connect()
            return True
        except Exception as e:
            wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
            time.sleep(wait_time)
    return False
```

**Why This Pattern:**
- Handles transient failures
- Exponential backoff prevents overwhelming
- Gives up eventually
- Returns success/failure

### Pattern 5: Data Transformation Pipeline

```python
def transform(raw_data):
    """Pipeline: raw → validated → calculated → formatted"""
    validated = validate(raw_data)
    calculated = calculate_metrics(validated)
    formatted = format_for_api(calculated)
    return formatted
```

**Why This Pattern:**
- Each step testable
- Easy to add new transformations
- Clear data flow
- Reusable steps

---

## Extending for Your Own Projects

### Template: Generic IoT Monitoring System

```python
# 1. Sensor Interface
class SensorInterface:
    def read_data(self):
        """Override with your sensor logic"""
        pass
    
    def process_data(self, data):
        """Override with your processing logic"""
        pass

# 2. Database Model
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    # Add your device-specific fields

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    timestamp = db.Column(db.DateTime)
    # Add your sensor-specific fields

# 3. API Endpoint
@app.route('/api/devices')
def get_devices():
    devices = Device.query.all()
    return jsonify([device_to_dict(d) for d in devices])

# 4. Analytics
def analyze_data(days=7):
    # Your analysis logic
    pass
```

### Example Adaptations

#### 1. Temperature Monitoring System

**Changes Needed:**
- Replace IMU with temperature sensor (DHT22)
- Change threshold logic: `is_overheating = temp > MAX_TEMP`
- Update database: store temperature instead of acceleration
- Analytics: predict temperature trends

```python
class TemperatureReading(db.Model):
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)  # DHT22 provides both

def is_overheating(temperature, threshold=30.0):
    return temperature > threshold
```

#### 2. Parking Spot Monitor

**Changes Needed:**
- Replace IMU with ultrasonic sensor (HC-SR04)
- Change detection: `is_occupied = distance < THRESHOLD`
- Analytics: predict busy times for parking

```python
class ParkingSpot(db.Model):
    is_occupied = db.Column(db.Boolean)
    
class OccupancySession(db.Model):
    spot_id = db.Column(db.Integer)
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
```

#### 3. Air Quality Monitor

**Changes Needed:**
- Use MQ-135 or similar air quality sensor
- Multiple thresholds: good/moderate/poor
- Analytics: track trends, predict poor air quality times

```python
class AirQualityReading(db.Model):
    co2_ppm = db.Column(db.Integer)
    voc_level = db.Column(db.Integer)
    quality_category = db.Column(db.String(20))

def categorize_air_quality(co2_ppm):
    if co2_ppm < 400:
        return 'excellent'
    elif co2_ppm < 1000:
        return 'good'
    elif co2_ppm < 2000:
        return 'moderate'
    else:
        return 'poor'
```

### Checklist for Your Own Project

- [ ] Identify what physical phenomenon to measure
- [ ] Choose appropriate sensor(s)
- [ ] Decide on communication protocol (Serial vs MQTT vs WiFi)
- [ ] Design database schema (entities, events, readings)
- [ ] Implement sensor reading and data collection
- [ ] Add state detection/threshold logic
- [ ] Create REST API endpoints
- [ ] Build web dashboard
- [ ] Implement analytics and predictions
- [ ] Add documentation and setup guide
- [ ] Test with real hardware
- [ ] Deploy and monitor

---

## Additional Learning Resources

### Concepts to Study Further

1. **Time-Series Databases**: InfluxDB, TimescaleDB for large-scale sensor data
2. **Message Brokers**: RabbitMQ, Kafka for high-throughput systems
3. **Real-Time Processing**: Apache Flink, Spark Streaming
4. **Machine Learning**: scikit-learn, TensorFlow for predictive models
5. **Containerization**: Docker for easy deployment
6. **Monitoring**: Prometheus, Grafana for system monitoring

### Books and References

- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Flask Web Development" by Miguel Grinberg
- "Building Internet of Things with Python" by Charalampos Doukas
- MQTT specification: https://mqtt.org/
- Flask documentation: https://flask.palletsprojects.com/
- SQLAlchemy documentation: https://www.sqlalchemy.org/

### Practice Projects

1. **Smart Plant Watering**: Monitor soil moisture, auto-water
2. **Home Energy Monitor**: Track power usage, identify waste
3. **Security System**: Motion detection, camera integration
4. **Weather Station**: Temperature, humidity, pressure tracking
5. **Smart Garage**: Detect when door open/closed

---

## Conclusion

The Laundriuno project demonstrates core IoT concepts that apply to countless monitoring applications. By understanding the patterns and principles used here, you can build your own IoT projects that:

- Collect sensor data reliably
- Process and store data efficiently
- Provide useful APIs
- Deliver insights through analytics
- Present information clearly

**Key Takeaways:**

1. Start simple (Serial) and evolve (MQTT)
2. Layer your architecture for flexibility
3. Use established patterns and protocols
4. Document as you build
5. Test with real hardware early
6. Focus on reliability and error handling

**Next Steps:**

1. Build this project to understand the concepts
2. Modify it for your own use case
3. Experiment with different sensors
4. Try different communication protocols
5. Implement your own analytics
6. Share what you build!

Happy building! 🚀

---

*This guide is part of the Laundriuno project. For implementation details, see the other documentation files.*

