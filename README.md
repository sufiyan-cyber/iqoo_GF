# 🦇 BAT POD — Physical AI Companion for Smart Living

> **"AI should interpret. Rules should authorize. Hardware should verify."**

**BAT POD** is a voice-first, offline-resilient physical AI companion designed to bridge the gap between environmental awareness and safe physical intervention. 

Unlike traditional smart-home gadgets that only stream telemetry to cloud dashboards, BAT POD executes the complete closed loop:
```
SENSE ➔ UNDERSTAND ➔ DECIDE ➔ ACT ➔ CONFIRM
```
It reads real-time sensors, extracts structured intents using natural language processing, enforces deterministic safety constraints and RBAC permissions, drives physical actuators, and verifies physical state before reporting confirmation back to the user.

---

## 🌟 Key Features

- **Dual-Brain Hybrid Architecture**:
  - **Arduino Uno (Sensor Hub)**: Real-time sensor polling (Temperature, MQ Gas, Soil Moisture), servo valve control, pump relay, buzzer, and autonomous emergency fallback.
  - **ESP32 (Interaction Gateway)**: SSD1306 OLED display, MFRC522 RFID reader, capacitive touch button, and dual-UART bridge.
  - **Local AI Backend**: Local intent extraction, sensor context filtering, deterministic safety engine, RBAC authorization, and local SQLite audit logging.
- **Strictly Decoupled Safety**: The LLM *never* directly controls physical actuators. Critical decisions (e.g., gas leaks exceeding 300 PPM) trigger immediate deterministic safe-state actions (servo closes valve, alarm sounds) without conversational delay.
- **Human-in-the-Loop Approval**: Normal physical actions (e.g., watering plants) require explicit user confirmation via capacitive touch button or authorized voice approval.
- **Closed-Loop Hardware Verification**: The system verifies physical actuator state before reporting success to prevent false confirmations.
- **Role-Based Access Control (RBAC)**: Supports Guest, Worker, and Admin access levels via RFID card authentication.
- **100% Offline-First Resilience**: All critical safety rules, sensor evaluation, local actuation, and SQLite audit logging run entirely without an active internet connection.
- **Dual Mode (Hardware & Mock)**: Complete Hardware Abstraction Layer (HAL) allowing seamless toggling between physical microcontrollers and a fully interactive mock simulation.

---

## 🏗️ System Architecture

```text
                  ┌───────────────────────────────┐
                  │          BAT POD              │
                  │                               │
  Sensors ───────►│        Arduino Uno            │
  - Gas (MQ-2)    │        Sensor Hub             │
  - Temp (LM35)   │  (Autonomous Failsafe Logic)  │
  - Soil Moisture └──────────────┬────────────────┘
                                 │
                               UART (115200 Baud)
                                 │
                                 ▼
                  ┌───────────────────────────────┐
  Peripherals ───►│            ESP32              │
  - OLED Display  │      Interaction Gateway      │
  - RC522 RFID    │                               │
  - Touch Button  └──────────────┬────────────────┘
                                 │
                                USB Serial / Stream
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Local AI Backend        │
                  │                               │
                  │  • Context Retriever          │
                  │  • Intent Parser (LLM / Rule) │
                  │  • Deterministic Safety Rules │
                  │  • RBAC Authorization         │
                  │  • Action Manager & Verifier  │
                  │  • Multilingual TTS / STT     │
                  │  • SQLite Audit Database      │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Physical Actuators      │
                  │  • Servo (Simulated Valve)    │
                  │  • 5V Water Pump Relay        │
                  │  • Piezo Alarm Buzzer         │
                  └───────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (tested on Python 3.13)
- Optional for Hardware: Arduino Uno, ESP32, MQ-2 Gas sensor, LM35 Temp sensor, Capacitive soil sensor, SG90 Servo, SSD1306 OLED, RC522 RFID reader.

### 2. Setup Environment
```bash
# Clone repository
git clone <repo-url>
cd iqoo_hack

