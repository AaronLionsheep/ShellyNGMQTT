import indigo # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU, BLEData


class ShellyBLUDoorWindow(ShellyBLU):
    """
    Creates a Shelly BLU Door Window device class.
    """

    display_name = "Shelly BLU Door/Window"

    def __init__(self, device_id):
        super(ShellyBLUDoorWindow, self).__init__(device_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLUDoorWindow, self).get_device_state_list()

        states.extend([
            indigo.activePlugin.getDeviceStateDictForNumberType("illuminance", "Illuminance", "Illuminance"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rotation", "Rotation", "Rotation")
        ])

        return states
    
    def update_state_image(self):
        opened = self.device.states.get('onOffState', False)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped if opened else indigo.kStateImageSel.SensorOff)
    
    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data)
        state_updates = []

        with data.sensor("illuminance") as illuminance:
            state_updates.append({'key': "illuminance", 'value': illuminance})

        with data.sensor("rotation") as rotation:
            state_updates.append({'key': "rotation", 'value': rotation})

        with data.sensor("window") as open:
            is_open = open == 1
            state_updates.append({'key': "onOffState", 'value': is_open, "uiValue": "open" if is_open else "closed"})

        with data.sensor("battery") as battery:
            state_updates.append({'key': "batteryLevel", 'value': battery})

        self.device.updateStatesOnServer(state_updates)