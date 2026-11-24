from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU


class ShellyBLURemoteControlZB(ShellyBLU):
    """
    Creates a Shelly BLU Remote Control ZB device class.
    """

    display_name = "Shelly BLU Remote Control ZB"
    button_count = 2

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(SupportsOnState=False, SupportsSensorValue=False)
        return props

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super().get_device_state_list()
        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "channel", "Channel", "Channel"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "wheel", "Wheel Steps", "Wheel Steps"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "rotation1", "Rotation 1", "Rotation 1"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "rotation2", "Rotation 2", "Rotation 2"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "rotation3", "Rotation 3", "Rotation 3"
                ),
            ]
        )
        return states

    def get_state_updates(self, data: BLEData) -> list[dict[str, Any]]:
        """
        Build the state updates for a BTHome data packet.
        """
        state_updates = super().get_state_updates(data)

        if (channel := data.sensors.get("channel")) is not None:
            state_updates.append({"key": "channel", "value": channel})

        # Magic wand angles, one rotation object per axis
        for index in (1, 2, 3):
            if (rotation := data.sensors.get(f"rotation_{index}")) is not None:
                state_updates.append({"key": f"rotation{index}", "value": rotation})

        # Wheel rotation is an event, so only packets with a rotation update it.
        # Steps are positive when rotated right and negative when rotated left.
        for event_type, properties in data.events.get("dimmer", {}).items():
            steps = (properties or {}).get("steps", 0)
            if event_type == "rotate_left":
                steps = -steps
            state_updates.append({"key": "wheel", "value": steps})

        return state_updates
