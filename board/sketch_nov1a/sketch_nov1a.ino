#include <Arduino.h>
#include <Wire.h> // Used for the Wire1 object
#include <Adafruit_ICM20649.h>
#include <Adafruit_Sensor.h>
#include <WiFiS3.h>
#include <PubSubClient.h>

// --- NEW: Unique Device Configuration ---
// !!! CHANGE THIS FOR EACH NODE !!!
const char* deviceName = "live_node_1"; // e.g., "washer_1", "dryer_1", "washer_upstairs"

// --- WiFi & MQTT Configuration ---
char ssid[] = "1033";         // Your network SSID (name)
char pass[] = "AYu13297";     // Your network password
const char* mqttServer = "192.168.137.208"; // IP or hostname of your broker
const int mqttPort = 1883;

// --- ADD THESE TWO LINES ---
const char* mqttUser = "ujju"; // The HA user you created (e.g., "mqtt-devices")
const char* mqttPass = "Oli*16620"; // The password for that user

// --- MODIFIED: Topic variables are now Strings, built in setup() ---
String machineTopic;
String doorTopic;

// Initialize the WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

/* Adafruit ICM20649 object */
Adafruit_ICM20649 icm;
/* Sensor event objects to store data */
sensors_event_t accel, gyro, temp;

// --- Tunable Thresholds ---
const float ACCEL_VIBRATION_THRESHOLD = 0.25;
const float ACCEL_DOOR_CLOSED_THRESHOLD = 8.0;
const long MACHINE_OFF_DELAY = 500;

// --- Calibration Variable ---
float calibratedGravity = 9.81;

// --- Variables for Moving Average ---
const int NUM_READINGS = 10;
float readings[NUM_READINGS];
int readIndex = 0;
float total = 0;
float averageAccelVibration = 0;

// --- Global state variables ---
bool isMachineOn = false;
bool isDoorOpen = true;
unsigned long timeMachineWentQuiet = 0;

// --- State Tracking for MQTT ---
bool lastMachineState = true;
bool lastDoorState = false;
unsigned long lastMqttPublishTime = 0;
const long mqttPublishInterval = 3000;
unsigned long lastMqttReconnectAttempt = 0;

