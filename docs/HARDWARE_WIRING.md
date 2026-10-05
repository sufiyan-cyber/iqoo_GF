# BAT POD — Hardware Wiring & Interconnection Guide

## 1. Dual-Brain System Overview

BAT POD employs a two-tier hardware architecture:
- **Arduino Uno (Sensor Hub)**: Real-time deterministic sensor polling (analog/digital), low-level actuator drive (PWM servo, relay, buzzer), and autonomous emergency failsafe logic.
- **ESP32 (Interaction Gateway)**: OLED visual display (SSD1306), RC522 RFID reader (SPI), capacitive touch button, and bridge to the Local AI Backend.

```
       [ MQ-2 Gas ]       [ LM35 / Temp ]     [ Capacitive Soil ]
            │                    │                     │
            └────────────┬───────┴─────────────────────┘
                         ▼
                ┌─────────────────┐
                │   Arduino Uno   │ ── Pin 9 ──► [ Servo Motor / Valve ]
                │   Sensor Hub    │ ── Pin 8 ──► [ 5V Pump Relay ]
                └────────┬────────┘ ── Pin 7 ──► [ Piezo Buzzer ]
                         │
                    UART │ (TX 1 -> RX2 16, RX 0 <- TX2 17)
                         │ (GND Common)
                         ▼
                ┌─────────────────┐ ── I2C (21, 22) ─► [ SSD1306 OLED ]
                │     ESP32       │ ── SPI (5,18,19,23) ► [ RC522 RFID ]
                │  Gateway / UI   │ ── GPIO 15 ──────► [ Touch Sensor ]
                └────────┬────────┘
                         │
                    USB  │ (115200 Baud)
                         ▼
               ┌──────────────────┐
               │ Local AI Backend │
               └──────────────────┘
```

---

## 2. Arduino Uno Pinout & Connections

| Component | Pin on Sensor | Arduino Uno Pin | Voltage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **LM35 / Temp** | VCC | 5V | 5V | Analog temperature sensor |
| | OUT | **A0** | 0-5V | 10mV / °C scale |
| | GND | GND | 0V | Common ground |
| **MQ-2 Gas** | VCC | 5V | 5V | MQ series flammable/smoke sensor |
| | AOUT | **A1** | 0-5V | Analog PPM voltage |
| | GND | GND | 0V | Common ground |
| **Soil Moisture** | VCC | 5V | 5V | Capacitive soil sensor |
| | AOUT | **A2** | 0-5V | Inverted analog curve |
| | GND | GND | 0V | Common ground |
| **Servo Motor** | Signal (Orange) | **Pin 9** | 5V PWM | Closed = 0°, Open = 90° |
| | VCC (Red) | 5V (Ext) | 5V | External 5V supply recommended |
| | GND (Brown) | GND | 0V | Common ground |
| **Pump Relay** | IN | **Pin 8** | 5V | Active HIGH relay trigger |
| | VCC | 5V | 5V | Relay coil VCC |
| | GND | GND | 0V | Common ground |
| **Piezo Buzzer** | (+) | **Pin 7** | 5V | Active buzzer for emergency alarm |
| | (-) | GND | 0V | Common ground |
| **ESP32 UART** | TX (Pin 1) | ESP32 RX2 (GPIO 16) | 5V to 3.3V | *Use 1k/2k resistor voltage divider!* |
| | RX (Pin 0) | ESP32 TX2 (GPIO 17) | 3.3V to 5V | Directly compatible |
| | GND | ESP32 GND | 0V | **Mandatory common ground** |

---

## 3. ESP32 Gateway Pinout & Connections

| Component | Pin on Module | ESP32 Pin | Voltage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **SSD1306 OLED** | VCC | 3.3V | 3.3V | 128x64 Monochrome I2C display |
| | GND | GND | 0V | Common ground |
| | SCL | **GPIO 22** | 3.3V | I2C Clock |
| | SDA | **GPIO 21** | 3.3V | I2C Data |
| **RC522 RFID** | 3.3V | 3.3V | 3.3V | **Do NOT connect to 5V** |
| | RST | **GPIO 4** | 3.3V | Reset pin |
| | GND | GND | 0V | Common ground |
| | MISO | **GPIO 19** | 3.3V | SPI Master In Slave Out |
| | MOSI | **GPIO 23** | 3.3V | SPI Master Out Slave In |
| | SCK | **GPIO 18** | 3.3V | SPI Clock |
| | SDA (SS) | **GPIO 5** | 3.3V | SPI Slave Select |
| **Touch Button** | VCC | 3.3V | 3.3V | TTP223 Capacitive touch sensor |
| | GND | GND | 0V | Common ground |
| | SIG | **GPIO 15** | 3.3V | Active LOW with pull-up |
| **Arduino UART** | RX2 | **GPIO 16** | 3.3V | Receives from Arduino TX |
| | TX2 | **GPIO 17** | 3.3V | Transmits to Arduino RX |

---

## 4. Power Architecture & Voltage Safety

> [!IMPORTANT]
> The ESP32 operates at **3.3V logic**, whereas the Arduino Uno operates at **5V logic**.
> - When connecting Arduino Uno TX (Pin 1) to ESP32 RX2 (GPIO 16), insert a simple 2-resistor voltage divider (1kΩ and 2kΩ) or a bi-directional logic level converter to protect the ESP32 input.
> - Ensure all grounds (Arduino GND, ESP32 GND, Sensor GND, External 5V Power Supply GND) are connected together into a **Single Common Ground**.
> - High-current actuators like the 5V water pump and SG90/MG996R servo must be powered by an external 5V 2A DC supply, NOT the Arduino 5V regulator pin, to prevent voltage sags or brownouts.
