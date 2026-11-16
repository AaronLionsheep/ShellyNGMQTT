from typing import Any

import indigo  # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU


class ShellyBLUButton1(ShellyBLU):
    """
    Creates a Shelly BLU Button1 device class.
    """

    display_name = "Shelly BLU Button1"
    button_count = 1

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(SupportsOnState=False, SupportsSensorValue=False)
        return props
