# Product Requirements Document — BAT POD

**Product:** BAT POD  
**Version:** 1.0  
**Product Type:** Physical AI / Edge AI / Smart Living Device  
**Primary Track:** Smart Living  
**Secondary Track:** Open Innovation  
**Tagline:** *A Physical AI Companion for Smart Living*

---

## 1. Product Overview

BAT POD is a **voice-first physical AI companion** designed to monitor and interact with physical environments.

Unlike conventional smart-home devices that primarily collect sensor data or send alerts, BAT POD combines:

- Environmental sensing
- Natural-language voice interaction
- Local AI reasoning
- User authentication
- Human-in-the-loop authorization
- Physical actuation
- Real-time alerts
- Local audit logging

The fundamental product loop is:

> **SENSE → UNDERSTAND → DECIDE → ACT → CONFIRM**

The device is designed to operate **offline for critical safety functions**, minimizing dependence on cloud services and keeping sensitive environmental and voice data local.

---

# 2. Problem Statement

Current smart environments are fragmented.

Users typically have:

- Sensors that detect but do not reason.
- Mobile applications that require constant interaction.
- Cloud-dependent AI systems that introduce privacy and connectivity concerns.
- Alert systems that notify users but cannot physically respond.

This creates a gap between **environmental awareness and physical intervention**.

For example:

> A gas sensor can detect a leak.  
> An application can notify someone.  
> But neither necessarily closes the valve.

BAT POD aims to bridge this gap by creating a system capable of **sensing an event, understanding its context, obtaining authorization where required, executing an action, and confirming the result**.

The target users include elderly people, small farmers, clinics/pharmacies, workshops/labs, and families.

---

# 3. Product Vision

### Vision

> **Build a privacy-first physical AI platform capable of understanding everyday environments and safely interacting with them.**

BAT POD should eventually become a modular platform that can adapt to:

- Homes
- Farms
- Clinics
- Pharmacies
- Workshops
- Laboratories
- Small industrial environments

The same core platform should support different sensor and actuator configurations.

---

# 4. Product Goals

## 4.1 Primary Goals

### G1 — Environmental Awareness

Continuously collect environmental information from connected sensors.

### G2 — Natural Interaction

Allow users to ask questions and issue commands using natural language.

### G3 — Intelligent Interpretation

Convert natural-language requests into structured intents.

Example:

```text
User:
"Is the kitchen safe?"

↓

Intent:
check_safety

↓

Location:
kitchen

↓

Required data:
temperature + gas

↓

Result:
SAFE
```

### G4 — Physical Action

Allow BAT POD to control physical components such as:

- Servo motors
- Pumps
- Locks
- Valves
- Alarms

### G5 — Safety

No critical physical action should be executed blindly.

The system must have authorization, confirmation, safe-state handling, and auditability.

### G6 — Privacy

Critical functionality should operate locally without requiring continuous cloud connectivity.

---

# 5. Non-Goals

To prevent scope creep, the following are **not part of the MVP**:

- Full medical diagnosis
- Autonomous medical decisions
- Industrial-grade gas detection certification
- Commercial home-security certification
- Facial recognition
- Continuous cloud video surveillance
- Fully autonomous high-risk physical actions
- Large-scale IoT fleet management
- Production-grade mobile application

BAT POD is initially a **prototype and demonstration platform**, not a certified safety-critical product.

---

# 6. Target Users

| Persona | Primary Need |
|---|---|
| Elderly resident | Safety monitoring and easy voice interaction |
| Family member | Remote confidence about elderly relative's environment |
| Small farmer | Soil/environment monitoring and irrigation assistance |
| Clinic/pharmacy staff | Temperature and gas monitoring |
| Workshop operator | Environmental safety monitoring |
| Authorized worker | Secure access and physical control |

---

# 7. Core User Journey

### Standard Interaction

```text
User
 ↓
Voice / Touch
 ↓
Voice Activity Detection
 ↓
Speech-to-Text
 ↓
Intent Detection
 ↓
Sensor Context Retrieval
 ↓
Decision Engine
 ↓
Authorization
 ↓
Action
 ↓
Hardware Confirmation
 ↓
Response
 ↓
Audit Log
```

