import math
from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU


class ShellyBLUHT(ShellyBLU):
    """
    Creates a Shelly BLU H&T device class.
    """

    display_name = "Shelly BLU H&T"
    button_count = 1

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        props = super().plugin_props()
        props.update(SupportsOnState=False, SupportsSensorValue=True)
        return props

    @classmethod
    def validate_config_ui(cls, values_dict) -> dict[str, str]:
        errors = super().validate_config_ui(values_dict)

        try:
            valid = math.isfinite(
                float(values_dict.get("temp-offset", "").strip() or 0)
            )
        except ValueError:
            valid = False
        if not valid:
            errors["temp-offset"] = "Must be a number."

        return errors

    def update_state_image(self):
        self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super().get_device_state_list()
        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "temperature", "Temperature", "Temperature"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "humidity", "Humidity", "Humidity"
                ),
            ]
        )
        return states

    def process_ble_data(self, data: BLEData):
        """
        Process a BTHome data packet.
        """
        super().process_ble_data(data)
        state_updates = []

        if (temperature := data.sensors.get("temperature")) is not None:
            unit = self.device.pluginProps.get("temp-unit", "F")
            offset = self.get_number_prop("temp-offset") or 0

            # Convert the temperature reading to fahrenheit if desired
            if unit == "F":
                temperature = (9 / 5) * temperature + 32.0

            # Apply a temperature offset after converting units
            temperature += offset

            state_updates.append(
                {
                    "key": "temperature",
                    "value": temperature,
                    "uiValue": f"{temperature:.1f} °{unit}",
                    "decimalPlaces": 1,
                }
            )
            state_updates.append(
                {
                    "key": "sensorValue",
                    "value": temperature,
                    "uiValue": f"{temperature:.1f} °{unit}",
                    "decimalPlaces": 1,
                }
            )

        if (humidity := data.sensors.get("humidity")) is not None:
            state_updates.append(
                {"key": "humidity", "value": humidity, "uiValue": f"{humidity}%"}
            )

        self.device.updateStatesOnServer(state_updates)
