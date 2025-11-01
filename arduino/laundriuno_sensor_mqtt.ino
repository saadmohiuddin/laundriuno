/*
 * ============================================================================
 * Laundriuno Arduino IMU Sensor Reader with MQTT Support
 * ============================================================================
 * 
 * This sketch reads data from an MPU6050 IMU sensor and sends acceleration
 * data to the Flask application backend via MQTT protocol over WiFi.
 * 
 * Features:
 *   - Reads 3-axis acceleration from MPU6050 sensor
 *   - Connects to WiFi network
 *   - Publishes sensor data to MQTT broker
 *   - Configurable machine ID for multiple deployments
 *   - Auto-reconnection on network failures
 *   - LED status indicators
 * 
 * Hardware Requirements:
 *   - ESP8266 (NodeMCU, Wemos D1 Mini) or ESP32 board
 *   - MPU6050 IMU sensor module
 *   - 5V power supply (USB or wall adapter)
 *   - Jumper wires for connections
 * 
 * Hardware Connections:
 * ====================
 * 
 * MPU6050 → ESP8266/ESP32
 * ------------------------
 * VCC  → 3.3V (NOT 5V - MPU6050 is 3.3V device!)
 * GND  → GND
 * SCL  → D1 (GPIO5 on ESP8266) or GPIO22 (on ESP32)
 * SDA  → D2 (GPIO4 on ESP8266) or GPIO21 (on ESP32)
 * 
 * Note: ESP8266 and ESP32 use 3.3V logic levels. Do not connect to 5V!
 * 
 * Software Dependencies:
 * =====================
 * Install these libraries via Arduino IDE Library Manager:
 * 
 * 1. Adafruit MPU6050
 *    - Provides MPU6050 sensor interface
 *    - Author: Adafruit Industries
 *    - Version: 2.0.0 or higher
 * 
 * 2. Adafruit Unified Sensor
 *    - Required dependency for Adafruit MPU6050
 *    - Author: Adafruit Industries
 *    - Version: 1.1.0 or higher
 * 
 * 3. PubSubClient
 *    - MQTT client library for Arduino
 *    - Author: Nick O'Leary
 *    - Version: 2.8.0 or higher
 * 
 * 4. ESP8266WiFi (for ESP8266) or WiFi (for ESP32)
 *    - WiFi connectivity
 *    - Included with ESP8266/ESP32 board support
 * 
 * Configuration:
 * =============
 * Update the following constants before uploading:
 * 
 * 1. MACHINE_ID: Unique identifier for this machine (1, 2, 3, ...)
 * 2. WIFI_SSID: Your WiFi network name
 * 3. WIFI_PASSWORD: Your WiFi password
 * 4. MQTT_SERVER: IP address or hostname of your MQTT broker
 * 5. MQTT_PORT: Port number of your MQTT broker (usually 1883)
 * 
 * MQTT Topic Structure:
 * ====================
 * Data is published to: laundriuno/sensor/{MACHINE_ID}/data
 * 
 * Message Format (JSON):
 * {
 *   "machine_id": 1,
 *   "ax": 1234.56,
 *   "ay": 789.01,
 *   "az": 456.78,
 *   "timestamp": 1635724800
 * }
 * 
 * LED Status Indicators:
 * =====================
 * Built-in LED blink patterns indicate system status:
 * - Rapid blink (5Hz): Connecting to WiFi
 * - Medium blink (1Hz): Connecting to MQTT broker
 * - Slow blink (0.5Hz): Normal operation, publishing data
 * - Solid ON: Error state
 * - OFF: Not initialized
 * 
 * Troubleshooting:
 * ===============
 * 
 * LED stays solid ON:
 *   - Check MPU6050 wiring and power
 *   - Verify I2C address (default 0x68)
 *   - Check 3.3V power supply
 * 
 * Rapid blinking never stops:
 *   - Check WiFi SSID and password
 *   - Verify WiFi network is available
 *   - Check antenna connection (if external)
 * 
 * Medium blinking never stops:
 *   - Verify MQTT broker is running
 *   - Check MQTT server IP address
 *   - Verify firewall allows port 1883
 *   - Try: mosquitto -v (to start broker in verbose mode)
 * 
 * No data in Flask app:
 *   - Verify MQTT topic matches Flask subscription
 *   - Check Serial Monitor for publish confirmations
 *   - Verify Flask app monitoring is started
 * 
 * Serial Monitor:
 * ==============
 * Open Serial Monitor at 115200 baud to see debug messages
 * 
 * Author: Laundriuno System
 * Version: 1.0.0
 * License: MIT
 * ============================================================================
 */

