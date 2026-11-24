from enum import IntEnum
from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU
from .shelly_blu_motion import ShellyBLUMotion


class LightLevel(IntEnum):
    """Light level values sent in BTHome object 0x64"""

    DARK = 0
    TWILIGHT = 1
    BRIGHT = 2


class ShellyBLUMotionZB(ShellyBLUMotion):
    """
    Creates a Shelly BLU Motion ZB device class.

    Motion is reported like the Shelly BLU Motion, but the light sensor sends a
    light level (dark, twilight, or bright) instead of illuminance in lux.
    """

    display_name = "Shelly BLU Motion ZB"

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        # Skip the BLU Motion's illuminance state, which this model never sends
        states = ShellyBLU.get_device_state_list(self)
        states.append(
            indigo.activePlugin.getDeviceStateDictForEnumType(
                "lightLevel", "Light Level Changed", "Light Level"
            )
        )
        # Indigo sets one true/false state per level, for triggers and conditions
        states.extend(
            indigo.activePlugin.getDeviceStateDictForBoolTrueFalseType(
                f"lightLevel.{level.name.lower()}",
                f"Light Level Is {level.name.title()}",
                f"Light Level {level.name.title()}",
            )
            for level in LightLevel
        )
        return states

    def get_state_updates(self, data: BLEData) -> list[dict[str, Any]]:
        """
        Build the state updates for a BTHome data packet.
        """
        state_updates = super().get_state_updates(data)

        if (light_level := data.sensors.get("light_level")) is not None:
            try:
                level = LightLevel(light_level)
            except ValueError:
                self.logger.warning(
                    f"Unknown light level {light_level} from {data.packet.address}, "
                    "please report it"
                )
            else:
                state_updates.append(
                    {
                        "key": "lightLevel",
                        "value": level.name.lower(),
                        "uiValue": level.name.title(),
                    }
                )

        return state_updates
