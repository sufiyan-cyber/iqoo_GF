"""Display Controller managing device visual interface states."""

from typing import Any, Dict, Optional
from bat_pod.core.interfaces import IDisplay
from bat_pod.core.models import (
    DisplayState,
    EnvironmentalSnapshot,
)


class DisplayController:
    """Renders Normal, Approval, and Emergency UI states to display hardware."""

    def __init__(self, display: Optional[IDisplay] = None) -> None:
        self.display = display

    def set_display(self, display: IDisplay) -> None:
        self.display = display

    def show_normal(self, snapshot: EnvironmentalSnapshot) -> None:
        """Render standard status dashboard."""
        if not self.display:
            return

        temp_str = f"{snapshot.temperature.value:.1f}°C" if snapshot.temperature and snapshot.temperature.is_valid() else "--"
        gas_safe = (snapshot.gas.value or 0) < 150 if snapshot.gas and snapshot.gas.is_valid() else False
        gas_str = "SAFE" if gas_safe else f"{snapshot.gas.value:.1f} PPM" if snapshot.gas and snapshot.gas.is_valid() else "--"
        soil_str = f"{snapshot.soil_moisture.value:.1f}%" if snapshot.soil_moisture and snapshot.soil_moisture.is_valid() else "--"

        context = {
            "temp": temp_str,
            "gas": gas_str,
            "soil": soil_str,
            "summary": snapshot.safety_summary,
        }
        self.display.show_screen(DisplayState.NORMAL, context)

    def show_approval(self, action_name: str, detail: str) -> None:
        """Render interactive confirmation screen."""
        if not self.display:
            return

        context = {
            "action_name": action_name,
            "detail": detail,
        }
        self.display.show_screen(DisplayState.APPROVAL, context)

    def show_emergency(self, hazard: str, action_taken: str) -> None:
        """Render high-priority warning alert screen."""
        if not self.display:
            return

        context = {
            "hazard": hazard,
            "action": action_taken,
        }
        self.display.show_screen(DisplayState.EMERGENCY, context)