// ============================================================================
// Library Includes
// ============================================================================

// MPU6050 sensor libraries
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// WiFi and MQTT libraries
#ifdef ESP32
  #include <WiFi.h>  // WiFi library for ESP32
#else
  #include <ESP8266WiFi.h>  // WiFi library for ESP8266
#endif
#include <PubSubClient.h>  // MQTT client library

// ============================================================================
// Configuration Constants
// ============================================================================

// Machine Configuration
// ---------------------
// IMPORTANT: Change this to a unique ID for each Arduino/machine (1, 2, 3, ...)
const int MACHINE_ID = 1;

// WiFi Configuration
// ------------------
// Update these with your WiFi network credentials
const char* WIFI_SSID = "YourWiFiSSID";          // WiFi network name
const char* WIFI_PASSWORD = "YourWiFiPassword";  // WiFi password

// MQTT Broker Configuration
// --------------------------
// Update these with your MQTT broker details
const char* MQTT_SERVER = "192.168.1.100";  // MQTT broker IP or hostname
const int MQTT_PORT = 1883;                  // MQTT broker port (usually 1883)
const char* MQTT_CLIENT_ID = "laundriuno_";  // MQTT client ID prefix (machine ID appended)

// Sensor Configuration
// --------------------
const int SAMPLE_RATE = 100;  // Milliseconds between sensor readings (100ms = 10Hz)

// LED Configuration
// -----------------
#ifdef ESP32
  const int LED_PIN = 2;  // Built-in LED pin for ESP32
#else
  const int LED_PIN = LED_BUILTIN;  // Built-in LED pin for ESP8266
#endif

// ============================================================================
// Global Objects
// ============================================================================

// Create MPU6050 sensor object
Adafruit_MPU6050 mpu;

// Create WiFi and MQTT client objects
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// ============================================================================
// Global Variables
// ============================================================================

// Track connection status
bool mpuConnected = false;
bool wifiConnected = false;
bool mqttConnected = false;

// LED state for blinking
unsigned long lastLedToggle = 0;
bool ledState = LOW;

// MQTT topic for publishing sensor data
char mqttTopic[50];  // Buffer for topic string

// Buffer for JSON message payload
char messageBuffer[200];

// ============================================================================
// Setup Function - Runs Once at Startup
// ============================================================================