---

# 8. Functional Requirements

## FR-01 — Sensor Monitoring

BAT POD shall collect data from connected sensors.

### MVP Sensors

1. Temperature
2. Gas
3. Soil moisture

### Optional

4. IR motion
5. Pulse oximeter

### Requirements

- Sensor readings shall be periodically sampled.
- Readings shall be timestamped.
- Invalid readings shall be flagged.
- Sensor failures shall not be represented as valid readings.
- Sensor data shall be available to the decision engine.

---

# 9. FR-02 — Voice Interaction

BAT POD shall provide voice-first interaction.

### Example commands

```text
"Is the environment safe?"

"Is there any gas leak?"

"Does the plant need water?"

"Water the plant."

"What happened?"

"Is the temperature normal?"
```

The system shall support:

- Voice capture
- Voice activity detection
- Wake-word or push-to-talk
- Speech-to-text
- Intent extraction
- Response generation
- Text-to-speech

Sarvam is proposed for Indian-language STT/TTS.

---

# 10. FR-03 — Multilingual Interaction

The system should support:

### MVP

- English
- Kannada

### Future

- Hindi
- Additional Indian languages

The language should ideally be automatically detected by the voice pipeline.

---

# 11. FR-04 — Intent Understanding

Natural-language input shall be converted into structured intents.

Example:

```json
{
  "intent": "check_safety",
  "location": "kitchen"
}
```

Another example:

```json
{
  "intent": "water_plant",
  "target": "plant_01",
  "action": "activate_pump"
}
```

The local LLM should perform **intent parsing**, while deterministic rules should control safety-critical decisions.

### Important architectural principle

> **LLM proposes. Rules authorize. Hardware confirms.**

The LLM should **not directly control a servo or pump**.

---

# 12. FR-05 — Sensor Context Retrieval

After intent extraction, the system shall retrieve only the sensor information relevant to that intent.

Example:

```text
Intent:
check_kitchen_safety

Required:
├── Gas
├── Temperature
└── Motion

Not required:
└── Soil moisture
```

This reduces unnecessary processing and improves explainability.

---

# 13. FR-06 — Decision Engine

BAT POD shall combine:

- Sensor readings
- User intent
- Device state
- Authorization state
- Safety rules

to determine the next operation.

### Decision categories

```text
INFORMATION
ACTION_REQUIRED
SAFETY_ALERT
AUTHORIZATION_REQUIRED
ERROR
```

Example:

```text
Gas detected
      ↓
Safety rule triggered
      ↓
Critical event
      ↓
Close valve
      ↓
Alarm
      ↓
Display warning
      ↓
Log event
```

---

# 14. FR-07 — Human-in-the-Loop Approval

For configurable physical actions, BAT POD shall request user confirmation.

Example:

> **Water plant?**  
> Soil moisture: 21%  
> Pump duration: 5 sec  
>
> `[APPROVE] [CANCEL]`

Approval may occur through:

- Touch button
- Authorized voice confirmation
- RFID authentication where required

---

# 15. FR-08 — Emergency Safety Actions

Safety-critical events require a different policy from normal user-requested actions.

Example:

```text
Gas detected
      ↓
Safety threshold exceeded
      ↓
Trigger emergency policy
      ↓
Close simulated valve
      ↓
Activate alarm
      ↓
Display warning
      ↓
Log event
```

The PRD distinguishes:

### Normal Action

Requires authorization.

### Emergency Safety Response

May execute automatically if the predefined threshold is exceeded.

This prevents a dangerous contradiction between "every action requires approval" and the requirement to respond rapidly to hazards.

---

# 16. FR-09 — RFID Authentication

RFID shall identify authorized users.

Example:

```text
RFID detected
      ↓
Read UID
      ↓
Check local authorization list
      ↓
AUTHORIZED
      ↓
Allow privileged operation
```

Unauthorized users shall not be permitted to trigger protected actions.

---

# 17. FR-10 — Physical Actuation

BAT POD shall support at least one physical actuator in the MVP.

### Recommended MVP

**Servo motor**

Use cases:

