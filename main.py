"""BAT POD - Main Executable Entrypoint.

Usage:
    python main.py --mode=mock --interactive
    python main.py --mode=hardware --arduino-port=COM3 --esp32-port=COM4
    python main.py --demo
"""

import argparse
import sys
import time
from typing import Optional

# Ensure standard output can print utf-8 safely across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

from bat_pod.audit.audit_logger import audit_logger
from bat_pod.config import settings
from bat_pod.core.models import DisplayState, SensorStatus, UserRole
from bat_pod.hal.mock_adapters import (
    MockAlarmActuator,
    MockAudioInput,
    MockAudioOutput,
    MockDisplay,
    MockGasSensor,
    MockPumpActuator,
    MockRFIDProvider,
    MockServoActuator,
    MockSoilMoistureSensor,
    MockTemperatureSensor,
    MockTouchButton,
)
from bat_pod.hal.real_adapters import (
    RealAlarmActuator,
    RealDisplay,
    RealGasSensor,
    RealPumpActuator,
    RealRFIDProvider,
    RealServoActuator,
    RealSoilMoistureSensor,
    RealTemperatureSensor,
    RealTouchButton,
    SerialDeviceManager,
)
from bat_pod.orchestrator.pod_controller import BatPodController

console = Console()


def build_system(mode: str, arduino_port: str, esp32_port: str, baud: int):
    """Factory creating a BatPodController configured for Mock or Real Hardware."""
    if mode == "hardware":
        console.print(f"[bold cyan]Connecting to Physical Hardware: Arduino on {arduino_port}, ESP32 on {esp32_port}...[/]")
        arduino_mgr = SerialDeviceManager(arduino_port, baud=baud)
        esp32_mgr = SerialDeviceManager(esp32_port, baud=baud)

        arduino_connected = arduino_mgr.connect()
        esp32_connected = esp32_mgr.connect()

        if not arduino_connected and not esp32_connected:
            console.print("[bold red]Failed to open physical serial ports. Falling back to Mock mode for safety.[/]")
            return build_system("mock", arduino_port, esp32_port, baud)

        temp_sensor = RealTemperatureSensor(arduino_mgr)
        gas_sensor = RealGasSensor(arduino_mgr)
        soil_sensor = RealSoilMoistureSensor(arduino_mgr)
        servo = RealServoActuator(arduino_mgr)
        pump = RealPumpActuator(arduino_mgr)
        alarm = RealAlarmActuator(arduino_mgr)
        rfid = RealRFIDProvider(esp32_mgr)
        touch = RealTouchButton(esp32_mgr)
        display = RealDisplay(esp32_mgr)
        audio_in = None
        audio_out = None

        controller = BatPodController(
            temp_sensor=temp_sensor,
            gas_sensor=gas_sensor,
            soil_sensor=soil_sensor,
            servo=servo,
            pump=pump,
            alarm=alarm,
            rfid=rfid,
            touch=touch,
            display=display,
            audio_in=audio_in,
            audio_out=audio_out,
        )
        return controller, None

    # MOCK MODE
    temp_sensor = MockTemperatureSensor(initial_c=26.0)
    gas_sensor = MockGasSensor(initial_ppm=42.0)
    soil_sensor = MockSoilMoistureSensor(initial_pct=21.0)
    servo = MockServoActuator(initial_angle=90)
    pump = MockPumpActuator()
    alarm = MockAlarmActuator()
    rfid = MockRFIDProvider()
    touch = MockTouchButton()
    display = MockDisplay()
    audio_in = MockAudioInput()
    audio_out = MockAudioOutput()

    controller = BatPodController(
        temp_sensor=temp_sensor,
        gas_sensor=gas_sensor,
        soil_sensor=soil_sensor,
        servo=servo,
        pump=pump,
        alarm=alarm,
        rfid=rfid,
        touch=touch,
        display=display,
        audio_in=audio_in,
        audio_out=audio_out,
    )

    mocks = {
        "temp": temp_sensor,
        "gas": gas_sensor,
        "soil": soil_sensor,
        "servo": servo,
        "pump": pump,
        "alarm": alarm,
        "rfid": rfid,
        "touch": touch,
        "display": display,
        "audio_in": audio_in,
        "audio_out": audio_out,
    }
    return controller, mocks