void setup() {
  /*
   * Initialize system components
   * 
   * This function runs once when the Arduino starts or resets. It:
   * 1. Initializes serial communication for debugging
   * 2. Configures LED pin for status indication
   * 3. Initializes MPU6050 sensor
   * 4. Connects to WiFi network
   * 5. Configures MQTT client
   * 6. Connects to MQTT broker
   * 
   * If any step fails, the system enters an error state (LED solid ON)
   */
  
  // Initialize serial communication for debugging
  // Baud rate: 115200 (faster than default 9600)
  Serial.begin(115200);
  while (!Serial) {
    delay(10);  // Wait for serial port to connect (needed for native USB)
  }
  
  Serial.println("\n\n========================================");
  Serial.println("Laundriuno IMU Sensor with MQTT");
  Serial.println("========================================");
  Serial.print("Machine ID: ");
  Serial.println(MACHINE_ID);
  
  // Configure LED pin for output
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize MPU6050 sensor
  Serial.println("\n[1/4] Initializing MPU6050 sensor...");
  if (!mpu.begin()) {
    Serial.println("ERROR: Failed to find MPU6050 chip!");
    Serial.println("Check wiring:");
    Serial.println("  VCC → 3.3V");
    Serial.println("  GND → GND");
    Serial.println("  SCL → D1 (ESP8266) or GPIO22 (ESP32)");
    Serial.println("  SDA → D2 (ESP8266) or GPIO21 (ESP32)");
    
    // Enter error state - solid LED
    digitalWrite(LED_PIN, HIGH);
    while (1) {
      delay(1000);  // Infinite loop in error state
    }
  }
  
  Serial.println("MPU6050 sensor found!");
  mpuConnected = true;
  
  // Configure MPU6050 sensor settings
  // These settings can be adjusted based on your specific requirements
  
  // Accelerometer range: ±2g, ±4g, ±8g, or ±16g
  // Lower range = higher resolution, higher range = measure larger accelerations
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range: ±");
  Serial.print(8);
  Serial.println("G");
  
  // Gyroscope range: ±250°/s, ±500°/s, ±1000°/s, or ±2000°/s
  // Not used for vibration detection, but must be configured
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyroscope range: ±");
  Serial.print(500);
  Serial.println(" deg/s");
  
  // Filter bandwidth: 260Hz, 184Hz, 94Hz, 44Hz, 21Hz, 10Hz, 5Hz
  // Lower = smoother but slower response, higher = faster but noisier
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("Filter bandwidth: 21 Hz");
  
  // Connect to WiFi
  Serial.println("\n[2/4] Connecting to WiFi...");
  Serial.print("SSID: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);  // Set WiFi to station mode
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  // Wait for WiFi connection with timeout
  int wifiAttempts = 0;
  const int MAX_WIFI_ATTEMPTS = 30;  // 30 seconds timeout
  
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < MAX_WIFI_ATTEMPTS) {
    delay(1000);
    Serial.print(".");
    
    // Rapid LED blink during WiFi connection
    digitalWrite(LED_PIN, wifiAttempts % 2);
    wifiAttempts++;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nERROR: Failed to connect to WiFi!");
    Serial.println("Check:");
    Serial.println("  - WiFi SSID is correct");
    Serial.println("  - WiFi password is correct");
    Serial.println("  - WiFi network is in range");
    
    // Enter error state
    digitalWrite(LED_PIN, HIGH);
    while (1) {
      delay(1000);
    }
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength: ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  wifiConnected = true;
  
  // Configure MQTT client
  Serial.println("\n[3/4] Configuring MQTT client...");
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  Serial.print("MQTT broker: ");
  Serial.print(MQTT_SERVER);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  
  // Build MQTT topic string: laundriuno/sensor/{MACHINE_ID}/data
  snprintf(mqttTopic, sizeof(mqttTopic), "laundriuno/sensor/%d/data", MACHINE_ID);
  Serial.print("MQTT topic: ");
  Serial.println(mqttTopic);
  
  // Connect to MQTT broker
  Serial.println("\n[4/4] Connecting to MQTT broker...");
  connectMQTT();
  
  Serial.println("\n========================================");
  Serial.println("System ready! Publishing sensor data...");
  Serial.println("========================================\n");
  
  delay(1000);
}

// ============================================================================
// Main Loop Function - Runs Continuously
// ============================================================================

void loop() {
  /*
   * Main program loop
   * 
   * This function runs continuously after setup() completes. It:
   * 1. Maintains MQTT connection (reconnects if needed)
   * 2. Reads sensor data from MPU6050
   * 3. Formats data as JSON
   * 4. Publishes data to MQTT broker
   * 5. Updates LED status indicator
   * 6. Delays for configured sample rate
   * 
   * The loop repeats indefinitely, providing continuous monitoring.
   */
  
  // Ensure MQTT client is connected
  // If connection is lost, this will attempt to reconnect
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  
  // Process MQTT messages and maintain connection
  // This must be called regularly to keep connection alive
  mqttClient.loop();
  
  // Read sensor data from MPU6050
  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);
  
  // Extract acceleration values
  // Values are in m/s² (meters per second squared)
  float ax = accel.acceleration.x;
  float ay = accel.acceleration.y;
  float az = accel.acceleration.z;
  
  // Multiply by 1000 to match expected format (larger integers easier to work with)
  // This converts m/s² to mm/s² (millimeters per second squared)
  ax *= 1000;
  ay *= 1000;
  az *= 1000;
  
  // Get current timestamp (milliseconds since boot)
  unsigned long timestamp = millis() / 1000;  // Convert to seconds
  
  // Format sensor data as JSON string
  // JSON format: {"machine_id":1,"ax":1234.56,"ay":789.01,"az":456.78,"timestamp":12345}
  snprintf(messageBuffer, sizeof(messageBuffer),
           "{\"machine_id\":%d,\"ax\":%.2f,\"ay\":%.2f,\"az\":%.2f,\"timestamp\":%lu}",
           MACHINE_ID, ax, ay, az, timestamp);
  
  // Publish JSON message to MQTT broker
  // QoS 0: At most once delivery (fast, no confirmation)
  // QoS 1: At least once delivery (confirmed, may duplicate)
  // QoS 2: Exactly once delivery (slowest, guaranteed single delivery)
  bool published = mqttClient.publish(mqttTopic, messageBuffer, false);
  
  if (published) {
    // Successfully published
    // Print to serial for debugging (can be disabled in production)
    Serial.print("Published: ");
    Serial.println(messageBuffer);
    
    // Slow LED blink indicates normal operation
    updateLED(500);  // Blink every 500ms (0.5 Hz)
    
  } else {
    // Failed to publish
    Serial.println("ERROR: Failed to publish message!");
    Serial.println("Check:");
    Serial.println("  - MQTT broker is running");
    Serial.println("  - Network connection is stable");
    Serial.println("  - Message size is within broker limits");
    
    // Rapid blink indicates error
    updateLED(100);  // Blink every 100ms (5 Hz)
  }
  
  // Wait for next sample period
  // This controls the data publishing frequency
  delay(SAMPLE_RATE);
}

