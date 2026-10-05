# BAT POD — MVP Golden Path Demonstration Guide

This guide walks through the exact 11-step **Golden Path** specified in Section 15 & 29 of `BAT_POD_PRD.md`.

---

## 1. Running the System

You can run BAT POD in **Simulation Mode** (no hardware needed) or **Hardware Mode** (with physical Arduino Uno & ESP32):

### Simulation Mode (Recommended for testing & demonstration)
```bash
python main.py --mode=mock --interactive
```

### Hardware Mode (With physical microcontrollers attached)
```bash
python main.py --mode=hardware --arduino-port=COM3 --esp32-port=COM4
```

---

## 2. Step-by-Step Golden Path Script

### Step 1: Authentication via RFID
- **Action**: Tap the RFID card (`CARD_ADMIN_001` or `CARD_WORKER_002`).
  - *Simulation*: Enter command `tap CARD_ADMIN_001`
- **BAT POD Response**:
  > *"User recognized: Bruce Wayne (admin). Hello Bruce Wayne."*

---

### Step 2: Environmental Safety Query
- **User Speaks**:
  > *"BAT POD, is the environment safe?"*
  - *Simulation*: Enter `say Is the environment safe?`
- **BAT POD Output**:
  - Retrieves Temperature, Gas, and Soil moisture context.
  - Display displays **Normal** dashboard.
  - Spoken output:
  > *"Temperature is normal at 26.0°C. Soil moisture is low at 21.0%. No gas detected. Everything is safe."*

---

### Step 3: Action Request (Water Plant)
- **User Speaks**:
  > *"Water the plant."*
  - *Simulation*: Enter `say Water the plant`
- **BAT POD Verification**:
  - Deterministic safety engine checks if soil is already flooded (it is 21.0% = safe).
  - RBAC checks user permission (Worker/Admin = permitted).
  - Human-in-the-loop approval created.
- **Display**: Switches to **APPROVAL** screen:
  ```text
  ┌────────────────────────────────┐
  │         ACTION REQUEST         │
  ├────────────────────────────────┤
  │ Water Plant?                   │
  │                                │
  │ Soil: 21.0%                    │
  │                                │
  │ [ APPROVE ]       [ CANCEL ]   │
  └────────────────────────────────┘
  ```
- **Spoken Prompt**:
  > *"Water the plant? Current soil moisture is 21.0%. Please approve using the touch button or voice."*

---

### Step 4: Human-in-the-Loop Approval & Verification
- **User Action**: Press the physical touch button or reply with approval.
  - *Simulation*: Enter `approve` (or `touch`)
- **Actuator Execution**:
  - Pump/servo activates to dispense water.
  - Actuator verifies physical state (`VERIFIED_SUCCESS`).
  - Event is written to local SQLite audit log.
- **BAT POD Output**:
  > *"Plant watered successfully. Physical action verified."*
- Display returns to **NORMAL** dashboard.

---

### Step 5: Gas Safety Hazard Event (Emergency Simulation)
- **Trigger**: Safe gas sensor spike simulating a leak (> 300 PPM threshold).
  - *Simulation*: Enter `gas 350`
- **Deterministic Auto-Intervention (< 1 second)**:
  - Gas reading = 350.0 PPM (exceeds 300 PPM threshold).
  - **No human approval required**: Emergency safety policy instantly triggers.
  - Servo moves to 0° (closes simulated valve).
  - Piezo buzzer / alarm turns ON.
  - Display switches to **EMERGENCY** screen:
  ```text
  ┌────────────────────────────────┐
  │         ⚠ WARNING ⚠            │
  ├────────────────────────────────┤
  │ GAS_LEAK detected!             │
  │                                │
  │ Closing valve & Alarm ON       │
  │                                │
  │ >>> ALARM ACTIVE <<<           │
  └────────────────────────────────┘
  ```
- **Spoken Alert**:
  > *"Warning! GAS_LEAK detected. Closing valve."*
- Complete emergency event recorded to SQLite audit table.

---

### Step 6: Incident Explanation
- **User Asks**:
  > *"What happened?"*
  - *Simulation*: Enter `say What happened?`
- **BAT POD Explanation**:
  - Queries SQLite audit database for the most recent emergency record.
  - Synthesizes factual, clear summary:
  > *"At 20:35, elevated gas concentration of 350.0 PPM triggered an emergency response. The valve was automatically closed, the alarm was activated, and the event was logged."*

---

## 3. Demonstration Commands Cheatsheet

| Command | Description |
| :--- | :--- |
| `status` | Print current environmental snapshot and display screen |
| `tap <CARD_ID>` | Simulate tapping an RFID card (`CARD_ADMIN_001`, `CARD_WORKER_002`, `GUEST`) |
| `say <utterance>` | Speak a voice query or command |
| `approve` / `touch` | Confirm pending human approval |
| `reject` | Cancel pending human approval |
| `gas <ppm>` | Set mock gas level (e.g. `gas 350` to trigger emergency) |
| `temp <c>` | Set mock temperature (e.g. `temp 28`) |
| `soil <pct>` | Set mock soil moisture (e.g. `soil 15`) |
| `history` | Print the 5 most recent SQLite audit log records |
| `quit` | Exit BAT POD |
