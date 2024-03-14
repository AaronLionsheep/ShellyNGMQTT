import indigo

from .ShellyBLU import ShellyBLU


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
    
    def process_packet(self, packet: dict):
        """
        Process a BTHome data packet.
        """
        super().process_packet(packet)
    
        state_updates = []

        state_updates.append({'key': "illuminance", 'value': packet.get("illuminance", -1)})
        state_updates.append({'key': "rotation", 'value': packet.get("rotation", -1)})
        state_updates.append({'key': "batteryLevel", 'value': packet.get("battery", 0)})

        is_open = packet.get("window", 0) == 1
        state_updates.append({'key': "onOffState", 'value': is_open})

        self.device.updateStatesOnServer(state_updates)

        self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped if is_open else indigo.kStateImageSel.SensorOff)
    