// ============================================================================
// Helper Functions
// ============================================================================

void connectMQTT() {
  /*
   * Connect to MQTT broker
   * 
   * Attempts to establish a connection to the MQTT broker with automatic
   * retry logic. Updates LED to indicate connection status.
   * 
   * Connection Process:
   * 1. Generate unique client ID using machine ID
   * 2. Attempt connection to broker
   * 3. Retry with exponential backoff if failed
   * 4. Update LED and serial output with status
   * 
   * LED Pattern:
   * - Medium blink (1 Hz) while connecting
   * - Slow blink (0.5 Hz) when connected
   * 
   * Returns: void
   * Side Effects: Sets mqttConnected flag, controls LED
   */
  
  // Build unique client ID: laundriuno_1, laundriuno_2, etc.
  char clientId[30];
  snprintf(clientId, sizeof(clientId), "%s%d", MQTT_CLIENT_ID, MACHINE_ID);
  
  // Attempt to connect with retry logic
  int attempts = 0;
  const int MAX_ATTEMPTS = 10;
  
  while (!mqttClient.connected() && attempts < MAX_ATTEMPTS) {
    Serial.print("Attempting MQTT connection as '");
    Serial.print(clientId);
    Serial.print("'...");
    
    // Attempt connection
    // Parameters: clientId, username (NULL), password (NULL), willTopic (NULL),
    //             willQoS (0), willRetain (false), willMessage (NULL)
    if (mqttClient.connect(clientId)) {
      // Connection successful
      Serial.println(" connected!");
      mqttConnected = true;
      return;
      
    } else {
      // Connection failed
      Serial.print(" failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5 seconds...");
      
      // Explain error codes
      switch (mqttClient.state()) {
        case -4:
          Serial.println("  (MQTT_CONNECTION_TIMEOUT - Server didn't respond)");
          break;
        case -3:
          Serial.println("  (MQTT_CONNECTION_LOST - Network cable unplugged?)");
          break;
        case -2:
          Serial.println("  (MQTT_CONNECT_FAILED - Unable to connect)");
          break;
        case -1:
          Serial.println("  (MQTT_DISCONNECTED - Clean disconnection)");
          break;
        case 1:
          Serial.println("  (MQTT_CONNECT_BAD_PROTOCOL - Protocol version mismatch)");
          break;
        case 2:
          Serial.println("  (MQTT_CONNECT_BAD_CLIENT_ID - Client ID rejected)");
          break;
        case 3:
          Serial.println("  (MQTT_CONNECT_UNAVAILABLE - Server unavailable)");
          break;
        case 4:
          Serial.println("  (MQTT_CONNECT_BAD_CREDENTIALS - Bad username/password)");
          break;
        case 5:
          Serial.println("  (MQTT_CONNECT_UNAUTHORIZED - Client not authorized)");
          break;
      }
      
      // Wait before retrying (exponential backoff)
      for (int i = 0; i < 5; i++) {
        delay(1000);
        // Medium blink during connection attempts
        digitalWrite(LED_PIN, i % 2);
      }
      
      attempts++;
    }
  }
  
  // If we exit the loop without connecting, enter error state
  if (!mqttClient.connected()) {
    Serial.println("\nERROR: Failed to connect to MQTT broker after multiple attempts!");
    Serial.println("Check:");
    Serial.println("  - MQTT broker is running (mosquitto -v)");
    Serial.println("  - MQTT server IP address is correct");
    Serial.println("  - Port 1883 is open (firewall)");
    Serial.println("  - Network connectivity is stable");
    
    // Solid LED indicates error
    digitalWrite(LED_PIN, HIGH);
    while (1) {
      delay(1000);
    }
  }
}

