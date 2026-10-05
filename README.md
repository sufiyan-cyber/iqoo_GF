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

## 🚀 Steps to Reproduce & Run

Follow these step-by-step instructions to set up and reproduce the BAT POD system from scratch on any machine (Windows, Linux, or macOS).

### 1. Clone the Repository
```bash
git clone https://github.com/sufiyan-cyber/iqoo_GF.git
cd iqoo_GF
```

### 2. Set Up Python Virtual Environment
We recommend Python 3.10, 3.11, 3.12, or 3.13:

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the environment template:
```bash
# On Windows PowerShell
Copy-Item .env.example .env

# On Linux / macOS
cp .env.example .env
```
*(Default settings are pre-configured to run immediately in Simulation/Mock mode).*

---

### 5. Run the Test Suite (Verification)
Execute the complete test suite across sensors, safety rules, RBAC authorization, closed-loop verification, AI intent extraction, and the Web API:
```bash
python -m pytest -v
```
**Expected Output:**
```text
============================= 39 passed in 0.82s ==============================
```

---

### 6. Run the Organic / Natural Web Companion UI
BAT POD features a tactile **Organic / Natural (Wabi-Sabi)** Web Companion UI built with:
- **Earth-drawn color palette**: Rice Paper (`#FDFCF8`), Moss Green (`#5D7052`), Terracotta (`#C18C5D`), Sand (`#E6DCCD`), and Raw Timber (`#DED8CF`).
- **Warm Typography**: *Fraunces* soft variable serif headings and *Nunito* rounded sans-serif body.
- **Physical Texture**: Global paper grain/noise overlay with multiply blend mode.
- **Organic Geometry**: Amorphous blob backgrounds and asymmetric cards with varied border radii.
- **Live Real-time Telemetry & Actuation**: Monitor live sensor gauges, tap simulated RFID cards, issue voice commands, trigger gas leak tests, and approve pending actions.

**Launch the Web Server:**
```bash
python main.py --web --web-port=8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

*(You can also directly double-click or open `web/index.html` in any modern web browser to interact with the client-side simulator).*

---

### 7. Run the Automated MVP Golden Path Demo
Run the complete 11-step end-to-end scenario specified in `BAT_POD_PRD.md`:
```bash
python main.py --demo
```
This automatically demonstrates:
1. **RFID Tap**: Identifies Admin card user (*Bruce Wayne*).
2. **Safety Query**: *"BAT POD, is the environment safe?"* -> Evaluates temperature, gas, and soil moisture context.
3. **Action Request**: *"Water the plant."* -> Generates human confirmation request with soil context.
4. **Approval**: User approves -> Pump/servo triggers with physical verification (`VERIFIED_SUCCESS`).
5. **Emergency Simulation**: Gas sensor spikes to 350 PPM (> 300 PPM threshold) -> Autonomous safe-state closure of valve, alarm ON, and emergency OLED display.
6. **Explanation Query**: *"What happened?"* -> Retrieves SQLite audit log and explains the hazard.
7. **Audit Log Inspection**: Outputs the SQLite records table.

---

### 8. Run the Interactive Simulation Shell
Interact live with BAT POD via the terminal without requiring physical microcontrollers:
```bash
python main.py --mode=mock --interactive
```

**Interactive Shell Commands:**
```text
bat-pod> status                      # View current sensors, OLED display, and active user
bat-pod> tap CARD_ADMIN_001          # Tap Admin RFID card
bat-pod> tap CARD_WORKER_002         # Tap Worker RFID card
bat-pod> say Is the environment safe?# Ask environmental status
bat-pod> say Water the plant         # Issue action command
bat-pod> approve                     # Confirm pending action
bat-pod> gas 350                     # Trigger emergency gas leak simulation (> 300 PPM)
bat-pod> say What happened?          # Ask for incident explanation
bat-pod> history                     # View recent SQLite audit log records
bat-pod> demo                        # Run automated golden path demo
bat-pod> help                        # View command list
bat-pod> quit                        # Exit shell
```

---

### 9. Run in Real Hardware Mode (Physical Microcontrollers)
When deploying to physical hardware:

1. **Flash Arduino Uno**: Open `firmware/arduino_sensor_hub/arduino_sensor_hub.ino` in Arduino IDE and upload to Arduino Uno.
2. **Flash ESP32**: Open `firmware/esp32_gateway/esp32_gateway.ino` in Arduino IDE and upload to ESP32.
3. **Wire Hardware**: Connect sensors and UART pins according to [HARDWARE_WIRING.md](docs/HARDWARE_WIRING.md).
4. **Start BAT POD**:
```bash
python main.py --mode=hardware --arduino-port=COM3 --esp32-port=COM4
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
├── pytest.ini               # Pytest path configurations
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
