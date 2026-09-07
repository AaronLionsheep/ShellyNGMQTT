import indigo # pyright: ignore[reportMissingModuleSource]

from .ShellyBLU import ShellyBLU, BLEData


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
    
    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data)    
        state_updates = []

        with data.sensor("battery") as battery:
            state_updates.append({'key': "batteryLevel", 'value': battery})

        self.device.updateStatesOnServer(state_updates)

        # Fire any triggers matching this event for the device associated with the component
        button_event = data.events.get("button")
        if button_event:
            trigger_types = {
                "press": "single-push",
                "double_press": "double-push",
                "triple_press": "triple-push",
                "long_press": "long-push"
            }

            if button_event in trigger_types:
                trigger_type = trigger_types[button_event]
                for trigger in indigo.activePlugin.triggers.values():
                    if trigger.pluginTypeId == trigger_type and int(trigger.pluginProps.get('device-id', -1)) == self.device.id:
                        indigo.trigger.execute(trigger)