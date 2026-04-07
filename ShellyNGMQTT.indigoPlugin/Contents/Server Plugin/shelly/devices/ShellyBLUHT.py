import indigo # pyright: ignore[reportMissingModuleSource]

from typing import Any

from .ShellyBLU import ShellyBLU, BLEData


class ShellyBLUHT(ShellyBLU):
    """
    Creates a Shelly BLU H&T device class.
    """

    display_name = "Shelly BLU H&T"
    button_count = 1

    def __init__(self, device_id):
        super(ShellyBLUHT, self).__init__(device_id)

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(
            SupportsStatusRequest=False,
			SupportsBatteryLevel=True,
            SupportsOnState=False,
            SupportsSensorValue=True
        )
        return props
    
    def update_state_image(self):
        self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super(ShellyBLUHT, self).get_device_state_list()
        states.extend([
            indigo.activePlugin.getDeviceStateDictForNumberType("temperature", "Temperature", "Temperature"),
            indigo.activePlugin.getDeviceStateDictForNumberType("humidity", "Humidity", "Humidity")
        ])
        return states
    
    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data) 
        state_updates = []

        with data.sensor("battery") as battery:
            state_updates.append({'key': "batteryLevel", 'value': battery})

        with data.sensor("temperature") as temperature:
            unit = self.device.pluginProps.get("temp-unit", "F")
            try:
                offset = float(self.device.pluginProps.get("temp-offset") or 0)
            except TypeError as e:
                self.logger.error(f"'{self.device.name}' has an invalid temperature offset")
                raise e

            # Convert the temperature reading to fahrenheit if desired
            if unit == "F":
                temperature = (9 / 5) * temperature + 32.0

            # Apply a temperature offset after converting units
            temperature += offset

            state_updates.append({'key': "temperature", 'value': temperature, 'uiValue': f"{temperature:.1f} °{unit}", 'decimalPlaces': 1})
            state_updates.append({'key': "sensorValue", 'value': temperature, 'uiValue': f"{temperature:.1f} °{unit}", 'decimalPlaces': 1})  

        with data.sensor("humidity") as humidity:
            state_updates.append({'key': "humidity", 'value': humidity, 'uiValue': f"{humidity}%"})

        self.device.updateStatesOnServer(state_updates)