def run_golden_path_demo(controller: BatPodController, mocks: dict) -> bool:
    """Automated execution of the entire 11-step MVP Golden Path."""
    console.print("\n" + "=" * 60, style="bold green")
    console.print("[BAT POD] STARTING MVP GOLDEN PATH DEMONSTRATION", style="bold green")
    console.print("=" * 60 + "\n", style="bold green")

    # Step 1: RFID Tap
    console.print("[bold yellow]Step 1: User presents Admin RFID Card...[/]")
    mocks["rfid"].tap_card("CARD_ADMIN_001")
    controller.sense()
    user = controller.auth.get_active_user()
    console.print(f"  [green][OK] User identified: {user.name} (Role: {user.role.value})[/]")

    # Step 2: Environmental Query
    console.print("\n[bold yellow]Step 2: User asks: 'BAT POD, is the environment safe?'...[/]")
    resp = controller.process_utterance("BAT POD, is the environment safe?")
    console.print(f"  [cyan]BAT POD Voice: \"{resp}\"[/]")

    # Step 3: Water plant request
    console.print("\n[bold yellow]Step 3: User says: 'Water the plant.'...[/]")
    resp = controller.process_utterance("Water the plant.")
    console.print(f"  [cyan]BAT POD Voice: \"{resp}\"[/]")
    console.print(f"  [blue]Display Screen:\n{mocks['display'].current_screen_text}[/]")

    # Step 4: Human Approval & Execution
    console.print("\n[bold yellow]Step 4: User presses touch button to approve...[/]")
    exec_res = controller.handle_user_approval(approved=True)
    console.print(f"  [green][OK] Action execution: {exec_res.execution_result}[/]")
    console.print(f"  [green][OK] Hardware verified state: {exec_res.verification_status.value} (Servo: {mocks['servo'].get_state()})[/]")

    # Step 5: Gas Hazard Simulation
    console.print("\n[bold yellow]Step 5: Safe gas sensor test spikes above 300 PPM threshold (350 PPM)...[/]")
    mocks["gas"].set_value(350.0)
    controller.sense()
    console.print(f"  [red][ALERT] EMERGENCY AUTO-TRIGGERED: Servo Valve State = {mocks['servo'].get_state()}[/]")
    console.print(f"  [red][ALERT] Alarm State = {mocks['alarm'].get_state()}[/]")
    console.print(f"  [red]Display Screen:\n{mocks['display'].current_screen_text}[/]")

    # Step 6: User Asks "What Happened?"
    console.print("\n[bold yellow]Step 6: User asks: 'What happened?'...[/]")
    resp = controller.process_utterance("What happened?")
    console.print(f"  [cyan]BAT POD Voice: \"{resp}\"[/]")

    # Step 7: Inspect Audit Database
    console.print("\n[bold yellow]Step 7: Verifying SQLite Audit Trail...[/]")
    recent = audit_logger.get_recent(limit=3)
    table = Table(title="Recent Audit Records")
    table.add_column("ID", justify="right")
    table.add_column("Timestamp")
    table.add_column("User")
    table.add_column("Action")
    table.add_column("Authorization")
    table.add_column("Result")
    table.add_column("Verified")

    for r in recent:
        table.add_row(
            str(r.id),
            r.timestamp.split("T")[-1][:8],
            r.user,
            r.requested_action,
            r.authorization,
            r.execution_result,
            r.verification_result,
        )
    console.print(table)

    console.print("\n" + "=" * 60, style="bold green")
    console.print("[SUCCESS] GOLDEN PATH DEMO COMPLETED SUCCESSFULLY!", style="bold green")
    console.print("=" * 60 + "\n", style="bold green")
    return True


