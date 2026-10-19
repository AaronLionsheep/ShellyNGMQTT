import indigo # pyright: ignore[reportMissingModuleSource]

from typing import Any

from .ShellyBLU import ShellyBLU, BLEData


class ShellyBLUMotion(ShellyBLU):
    """
    Creates a Shelly BLU Motion device class.
    """

    display_name = "Shelly BLU Motion"

    def __init__(self, device_id):
        super(ShellyBLUMotion, self).__init__(device_id)

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(
			SupportsBatteryLevel=True,
            SupportsOnState=True,
            SupportsStatusRequest=False,
            SupportsSensorValue=False
        )
        return props

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLUMotion, self).get_device_state_list()

        states.extend([
            indigo.activePlugin.getDeviceStateDictForNumberType("illuminance", "Illuminance", "Illuminance")
        ])

        return states
    
    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data) 
        state_updates = []

        if (illuminance := data.sensors.get("illuminance")) is not None:
            state_updates.append({'key': "illuminance", 'value': illuminance})

        if (motion := data.sensors.get("motion")) is not None:
            state_updates.append({'key': "onOffState", 'value': motion})

        self.device.updateStatesOnServer(state_updates)

    def update_state_image(self):
        motion = self.device.states.get('onOffState', False)
        image = indigo.kStateImageSel.MotionSensorTripped if motion else indigo.kStateImageSel.MotionSensor
        self.device.updateStateImageOnServer(image)
