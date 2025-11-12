import indigo

from .ShellyBLU import ShellyBLU


class ShellyBLUDistance(ShellyBLU):
    """
    Creates a Shelly BLU Distance device class.
    """

    display_name = "Shelly BLU Distance"

    def __init__(self, device_id):
        super(ShellyBLUDistance, self).__init__(device_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLUDistance, self).get_device_state_list()

        states.extend([
            indigo.activePlugin.getDeviceStateDictForBoolTrueFalseType("vibration", "Vibration", "Vibration"),
            indigo.activePlugin.getDeviceStateDictForNumberType("distance", "Distance", "Distance")
        ])

        return states
    
    def process_packet(self, packet: dict):
        """
        Process a BTHome data packet.
        """
        super().process_packet(packet)
    
        state_updates = []

        distance = packet.get("distance_mm", 0)
        distance += int(self.device.pluginProps.get("offset", 0))

        state_updates.append({'key': "vibration", 'value': packet.get("vibration", 0) == 1})
        state_updates.append({'key': "distance", 'value': distance, 'uiValue': f"{distance} mm"})
        state_updates.append({'key': "batteryLevel", 'value': packet.get("battery", 0)})

        if self.device.pluginProps.get("measure-contents-level"):
            container_height = self.device.pluginProps.get("measure-contents-level-container-height", 0)
            sensor_height = self.device.pluginProps.get("measure-contents-level-sensor-height", 0)            

            contents_height = sensor_height - distance
            contents_level = round(contents_height / container_height * 100)

            state_updates.append({'key': "sensorValue", 'value': contents_level, 'uiValue': f"{contents_level}%"})
        else:
            state_updates.append({'key': "sensorValue", 'value': distance, 'uiValue': f"{distance} mm"})

        self.device.updateStatesOnServer(state_updates)    