// --- WiFi Setup Function (Unchanged) ---
void setupWifi() {
  delay(10);
  Serial.print("\nConnecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnectMqtt() {
  Serial.print("Attempting MQTT connection...");
  
  // Create a unique client ID based on deviceName
  String clientID = "r4-client-" + String(deviceName);
  Serial.print(" as ");
  Serial.println(clientID);

  // --- THIS IS THE MODIFIED LINE ---
  // We now pass the clientID, mqttUser, and mqttPass
  if (mqttClient.connect(clientID.c_str(), mqttUser, mqttPass)) {
    Serial.println("MQTT connected!");
    // On reconnect, force a re-publish of the current state
    lastMachineState = !isMachineOn;
    lastDoorState = !isDoorOpen;
  } else {
    Serial.print("failed, rc=");
    Serial.print(mqttClient.state()); // This will now stop printing '5'
    Serial.println(" try again in 5 seconds");
  }
}

// --- MODIFIED: MQTT Publish Function ---
void publishState() {
  unsigned long now = millis();
  bool stateChanged = false;

  if (isMachineOn != lastMachineState) stateChanged = true;
  if (isDoorOpen != lastDoorState) stateChanged = true;

  if (stateChanged || (now - lastMqttPublishTime > mqttPublishInterval)) {
    const char* machinePayload = isMachineOn ? "ON" : "OFF";
    const char* doorPayload = isDoorOpen ? "Open" : "Closed";

    Serial.print("Publishing MQTT - Machine: ");
    Serial.print(machinePayload);
    Serial.print(" | Door: ");
    Serial.println(doorPayload);

    // --- MODIFIED: Use .c_str() for String topics ---
    mqttClient.publish(machineTopic.c_str(), machinePayload, true);
    mqttClient.publish(doorTopic.c_str(), doorPayload, true);

    lastMachineState = isMachineOn;
    lastDoorState = isDoorOpen;
    lastMqttPublishTime = now;
  }
}


void setup() {
  Serial.begin(115200);
  while (!Serial) {}
  delay(1000);

  Serial.println("Washing Machine Monitor Initializing...");
  
  // --- Sensor Setup (Your existing code) ---
  if (!icm.begin_I2C(0x68, &Wire1)) {
    Serial.println("Error initializing ICM-20649 on Wire1 (Qwiic)");
    while (1) {}
  }
  Serial.println("ICM-20649 Found!");
  icm.setAccelRange(ICM20649_ACCEL_RANGE_4_G);
  icm.setGyroRange(ICM20649_GYRO_RANGE_500_DPS);

  // --- Calibration (Your existing code) ---
  Serial.println("Calibrating accelerometer for 2 seconds... Keep sensor still!");
  unsigned long calibrationStartTime = millis();
  float totalMag = 0;
  int sampleCount = 0;
  while (millis() - calibrationStartTime < 2000) {
    icm.getEvent(&accel, &gyro, &temp);
    float ax = accel.acceleration.x;
    float ay = accel.acceleration.y;
    float az = accel.acceleration.z;
    totalMag += sqrt(ax * ax + ay * ay + az * az);
    sampleCount++;
    delay(5);
  }
  calibratedGravity = totalMag / sampleCount;
  Serial.print("Calibration complete. Baseline gravity: ");
  Serial.println(calibratedGravity);

  // Initialize moving average
  for (int i = 0; i < NUM_READINGS; i++) {
    readings[i] = 0;
  }

  // --- NEW: Build unique topic strings ---
  // Using a hierarchical structure: home/[location]/[device]/[measurement]
  String baseTopic = "home/laundry/" + String(deviceName);
  machineTopic = baseTopic + "/machine_state";
  doorTopic = baseTopic + "/door_state";
  // --- End NEW Section ---

  // Connect to WiFi and MQTT
  setupWifi();
  mqttClient.setServer(mqttServer, mqttPort);

  Serial.println("Monitor Initialized and Connected.");
  Serial.print("  Device Name: "); Serial.println(deviceName);
  Serial.print("  Machine Topic: "); Serial.println(machineTopic);
  Serial.print("  Door Topic: "); Serial.println(doorTopic);
}

void loop() {
  // --- Handle MQTT Connection ---
  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastMqttReconnectAttempt > 500) {
      lastMqttReconnectAttempt = now;
      reconnectMqtt();
    }
  }
  mqttClient.loop(); 

  // --- Sensor Logic (Your existing code) ---
  icm.getEvent(&accel, &gyro, &temp);
  float ax = accel.acceleration.x;
  float ay = accel.acceleration.y;
  float az = accel.acceleration.z;
  float currentAccelMag = sqrt(ax * ax + ay * ay + az * az);
  float currentVibration = abs(currentAccelMag - calibratedGravity); 

  total = total - readings[readIndex];
  readings[readIndex] = currentVibration;
  total = total + readings[readIndex];
  readIndex = (readIndex + 1) % NUM_READINGS;
  averageAccelVibration = total / NUM_READINGS;

  if (abs(ay) < ACCEL_DOOR_CLOSED_THRESHOLD) {
    isDoorOpen = false; // "Closed"
  } else {
    isDoorOpen = true; // "Open"
  }

  if (isDoorOpen) {
    isMachineOn = false;
    timeMachineWentQuiet = 0; 
  }
  else {
    if (averageAccelVibration > ACCEL_VIBRATION_THRESHOLD) {
      isMachineOn = true;
      timeMachineWentQuiet = 0; 
    }
    else {
      if (isMachineOn) { 
        if (timeMachineWentQuiet == 0) {
          timeMachineWentQuiet = millis();
        } else if (millis() - timeMachineWentQuiet > MACHINE_OFF_DELAY) {
          isMachineOn = false; 
          timeMachineWentQuiet = 0; 
        }
      }
    }
  }
  
  // --- Serial Report (Your existing code) ---
  // Serial.print("Device: "); Serial.print(deviceName);
  // Serial.print(" | Machine: ");
  // Serial.print(isMachineOn ? "ON  " : "OFF ");
  // Serial.print(" | Door: ");
  // Serial.println(isDoorOpen ? "Open" : "Closed");

  // --- Publish to MQTT ---
  publishState();

  delay(20); 
}