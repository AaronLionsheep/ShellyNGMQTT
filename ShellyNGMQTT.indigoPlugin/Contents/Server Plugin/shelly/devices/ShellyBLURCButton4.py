import indigo # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU, BLEData


class ShellyBLURCButton4(ShellyBLU):
    """
    Creates a Shelly BLU RC Button 4 device class.
    """

    display_name = "Shelly BLU RC Button 4"
    button_count = 4

    def __init__(self, device_id):
        super(ShellyBLURCButton4, self).__init__(device_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLURCButton4, self).get_device_state_list()
        return states
    
    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data) 
        state_updates = []

        if (battery := data.sensors.get("battery")) is not None:
            state_updates.append({'key': "batteryLevel", 'value': battery})

        self.device.updateStatesOnServer(state_updates)