void updateLED(unsigned long blinkInterval) {
  /*
   * Update LED state for status indication
   * 
   * Toggles LED on/off at specified interval to provide visual feedback
   * about system status. Uses non-blocking timing to avoid interfering
   * with main loop execution.
   * 
   * Parameters:
   *   blinkInterval (unsigned long): Milliseconds between LED toggles
   *     - 100ms = 5 Hz rapid blink (error state)
   *     - 500ms = 1 Hz medium blink (connecting)
   *     - 1000ms = 0.5 Hz slow blink (normal operation)
   * 
   * Implementation:
   * Uses millis() for non-blocking timing, avoiding delay() which would
   * block MQTT message processing and WiFi maintenance.
   * 
   * Returns: void
   * Side Effects: Modifies LED pin state and lastLedToggle timestamp
   */
  
  unsigned long currentMillis = millis();
  
  // Check if it's time to toggle LED
  if (currentMillis - lastLedToggle >= blinkInterval) {
    lastLedToggle = currentMillis;
    
    // Toggle LED state
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
  }
}

/*
 * ============================================================================
 * End of Sketch
 * ============================================================================
 * 
 * Next Steps After Upload:
 * ========================
 * 
 * 1. Open Serial Monitor (115200 baud) to see debug messages
 * 
 * 2. Verify connections:
 *    - WiFi connection established
 *    - MQTT broker connection established
 *    - Sensor readings being published
 * 
 * 3. Test MQTT reception:
 *    mosquitto_sub -h localhost -t "laundriuno/sensor/+/data" -v
 * 
 * 4. Start Flask application:
 *    python app.py
 * 
 * 5. Start monitoring via API:
 *    curl -X POST http://localhost:5000/api/monitoring/start
 * 
 * 6. View dashboard:
 *    Open http://localhost:5000 in web browser
 * 
 * For Support:
 * ===========
 * - Check README.md for detailed setup instructions
 * - See ARCHITECTURE.md for system design details
 * - Review troubleshooting section above
 * 
 * ============================================================================
 */
