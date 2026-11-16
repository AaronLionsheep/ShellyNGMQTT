from typing import Any

from .ShellyBLU import ShellyBLU


class ShellyBLURCButton4(ShellyBLU):
    """
    Creates a Shelly BLU RC Button 4 device class.
    """

    display_name = "Shelly BLU RC Button 4"
    button_count = 4

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(SupportsOnState=False, SupportsSensorValue=False)
        return props
