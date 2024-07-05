import indigo

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

        states.extend([
            indigo.activePlugin.getDeviceStateDictForNumberType("button", "Button Press", "Button Press")
        ])

        return states
    
    def process_packet(self, packet: dict):
        """
        Process a BTHome data packet.
        """
        super().process_packet(packet)
    
        state_updates = []

        state_updates.append({'key': "button", 'value': packet.get("button", -1)})
        state_updates.append({'key': "batteryLevel", 'value': packet.get("battery", 0)})

        self.device.updateStatesOnServer(state_updates)

        # Fire any triggers matching this event for the device associated with the component
        try:
            trigger_type = ["single-push", "double-push", "triple-push", "long-push"][packet.get("button", -999) - 1]
            for trigger in indigo.activePlugin.triggers.values():
                if trigger.pluginTypeId == trigger_type and int(trigger.pluginProps.get('device-id', -1)) == self.device.id:
                    indigo.trigger.execute(trigger)
        except IndexError:
            self.logger.error(f"Unknown button event for button value: {packet.get('button', -1)}")