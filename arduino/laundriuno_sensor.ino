/*
 * Laundriuno Arduino IMU Sensor Reader
 * 
 * This sketch reads data from an MPU6050 IMU sensor and sends
 * acceleration data to the Flask application via serial communication.
 * 
 * Hardware Setup:
 * - Arduino board (Uno, Nano, or similar)
 * - MPU6050 IMU sensor
 * - Connect MPU6050 VCC to Arduino 5V
 * - Connect MPU6050 GND to Arduino GND
 * - Connect MPU6050 SCL to Arduino A5 (SCL)
 * - Connect MPU6050 SDA to Arduino A4 (SDA)
 * 
 * Required Library:
 * - Adafruit MPU6050 (Install via Arduino Library Manager)
 * - Adafruit Unified Sensor (Install via Arduino Library Manager)
 */

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;

// Configuration
const int MACHINE_ID = 1;  // Change this for each Arduino/machine
const int SAMPLE_RATE = 100; // ms between readings
const int BAUD_RATE = 9600;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  
  // Wait for serial port to connect
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("Laundriuno IMU Sensor Starting...");
  
  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  
  Serial.println("MPU6050 Found!");
  
  // Configure MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  Serial.println("MPU6050 Configured");
  Serial.println("Sending data to Flask application...");
  
  delay(100);
}

void loop() {
  // Get sensor readings
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Send data in CSV format: machine_id,ax,ay,az
  // Multiply by 1000 to convert m/s² to approximate integer values
  Serial.print(MACHINE_ID);
  Serial.print(",");
  Serial.print(a.acceleration.x * 1000);
  Serial.print(",");
  Serial.print(a.acceleration.y * 1000);
  Serial.print(",");
  Serial.println(a.acceleration.z * 1000);
  
  delay(SAMPLE_RATE);
}
