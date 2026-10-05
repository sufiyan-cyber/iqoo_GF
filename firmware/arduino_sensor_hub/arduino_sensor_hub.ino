/*
 * BAT POD — Arduino Uno Sensor Hub Firmware
 * 
 * Hardware Responsibilities:
 * - Periodically poll Temperature (A0), Gas (A1), and Soil Moisture (A2)
 * - Drive Servo Motor (Pin 9) for physical valve actuation
 * - Drive Water Pump Relay (Pin 8)
 * - Drive Buzzer Alarm (Pin 7)
 * - Autonomous Hardware Safety Fallback:
 *   If gas level exceeds HARDWARE_CRITICAL_GAS, immediately close valve and activate buzzer,
 *   even if communication with ESP32 / Host is severed!
 * - Send newline-delimited JSON telemetry over UART (115200 baud)
 * - Receive and execute structured actuator commands
 */

#include <Servo.h>

// Pin Definitions
const int PIN_TEMP_SENSOR = A0;
const int PIN_GAS_SENSOR  = A1;
const int PIN_SOIL_SENSOR = A2;
const int PIN_SERVO       = 9;
const int PIN_PUMP_RELAY  = 8;
const int PIN_BUZZER      = 7;

// Safety & Threshold Constants
const float HARDWARE_CRITICAL_GAS = 300.0; // PPM
const unsigned long POLL_INTERVAL_MS = 1000;

// Actuator & State
Servo valveServo;
int currentServoAngle = 90; // 90° = Open / Normal, 0° = Closed
bool pumpActive = false;
bool buzzerActive = false;
unsigned long lastPollTime = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_TEMP_SENSOR, INPUT);
  pinMode(PIN_GAS_SENSOR, INPUT);
  pinMode(PIN_SOIL_SENSOR, INPUT);
  
  pinMode(PIN_PUMP_RELAY, OUTPUT);
  digitalWrite(PIN_PUMP_RELAY, LOW);
  
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  
  valveServo.attach(PIN_SERVO);
  valveServo.write(currentServoAngle);
}

// Convert analog pin read to temperature in Celsius (LM35: 10mV/°C)
float readTemperature() {
  int raw = analogRead(PIN_TEMP_SENSOR);
  float voltage = (raw * 5.0) / 1024.0;
  return voltage * 100.0; // 10mV per degree C
}

// Convert analog pin read to approximate Gas PPM
float readGasPPM() {
  int raw = analogRead(PIN_GAS_SENSOR);
  // MQ curve approximation: raw 0-1023 mapped to 0-1000 PPM
  return (raw / 1023.0) * 1000.0;
}

// Convert analog pin read to Soil Moisture percentage
float readSoilMoisturePct() {
  int raw = analogRead(PIN_SOIL_SENSOR);
  // Inverted: higher moisture = lower resistance/voltage
  float pct = (1.0 - (raw / 1023.0)) * 100.0;
  if (pct < 0.0) pct = 0.0;
  if (pct > 100.0) pct = 100.0;
  return pct;
}

void processIncomingCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  // Simple string-based JSON command parsing on AVR
  if (line.indexOf("\"SET_SERVO\"") >= 0) {
    int angleIdx = line.indexOf("\"angle\":");
    if (angleIdx >= 0) {
      int endIdx = line.indexOf("}", angleIdx);
      int targetAngle = line.substring(angleIdx + 8, endIdx).toInt();
      targetAngle = constrain(targetAngle, 0, 180);
      valveServo.write(targetAngle);
      currentServoAngle = targetAngle;
      
      // Send verification ACK
      Serial.print("{\"type\":\"ack\",\"target\":\"servo\",\"state\":\"");
      Serial.print(currentServoAngle);
      Serial.println("_DEG\",\"verified\":true}");
    }
  } else if (line.indexOf("\"SET_PUMP\"") >= 0) {
    int stateIdx = line.indexOf("\"state\":");
    if (stateIdx >= 0) {
      int state = line.substring(stateIdx + 8, stateIdx + 9).toInt();
      pumpActive = (state == 1);
      digitalWrite(PIN_PUMP_RELAY, pumpActive ? HIGH : LOW);
      
      Serial.print("{\"type\":\"ack\",\"target\":\"pump\",\"state\":\"");
      Serial.print(pumpActive ? "RUNNING" : "STOPPED");
      Serial.println("\",\"verified\":true}");
    }
  } else if (line.indexOf("\"SET_ALARM\"") >= 0) {
    int stateIdx = line.indexOf("\"state\":");
    if (stateIdx >= 0) {
      int state = line.substring(stateIdx + 8, stateIdx + 9).toInt();
      buzzerActive = (state == 1);
      digitalWrite(PIN_BUZZER, buzzerActive ? HIGH : LOW);
      
      Serial.print("{\"type\":\"ack\",\"target\":\"alarm\",\"state\":\"");
      Serial.print(buzzerActive ? "ON" : "OFF");
      Serial.println("\",\"verified\":true}");
    }
  }
}

void loop() {
  // Check for incoming serial commands from ESP32/Host
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    processIncomingCommand(incoming);
  }

  unsigned long currentMillis = millis();
  if (currentMillis - lastPollTime >= POLL_INTERVAL_MS) {
    lastPollTime = currentMillis;

    float temp = readTemperature();
    float gas = readGasPPM();
    float soil = readSoilMoisturePct();

    // HARDWARE DETERMINISTIC SAFETY INTERVENTION
    // If gas exceeds critical threshold, close valve immediately
    if (gas >= HARDWARE_CRITICAL_GAS) {
      if (currentServoAngle != 0) {
        valveServo.write(0);
        currentServoAngle = 0;
      }
      digitalWrite(PIN_BUZZER, HIGH);
      buzzerActive = true;
    }

    // Emit telemetry packet
    Serial.print("{\"type\":\"telemetry\",");
    Serial.print("\"temp\":");
    Serial.print(temp, 1);
    Serial.print(",\"gas\":");
    Serial.print(gas, 1);
    Serial.print(",\"soil\":");
    Serial.print(soil, 1);
    Serial.print(",\"servo_angle\":");
    Serial.print(currentServoAngle);
    Serial.println("}");
  }
}