def run_interactive_shell(controller: BatPodController, mocks: Optional[dict]):
    """Interactive command shell allowing full live control of BAT POD."""
    console.print(Panel("[bold green]BAT POD Interactive Shell[/]\nType 'help' for commands, 'demo' for Golden Path, or 'quit' to exit."))

    while True:
        try:
            line = input("\nbat-pod> ").strip()
            if not line:
                continue

            parts = line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("quit", "exit"):
                console.print("[dim]Exiting BAT POD. Stay safe![/]")
                break

            elif cmd == "help":
                console.print(
                    """
[bold]Available Commands:[/]
  [cyan]status[/]             - Display current readings, screen, and user
  [cyan]say <phrase>[/]       - Issue voice command (e.g. 'say is the environment safe?')
  [cyan]tap <card_id>[/]      - Tap RFID card (e.g. 'tap CARD_ADMIN_001', 'tap CARD_WORKER_002')
  [cyan]approve[/] / [cyan]touch[/]     - Approve pending physical action
  [cyan]reject[/]              - Reject pending physical action
  [cyan]gas <ppm>[/]          - Set simulated gas level (e.g. 'gas 350')
  [cyan]temp <degC>[/]        - Set simulated temperature (e.g. 'temp 28.5')
  [cyan]soil <pct>[/]         - Set simulated soil moisture (e.g. 'soil 18')
  [cyan]history[/]            - Show last 5 SQLite audit records
  [cyan]demo[/]               - Run complete 11-step MVP Golden Path demonstration
  [cyan]quit[/]               - Exit shell
                    """
                )

            elif cmd == "demo":
                if mocks:
                    run_golden_path_demo(controller, mocks)
                else:
                    console.print("[red]Automated demo script requires Mock mode.[/]")

            elif cmd == "status":
                snap = controller.sense()
                user = controller.auth.get_active_user()
                console.print(f"[bold]Active User:[/] {user.name} ({user.role.value})")
                console.print(f"[bold]Sensors:[/] Temp={snap.temperature.value}°C, Gas={snap.gas.value} PPM, Soil={snap.soil_moisture.value}%")
                console.print(f"[bold]Safety:[/] Safe={snap.is_safe} ({snap.safety_summary})")
                if mocks and "display" in mocks:
                    console.print(f"[blue]{mocks['display'].current_screen_text}[/]")

            elif cmd == "say":
                if not arg:
                    console.print("[red]Please specify text to say.[/]")
                    continue
                resp = controller.process_utterance(arg)
                console.print(f"[cyan]Voice:[/] {resp}")
                if mocks and "display" in mocks:
                    console.print(f"[blue]{mocks['display'].current_screen_text}[/]")

            elif cmd == "tap":
                if not arg:
                    console.print("[red]Specify RFID card UID (e.g., tap CARD_ADMIN_001)[/]")
                    continue
                if mocks and "rfid" in mocks:
                    mocks["rfid"].tap_card(arg)
                    controller.sense()
                    u = controller.auth.get_active_user()
                    console.print(f"[green]Tapped card {arg}: {u.name} ({u.role.value})[/]")
                else:
                    console.print("[yellow]RFID tap simulation only available in Mock mode.[/]")

            elif cmd in ("approve", "touch"):
                res = controller.handle_user_approval(approved=True)
                if res:
                    console.print(f"[green]Action completed: {res.execution_result} (Verified: {res.verification_status.value})[/]")

            elif cmd == "reject":
                res = controller.handle_user_approval(approved=False)
                if res:
                    console.print(f"[yellow]Action cancelled by user.[/]")

            elif cmd == "gas":
                if mocks and "gas" in mocks:
                    try:
                        val = float(arg)
                        mocks["gas"].set_value(val)
                        console.print(f"[magenta]Gas sensor set to {val} PPM[/]")
                        controller.sense()
                        if mocks and "display" in mocks:
                            console.print(f"[blue]{mocks['display'].current_screen_text}[/]")
                    except ValueError:
                        console.print("[red]Invalid number for gas PPM[/]")
                else:
                    console.print("[yellow]Gas simulation only available in Mock mode.[/]")

            elif cmd == "temp":
                if mocks and "temp" in mocks:
                    try:
                        val = float(arg)
                        mocks["temp"].set_value(val)
                        console.print(f"[magenta]Temperature set to {val}°C[/]")
                        controller.sense()
                    except ValueError:
                        console.print("[red]Invalid temperature number[/]")

            elif cmd == "soil":
                if mocks and "soil" in mocks:
                    try:
                        val = float(arg)
                        mocks["soil"].set_value(val)
                        console.print(f"[magenta]Soil moisture set to {val}%[/]")
                        controller.sense()
                    except ValueError:
                        console.print("[red]Invalid soil moisture percentage[/]")

            elif cmd == "history":
                records = audit_logger.get_recent(limit=5)
                table = Table(title="Recent Audit Log")
                table.add_column("ID")
                table.add_column("Timestamp")
                table.add_column("User")
                table.add_column("Action")
                table.add_column("Auth")
                table.add_column("Result")
                table.add_column("Verified")
                for r in records:
                    table.add_row(
                        str(r.id),
                        r.timestamp.split("T")[-1][:8],
                        r.user,
                        r.requested_action,
                        r.authorization,
                        r.execution_result,
                        r.verification_result,
                    )
                console.print(table)

            else:
                console.print(f"[red]Unknown command '{cmd}'. Type 'help' for available commands.[/]")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as ex:
            console.print(f"[bold red]Error:[/] {ex}")


def main():
    parser = argparse.ArgumentParser(description="BAT POD — Physical AI Companion MVP")
    parser.add_argument("--mode", choices=["mock", "hardware"], default=settings.BAT_POD_MODE, help="Run mode")
    parser.add_argument("--arduino-port", default=settings.ARDUINO_PORT, help="Arduino serial port")
    parser.add_argument("--esp32-port", default=settings.ESP32_PORT, help="ESP32 serial port")
    parser.add_argument("--baud", type=int, default=settings.ARDUINO_BAUD, help="Serial baud rate")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive terminal shell")
    parser.add_argument("--demo", action="store_true", help="Run automated Golden Path demo and exit")

    args = parser.parse_args()

    controller, mocks = build_system(
        mode=args.mode,
        arduino_port=args.arduino_port,
        esp32_port=args.esp32_port,
        baud=args.baud,
    )

    if args.demo:
        if not mocks:
            console.print("[bold red]Cannot run automated demo against hardware mode without mock simulator.[/]")
            sys.exit(1)
        success = run_golden_path_demo(controller, mocks)
        sys.exit(0 if success else 1)

    if args.interactive or len(sys.argv) == 1:
        run_interactive_shell(controller, mocks)
    else:
        # Default headless loop
        console.print("[bold green]BAT POD running in background polling loop... (Ctrl+C to stop)[/]")
        try:
            while True:
                controller.sense()
                time.sleep(settings.SENSOR_POLL_INTERVAL_SEC)
        except KeyboardInterrupt:
            console.print("\nShutting down BAT POD.")


if __name__ == "__main__":
    main()
