# BAT POD — Protocol, Schema & API Reference

## 1. UART Serial Protocol Specification

Microcontrollers and the Host AI Backend communicate over a newline-delimited JSON stream (`115200` baud, 8-N-1).

### 1.1 Telemetry Packet (Sensor Hub / ESP32 ➔ Host)
Dispatched once per second or upon state change.

```json
{
  "type": "telemetry",
  "temp": 26.5,
  "gas": 42.0,
  "soil": 21.0,
  "servo_angle": 90,
  "rfid": "CARD_ADMIN_001",
  "touch": 0,
  "error": null
}
```

### 1.2 Actuator Command Packet (Host ➔ Microcontroller)
```json
{
  "type": "command",
  "target": "servo",
  "cmd": "SET_SERVO",
  "angle": 0
}
```

### 1.3 Hardware Acknowledgement (ACK) Packet (Microcontroller ➔ Host)
Returned after physical execution to confirm or report physical state:
```json
{
  "type": "ack",
  "target": "servo",
  "state": "0_DEG",
  "verified": true
}
```

### 1.4 Display State Packet (Host ➔ ESP32 OLED)
```json
{
  "type": "display",
  "state": "approval",
  "context": {
    "action_name": "Water plant?",
    "detail": "Soil: 18%"
  }
}
```

---

## 2. Role-Based Access Control (RBAC) Matrix

| Role | Environmental Monitoring | Normal Actions (`water_plant`, `deactivate_alarm`) | Critical Actions (`close_valve`, `open_valve`) | Emergency Override |
| :--- | :---: | :---: | :---: | :---: |
| **Guest** (`GUEST`) | ✅ Allowed | ❌ Blocked | ❌ Blocked | ❌ Blocked |
| **Worker** (`WORKER`) | ✅ Allowed | ✅ Allowed (with approval) | ❌ Blocked | ❌ Blocked |
| **Admin** (`ADMIN`) | ✅ Allowed | ✅ Allowed (with approval) | ✅ Allowed | ✅ Allowed |
| **System Safety** | ✅ Auto | ✅ Auto | ✅ Auto (Bypasses approval) | ✅ Auto |

---

## 3. SQLite Audit Database Schema

Database path: `data/bat_pod.db`

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user TEXT NOT NULL,
    intent TEXT NOT NULL,
    sensor_context TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    authorization TEXT NOT NULL,
    execution_result TEXT NOT NULL,
    verification_result TEXT NOT NULL,
    error TEXT
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
```

### Audit Record Example (JSON Serialization)
```json
{
  "id": 14,
  "timestamp": "2026-10-05T20:35:21+00:00",
  "user": "SAFETY_DAEMON",
  "intent": "action:close_valve",
  "sensor_context": {
    "is_safe": false,
    "safety_summary": "EMERGENCY: GAS_LEAK detected!",
    "readings": {
      "gas": {"value": 350.0, "unit": "PPM", "status": "CRITICAL"}
    }
  },
  "requested_action": "close_valve",
  "authorization": "emergency_override",
  "execution_result": "success",
  "verification_result": "verified_success",
  "error": null
}
```