# Install dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env
```

### 3. Run in Simulation / Mock Mode
No hardware connected? You can run the complete interactive simulation immediately:

```bash
# Launch interactive terminal shell
python main.py --mode=mock --interactive
```

Inside the interactive shell:
```text
bat-pod> status
bat-pod> tap CARD_ADMIN_001
bat-pod> say Is the environment safe?
bat-pod> say Water the plant
bat-pod> approve
bat-pod> gas 350
bat-pod> say What happened?
bat-pod> history
```

### 4. Run Automated Golden Path MVP Demo
Run the complete 11-step PRD Golden Path test scenario with one command:
```bash
python main.py --demo
```

### 5. Run in Physical Hardware Mode
Connect your Arduino Uno and ESP32 via USB and run:
```bash
python main.py --mode=hardware --arduino-port=COM3 --esp32-port=COM4
```

---

## 🧪 Running Automated Tests

Run the test suite covering sensors, safety rules, RBAC authorization, hardware verification, AI intent extraction, and the Golden Path:

```bash
pytest -v
```

---

## 📊 RBAC Permissions Matrix

| Role | Default RFID UID | Environmental Monitoring | Normal Actions (`water_plant`) | Critical Actions (`close_valve`) | Emergency Override |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Guest** | Any unrecognized card | ✅ Allowed | ❌ Denied | ❌ Denied | ❌ Denied |
| **Worker** | `CARD_WORKER_002` | ✅ Allowed | ✅ With Approval | ❌ Denied | ❌ Denied |
| **Admin** | `CARD_ADMIN_001` | ✅ Allowed | ✅ With Approval | ✅ Allowed | ✅ Allowed |
| **System** | Internal Safety Daemon | ✅ Auto | ✅ Auto | ✅ Auto (Bypasses approval) | ✅ Auto |

---

## 📁 Repository Structure

```text
├── bat_pod/
│   ├── action/              # Safe execution & closed-loop hardware verification
│   ├── ai/                  # Intent parser, context retriever, response generator, voice
│   ├── audit/               # Persistent SQLite audit logger
│   ├── auth/                # RFID authentication & human-in-the-loop approval manager
│   ├── core/                # Domain models, event bus & HAL interfaces
│   ├── display/             # OLED / terminal screen renderer
│   ├── hal/                 # Mock and Real serial hardware adapters
│   ├── orchestrator/        # Central BatPodController coordinating the product loop
│   ├── safety/              # Deterministic safety rules & policy engine
│   └── config.py            # Typed settings
├── firmware/
│   ├── arduino_sensor_hub/  # Arduino Uno firmware (sensors + servo + autonomous failsafe)
│   └── esp32_gateway/       # ESP32 firmware (OLED + RFID + touch + bridge)
├── docs/
│   ├── HARDWARE_WIRING.md   # Pinout, schematic & level-shifting guide
│   ├── API.md               # Serial protocol, database schema & RBAC reference
│   └── DEMO_GUIDE.md        # Step-by-step Golden Path demonstration script
├── tests/                   # Comprehensive unit and integration test suite
├── main.py                  # CLI runner supporting --mode=mock and --mode=hardware
├── requirements.txt         # Python dependencies
└── .env.example             # Configuration template
```

---

## 📜 Audit Logging

Every critical event is recorded locally in `data/bat_pod.db` in SQLite:
```json
{
  "timestamp": "2026-10-05T20:35:21+00:00",
  "user": "SAFETY_DAEMON",
  "intent": "action:close_valve",
  "sensor_context": {
    "is_safe": false,
    "safety_summary": "EMERGENCY: GAS_LEAK detected!",
    "readings": {"gas": {"value": 350.0, "unit": "PPM", "status": "CRITICAL"}}
  },
  "requested_action": "close_valve",
  "authorization": "emergency_override",
  "execution_result": "success",
  "verification_result": "verified_success",
  "error": null
}
```

---

## 🛠️ Troubleshooting

- **`SerialException: could not open port`**: Ensure correct COM port in `.env` (or run with `--mode=mock`). Close any Arduino Serial Monitor before starting `main.py`.
- **`5V to 3.3V Logic Level Warning`**: When wiring Arduino TX to ESP32 RX, use a 1kΩ / 2kΩ voltage divider to prevent damage to the ESP32 input.
- **Offline / Cloud API Unavailable**: BAT POD is offline-first. If Sarvam or Ollama are unavailable, it seamlessly uses deterministic offline parsers and synthesizers.