- Simulated valve closure
- Door locking
- Physical mechanism activation

Optional:

- Water pump
- Motor controller
- Additional servos

---

# 18. FR-11 — Display

The display shall provide:

### Normal state

```text
BAT POD
──────────────
TEMP       26°C
GAS        SAFE
SOIL       42%

STATUS
Everything OK
```

### Approval state

```text
ACTION REQUEST

Water plant?

Soil: 18%

[ APPROVE ]
[ CANCEL ]
```

### Emergency state

```text
⚠ WARNING

GAS DETECTED

Closing valve...

ALARM ACTIVE
```

---

# 19. FR-12 — Audio Output

BAT POD shall communicate through:

- Speaker
- TTS

Example:

> "Warning. Gas detected. Closing the valve."

The spoken response should correspond to the actual device state.

---

# 20. FR-13 — Hardware Confirmation

BAT POD shall never claim an action succeeded merely because a command was sent.

Instead:

```text
COMMAND
  ↓
ACTUATOR
  ↓
PHYSICAL STATE
  ↓
CONFIRMATION
  ↓
USER RESPONSE
```

Example:

```text
Servo command sent
      ↓
Servo reaches target
      ↓
State confirmed
      ↓
"Valve closed successfully."
```

If confirmation fails:

> "I attempted to close the valve, but I could not confirm the physical state."

---

# 21. FR-14 — Audit Logging

Every important operation shall be logged.

### Example

```json
{
  "timestamp": "2026-10-05T20:35:21",
  "user": "RFID_01",
  "intent": "water_plant",
  "action": "pump_on",
  "authorization": "approved",
  "result": "success"
}
```

Logs should capture:

- Timestamp
- User/device identity
- Intent
- Sensor state
- Requested action
- Authorization
- Execution result
- Failure reason if applicable

SQLite is appropriate for the prototype.

---

# 22. System Architecture

## Hardware

```text
                 ┌─────────────────────┐
                 │     BAT POD         │
                 │                     │
Sensors ────────►│   Arduino Uno       │
                 │   Sensor Hub        │
                 └─────────┬───────────┘
                           │
                         UART
                           │
                           ▼
                 ┌─────────────────────┐
                 │       ESP32         │
                 │                     │
                 │ Voice               │
                 │ Display             │
                 │ Wi-Fi               │
                 │ AI communication    │
                 │ Decision interface  │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Local AI Backend    │
                 │                     │
                 │ STT / TTS           │
                 │ Local LLM           │
                 │ Rules Engine        │
                 │ Audit Database      │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Action Layer        │
                 │ Servo / Motor       │
                 │ Alarm / Display     │
                 │ Speaker             │
                 └─────────────────────┘
```

The dual-brain architecture separates deterministic sensing from higher-level AI/voice processing.

---

# 23. Software Architecture

## Layer 1 — Device Firmware

### ESP32

- Device communication
- Display
- Voice interface
- Network communication
- Actuator interface

### Arduino

- Sensor polling
- Sensor preprocessing
- Actuator-level control
- Safety fallback

---

## Layer 2 — AI Gateway

```text
Audio
 ↓
STT
 ↓
Intent Parser
 ↓
Context Manager
 ↓
Decision Engine
```

---

## Layer 3 — Safety Policy Engine

This should be **deterministic**, not LLM-controlled.

Example:

```python
if gas_level > CRITICAL_THRESHOLD:
    emergency_action("CLOSE_VALVE")
```

The LLM can identify the context, but safety policies determine whether an action is allowed.

---

## Layer 4 — Action Manager

Responsible for:

- Permission checking
- Confirmation
- Actuator execution
- Hardware verification
- Failure handling
- Logging

---

## Layer 5 — Audit Database

SQLite for MVP.

---

# 24. Non-Functional Requirements

## NFR-01 — Latency

| Operation | Target |
|---|---:|
| Sensor reading | <1 sec |
| Intent parsing | <3 sec |
| Normal voice response | <5 sec |
| Emergency detection | <5 sec |
| Physical action initiation | <2 sec after authorization |

---

## NFR-02 — Availability

Critical safety functions should operate without internet.

Target:

> **100% of critical safety functions available offline**

---

## NFR-03 — Reliability

Target:

- >90% voice-query success in English/Kannada
- <5% false-positive rate
- 100% action auditability

---

# 25. Privacy Requirements

BAT POD shall follow an **offline-first architecture**.

### Default

```text
Voice
 ↓
Local processing
 ↓
Local decision
 ↓
Local action
 ↓
Local storage
```

No environmental or voice data should leave the device unless explicitly configured.

### Hardware privacy controls

- Physical microphone mute
- Microphone indicator LED
- Session timeout
- Local audit log

---

# 26. Security Requirements 🔐

Security should be treated as a first-class product requirement.

### Authentication

- RFID-based authentication
- Device-level authorization

### Authorization

Different users should eventually have different permissions.

| User | View | Normal Actions | Critical Actions |
|---|---:|---:|---:|
| Guest | ✓ | ✗ | ✗ |
| Worker | ✓ | ✓ | ✗ |
| Admin | ✓ | ✓ | ✓ |

### Integrity

The device should reject:

- Unknown RFID users
- Malformed commands
- Invalid sensor values
- Unauthorized actuator requests

---

# 27. Failure Handling

BAT POD must fail safely.

### Scenario: Sensor failure

```text
Sensor unavailable
 ↓
Mark reading INVALID
 ↓
Do not fabricate value
 ↓
Display warning
 ↓
Log failure
```

### Scenario: Arduino disconnected

```text
Heartbeat lost
 ↓
ESP32 detects failure
 ↓
Disable unsafe actions
 ↓
Display ERROR
 ↓
Log event
```

### Scenario: AI unavailable

Critical deterministic safety functions should continue operating.

### Scenario: Actuator failure

```text
Action requested
 ↓
Actuator command
 ↓
Verification fails
 ↓
Report failure
 ↓
Safe-state procedure
 ↓
Audit log
```

---

# 28. MVP Definition

The MVP should **not attempt every use case**.

### MVP = One complete end-to-end experience.

### Required

- ESP32
- Arduino Uno
- Temperature sensor
- Gas sensor
- Soil moisture sensor
- Microphone
- Speaker
- Display
- Servo
- RFID
- Touch button
- UART communication
- Sarvam STT/TTS
- Local LLM
- Rule engine
- SQLite audit log

---

# 29. MVP Golden Path

The entire product should be demonstrated through **one coherent scenario**.

### Step 1 — Authentication

```text
RFID → Authorized User
```

### Step 2 — Safety Question

User:

> "BAT POD, is the environment safe?"

### Step 3 — Sensor Context

BAT POD retrieves:

```text
Temperature
Gas
Soil moisture
```

### Step 4 — Response

> "Temperature is normal. Soil moisture is low. No gas detected."

### Step 5 — Action Request

User:

> "Water the plant."

### Step 6 — Approval

```text
Water plant?

[ APPROVE ]
[ CANCEL ]
```

### Step 7 — Execution

User approves and the pump/servo activates.

### Step 8 — Confirmation

BAT POD confirms the physical action.

### Step 9 — Safety Event

A safe gas-sensor demonstration triggers the configured threshold.

### Step 10 — Emergency Response

BAT POD:

> "Warning. Gas detected. Closing valve."

The servo closes the simulated valve and the alarm/display activate.

### Step 11 — Explanation

User:

> "What happened?"

BAT POD explains the event.

---

# 30. Acceptance Criteria

## Hardware

- [ ] Arduino reads ≥3 sensors.
- [ ] Arduino communicates with ESP32.
- [ ] ESP32 drives display.
- [ ] Servo performs a physical action.
- [ ] RFID authentication works.
- [ ] Touch approval works.

## AI

- [ ] Voice input is captured.
- [ ] Speech is converted to text.
- [ ] Intent is extracted.
- [ ] Sensor context is retrieved.
- [ ] Natural-language response is generated.
- [ ] TTS response works.

## Safety

- [ ] Unauthorized users cannot execute protected actions.
- [ ] Safety threshold triggers emergency response.
- [ ] System does not falsely report actuator success.
- [ ] Critical safety logic continues without internet.
- [ ] Hardware failure enters a safe state.

