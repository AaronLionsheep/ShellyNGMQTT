from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU


class ShellyBLUDoorWindow(ShellyBLU):
    """
    Creates a Shelly BLU Door Window device class.
    """

    display_name = "Shelly BLU Door/Window"
    button_count = 1

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(SupportsOnState=True, SupportsSensorValue=False)
        return props

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super().get_device_state_list()
        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "illuminance", "Illuminance", "Illuminance"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "rotation", "Rotation", "Rotation"
                ),
            ]
        )
        return states

    def update_state_image(self):
        opened = self.device.states.get("onOffState", False)
        self.device.updateStateImageOnServer(
            indigo.kStateImageSel.SensorTripped
            if opened
            else indigo.kStateImageSel.SensorOff
        )

    def get_state_updates(self, data: BLEData) -> list[dict[str, Any]]:
        """
        Build the state updates for a BTHome data packet.
        """
        state_updates = super().get_state_updates(data)

        if (illuminance := data.sensors.get("illuminance")) is not None:
            state_updates.append({"key": "illuminance", "value": illuminance})

        if (rotation := data.sensors.get("rotation")) is not None:
            state_updates.append({"key": "rotation", "value": rotation})

        if (window := data.sensors.get("window")) is not None:
            is_open = window == 1
            state_updates.append(
                {
                    "key": "onOffState",
                    "value": is_open,
                    "uiValue": "open" if is_open else "closed",
                }
            )

        return state_updates
