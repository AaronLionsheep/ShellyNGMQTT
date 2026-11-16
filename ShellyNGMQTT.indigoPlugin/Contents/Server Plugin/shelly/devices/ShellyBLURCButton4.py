from typing import Any

import indigo  # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU


class ShellyBLURCButton4(ShellyBLU):
    """
    Creates a Shelly BLU RC Button 4 device class.
    """

    display_name = "Shelly BLU RC Button 4"
    button_count = 4

    def __init__(self, device_id):
        super().__init__(device_id)

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
        return states
