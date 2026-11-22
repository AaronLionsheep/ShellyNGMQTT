from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU


class ShellyBLUMotion(ShellyBLU):
    """
    Creates a Shelly BLU Motion device class.
    """

    display_name = "Shelly BLU Motion"
    button_count = 1

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(
            SupportsOnState=True,
            SupportsSensorValue=False,
        )
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
                )
            ]
        )
        return states

    def get_state_updates(self, data: BLEData) -> list[dict[str, Any]]:
        """
        Build the state updates for a BTHome data packet.
        """
        state_updates = super().get_state_updates(data)

        if (illuminance := data.sensors.get("illuminance")) is not None:
            state_updates.append({"key": "illuminance", "value": illuminance})

        if (motion := data.sensors.get("motion")) is not None:
            state_updates.append({"key": "onOffState", "value": motion})

        return state_updates

    def update_state_image(self):
        motion = self.device.states.get("onOffState", False)
        image = (
            indigo.kStateImageSel.MotionSensorTripped
            if motion
            else indigo.kStateImageSel.MotionSensor
        )
        self.device.updateStateImageOnServer(image)