## Data

- [ ] Actions are logged.
- [ ] Sensor readings can be retrieved.
- [ ] Audit records contain timestamp + action + result.

---

# 31. Success Metrics

## Hackathon MVP

| Metric | Target |
|---|---:|
| Sensor integrations | ≥3 |
| Voice-query success | >90% |
| Emergency response | <5 sec |
| False positives | <5% |
| Action logging | 100% |
| Safety-function offline availability | 100% |
| Physical action success | >95% |

---

# 32. Roadmap

## Phase 1 — Hackathon MVP

**Goal:** Working physical AI demonstration.

```text
Sensors
+
Voice
+
LLM
+
Approval
+
Servo
+
Audit
```

---

## Phase 2 — Pilot

Deploy to:

- 5 homes
- 2 small clinics

Collect:

- Voice accuracy
- False alarms
- User satisfaction
- Sensor reliability
- Response latency

---

## Phase 3 — Modular Platform

Create interchangeable modules:

```text
BAT POD Core
│
├── Home Module
├── Farm Module
├── Clinic Module
├── Workshop Module
└── Elder Care Module
```

---

## Phase 4 — Ecosystem

Long-term:

- Open-source hardware
- Open-source firmware
- Developer APIs
- Third-party sensors
- Third-party actuators
- Community-built modules

---

# 33. Future Features

## P1

- Kannada + Hindi support
- IR motion detection
- Pulse oximeter
- Remote alerts
- Better local model

## P2

- Web dashboard
- Historical analytics
- Remote family monitoring
- More RFID roles
- OTA firmware updates

## P3

- Wake-word detection
- Multi-device communication
- Edge model optimization
- Plugin architecture
- Open hardware ecosystem

---

# 34. Major Product Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Gas sensor false positives | High | Calibration + thresholding + secondary validation |
| LLM hallucination | High | LLM cannot directly control actuators |
| Voice recognition failure | Medium | Display confirmation + touch controls |
| ESP32 memory constraints | High | Local-server inference fallback |
| UART failure | High | Heartbeat + safe state |
| Power loss | High | Battery backup for critical functions |
| Unauthorized action | Critical | RFID + authorization |
| Sensor failure | High | Health monitoring + invalid state |
| Privacy concerns | High | Local processing + physical mic mute |

---

# 35. Product Architecture Principle

The most important design principle for BAT POD is:

> ### **AI should interpret. Rules should authorize. Hardware should verify.**

The system should not simply operate as:

```text
Voice → LLM → Servo
```

Instead:

```text
             AI
              │
       "What does user mean?"
              │
              ▼
        Intent Engine
              │
              ▼
        Safety Rules
              │
       ┌──────┴──────┐
       │             │
    Allowed       Blocked
       │             │
       ▼             ▼
  Authorization     Explain
       │
       ▼
   Actuator
       │
       ▼
   Verification
       │
       ▼
     Audit
```

This distinction is critical if BAT POD is eventually used in environments involving gas, medical equipment, doors, pumps, or other physical systems.

---

# 36. Final Product Definition

### BAT POD

> **A privacy-first physical AI companion that senses its environment, understands natural language, reasons over real-world context, and safely interacts with the physical world.**

### Core Architecture

**ESP32 + Arduino + Sensors + Local AI + Voice + Rules Engine + Actuators**

### Core Interaction

**Sense → Understand → Decide → Act → Confirm**

### Core Differentiator

> **It doesn't just tell you what is happening. It can safely do something about it.**

### MVP

> **A multilingual voice-controlled physical AI device that reads real sensor data, reasons locally, asks for authorization, performs a physical action, verifies the result, and records the entire event locally.**

---

## Product Success Definition

BAT POD succeeds when a user can interact with a physical device using natural language, the device can understand the request in context, retrieve real-world sensor information, make a safe deterministic decision, obtain appropriate authorization, perform a physical action, verify that action actually happened, communicate the outcome, and retain an auditable local record — without requiring continuous cloud connectivity.

**BAT POD is not just a project. It is a physical AI platform for bringing intelligence into everyday spaces.**
