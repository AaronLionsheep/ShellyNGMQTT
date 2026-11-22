from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from .shelly_blu import BLEData, ShellyBLU


class ShellyBLUDistance(ShellyBLU):
    """
    Creates a Shelly BLU Distance device class.
    """

    display_name = "Shelly BLU Distance"
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
            int(values_dict.get("offset", "").strip() or 0)
        except ValueError:
            errors["offset"] = "Must be a whole number of mm."

        if values_dict.get("measure-contents-level"):
            key = "measure-contents-level-container-height"
            try:
                valid = int(values_dict.get(key, "")) > 0
            except ValueError:
                valid = False
            if not valid:
                errors[key] = "Must be a whole number of mm greater than 0."

            key = "measure-contents-level-sensor-height"
            try:
                int(values_dict.get(key, ""))
            except ValueError:
                errors[key] = "Must be a whole number of mm."

        return errors

    def get_device_state_list(self):
        """
        Build the device state list for the device.
        """
        states = super().get_device_state_list()
        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForBoolTrueFalseType(
                    "vibration", "Vibration", "Vibration"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "distance", "Distance", "Distance"
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

        if (distance := data.sensors.get("distance")) is not None:
            distance += self.get_number_prop("offset", int) or 0
            state_updates.append(
                {"key": "distance", "value": distance, "uiValue": f"{distance} mm"}
            )

            container_height = sensor_height = None
            if self.device.pluginProps.get("measure-contents-level"):
                container_height = self.get_number_prop(
                    "measure-contents-level-container-height", int, minimum=1
                )
                sensor_height = self.get_number_prop(
                    "measure-contents-level-sensor-height", int
                )

            # Report the distance when the level can't be calculated
            if container_height is not None and sensor_height is not None:
                contents_height = sensor_height - distance
                contents_level = round(contents_height / container_height * 100)

                state_updates.append(
                    {
                        "key": "sensorValue",
                        "value": contents_level,
                        "uiValue": f"{contents_level}%",
                    }
                )
            else:
                state_updates.append(
                    {
                        "key": "sensorValue",
                        "value": distance,
                        "uiValue": f"{distance} mm",
                    }
                )

        if (vibration := data.sensors.get("vibration")) is not None:
            state_updates.append({"key": "vibration", "value": vibration == 1})

        self.device.updateStatesOnServer(state_updates)
