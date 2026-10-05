/*
 * BAT POD — ESP32 Gateway & Interaction Firmware
 * 
 * Hardware Responsibilities:
 * - Bridge UART communication with Arduino Uno (HardwareSerial Serial2: RX=16, TX=17)
 * - Drive SSD1306 OLED Display (I2C: SDA=21, SCL=22) showing Normal, Approval, and Emergency screens
 * - Read MFRC522 RFID Cards (SPI: SS=5, RST=4, MOSI=23, MISO=19, SCK=18)
 * - Monitor Capacitive Touch Button (GPIO 4)
 * - Relay telemetry, RFID events, and touch triggers to Local AI Backend over Serial0 (115200 baud)
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <MFRC522.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// RFID RC522 Pins
#define RST_PIN 4
#define SS_PIN  5
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Touch Pin
#define TOUCH_PIN 15

// HardwareSerial to Arduino Uno
HardwareSerial ArduinoSerial(2); // UART2: RX2=16, TX2=17

// Current Display State
String currentScreenState = "NORMAL";
String displayTemp = "--";
String displayGas = "SAFE";
String displaySoil = "--";
String displayStatus = "Everything OK";
String actionTitle = "";
String actionDetail = "";

void setup() {
  Serial.begin(115200);           // USB connection to Local AI Backend
  ArduinoSerial.begin(115200, SERIAL_8N1, 16, 17); // UART link to Arduino Uno

  // Init SPI and RFID
  SPI.begin();
  mfrc522.PCD_Init();

  // Init Touch Pin
  pinMode(TOUCH_PIN, INPUT_PULLUP);

  // Init OLED Display
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(20, 20);
    display.println("BAT POD STARTING...");
    display.display();
  }
}

void renderScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  if (currentScreenState == "NORMAL") {
    display.setCursor(40, 2);
    display.println("BAT POD");
    display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
    
    display.setCursor(0, 16);
    display.print("TEMP: "); display.println(displayTemp);
    display.print("GAS:  "); display.println(displayGas);
    display.print("SOIL: "); display.println(displaySoil);
    
    display.setCursor(0, 48);
    display.println("STATUS:");
    display.setCursor(0, 56);
    display.println(displayStatus);

  } else if (currentScreenState == "APPROVAL") {
    display.setCursor(20, 2);
    display.println("ACTION REQUEST");
    display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
    
    display.setCursor(0, 18);
    display.println(actionTitle);
    display.setCursor(0, 28);
    display.println(actionDetail);
    
    display.setCursor(0, 52);
    display.println("[TOUCH: APPROVE]");

  } else if (currentScreenState == "EMERGENCY") {
    display.setCursor(25, 2);
    display.println("! WARNING !");
    display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
    
    display.setCursor(0, 20);
    display.println("GAS DETECTED");
    display.setCursor(0, 32);
    display.println("Closing valve...");
    display.setCursor(0, 48);
    display.println("ALARM ACTIVE");
  }

  display.display();
}

void checkRFID() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }
  
  String uidStr = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidStr.toUpperCase();
  mfrc522.PICC_HaltA();

  // Forward RFID event to Backend
  Serial.print("{\"type\":\"rfid_event\",\"uid\":\"");
  Serial.print(uidStr);
  Serial.println("\"}");
}

void checkTouch() {
  static bool lastState = HIGH;
  bool currentState = digitalRead(TOUCH_PIN);
  if (currentState == LOW && lastState == HIGH) {
    // Touch pressed
    Serial.println("{\"type\":\"touch_event\",\"pressed\":true}");
    delay(200); // Debounce
  }
  lastState = currentState;
}

void loop() {
  // Check hardware inputs
  checkRFID();
  checkTouch();

  // Forward incoming data from Arduino Uno to Local AI Backend
  while (ArduinoSerial.available()) {
    String telemetryLine = ArduinoSerial.readStringUntil('\n');
    telemetryLine.trim();
    if (telemetryLine.length() > 0) {
      Serial.println(telemetryLine);
    }
  }

  // Handle incoming commands/display updates from Local AI Backend
  while (Serial.available()) {
    String hostLine = Serial.readStringUntil('\n');
    hostLine.trim();
    if (hostLine.length() == 0) continue;

    if (hostLine.indexOf("\"type\":\"display\"") >= 0) {
      if (hostLine.indexOf("\"state\":\"normal\"") >= 0) {
        currentScreenState = "NORMAL";
      } else if (hostLine.indexOf("\"state\":\"approval\"") >= 0) {
        currentScreenState = "APPROVAL";
      } else if (hostLine.indexOf("\"state\":\"emergency\"") >= 0) {
        currentScreenState = "EMERGENCY";
      }
      renderScreen();
    } else {
      // Forward actuator commands down to Arduino Uno
      ArduinoSerial.println(hostLine);
    }
  }
}
