import pytest
from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_distance import ShellyBLUDistance

OFFSET_ERROR = "Must be a whole number of mm."
CONTAINER_ERROR = "Must be a whole number of mm greater than 0."
SENSOR_ERROR = "Must be a whole number of mm."
CONTAINER = "measure-contents-level-container-height"
SENSOR = "measure-contents-level-sensor-height"


class TestShellyBLUDistance:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUDistance.display_name == "Shelly BLU Distance"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUDistance.button_count == 1

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUDistance, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUDistance.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert ShellyBLUDistance.plugin_props() is not ShellyBLUDistance.plugin_props()


class TestValidateConfigUi:
    @staticmethod
    def level(container="1000", sensor="1000", **values):
        """Settings with Measure Level on and the given heights"""
        return {
            "measure-contents-level": True,
            CONTAINER: container,
            SENSOR: sensor,
            **values,
        }

    @pytest.mark.parametrize("offset", ["0", "10", "-25", " 5 ", "", "   "])
    def test_valid_offset(self, offset):
        """Whole and blank (no adjustment) offsets are accepted"""
        assert ShellyBLUDistance.validate_config_ui({"offset": offset}) == {}

    def test_missing_values(self):
        """Settings without an offset or Measure Level (ex: older devices) are valid"""
        assert ShellyBLUDistance.validate_config_ui({}) == {}

    @pytest.mark.parametrize("offset", ["abc", "1.5", "1e2", "5mm", "nan"])
    def test_invalid_offset(self, offset):
        """Distances are whole mm, so the offset must be too"""
        assert ShellyBLUDistance.validate_config_ui({"offset": offset}) == {
            "offset": OFFSET_ERROR
        }

    @pytest.mark.parametrize("measure", [False, ""])
    def test_heights_ignored_without_measure_level(self, measure):
        """Hidden height fields don't block saving when the level isn't measured"""
        values = self.level(container="abc", sensor="0.5")
        values["measure-contents-level"] = measure

        assert ShellyBLUDistance.validate_config_ui(values) == {}

    @pytest.mark.parametrize(
        ("container", "sensor"),
        [
            ("1000", "1000"),
            ("1", "0"),
            ("500", "750"),
            (" 300 ", " 300 "),
            ("10", "-5"),
        ],
    )
    def test_valid_heights(self, container, sensor):
        """Any positive container height and whole sensor height can measure the level"""
        values = self.level(container=container, sensor=sensor)

        assert ShellyBLUDistance.validate_config_ui(values) == {}

    @pytest.mark.parametrize("container", ["0", "-1", "", "  ", "abc", "1.5", "1e3"])
    def test_invalid_container_height(self, container):
        """The level divides by the container height, so it must be a positive whole number"""
        values = self.level(container=container)

        assert ShellyBLUDistance.validate_config_ui(values) == {
            CONTAINER: CONTAINER_ERROR
        }

    def test_missing_container_height(self):
        """Turning on Measure Level without entering a container height is an error"""
        values = self.level()
        del values[CONTAINER]

        assert ShellyBLUDistance.validate_config_ui(values) == {
            CONTAINER: CONTAINER_ERROR
        }

    @pytest.mark.parametrize("sensor", ["", "  ", "abc", "1.5", "1e3"])
    def test_invalid_sensor_height(self, sensor):
        """The level is measured from the sensor height, so it must be a whole number"""
        values = self.level(sensor=sensor)

        assert ShellyBLUDistance.validate_config_ui(values) == {SENSOR: SENSOR_ERROR}

    def test_missing_sensor_height(self):
        """Turning on Measure Level without entering a sensor height is an error"""
        values = self.level()
        del values[SENSOR]

        assert ShellyBLUDistance.validate_config_ui(values) == {SENSOR: SENSOR_ERROR}

    def test_all_invalid(self):
        """Every invalid field is reported together so they can be fixed at once"""
        values = self.level(container="0", sensor="abc", offset="1.5")

        assert ShellyBLUDistance.validate_config_ui(values) == {
            "offset": OFFSET_ERROR,
            CONTAINER: CONTAINER_ERROR,
            SENSOR: SENSOR_ERROR,
        }
