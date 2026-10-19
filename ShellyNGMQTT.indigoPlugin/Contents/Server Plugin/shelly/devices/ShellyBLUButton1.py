import indigo  # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU


class ShellyBLUButton1(ShellyBLU):
    """
    Creates a Shelly BLU Button1 device class.
    """

    display_name = "Shelly BLU Button1"

    def __init__(self, device_id):
        super(ShellyBLUButton1, self).__init__(device_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLUButton1, self).get_device_state_list()
        return states
