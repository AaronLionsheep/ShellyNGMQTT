import pytest
from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_ht import ShellyBLUHT


class TestShellyBLUHT:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUHT.display_name == "Shelly BLU H&T"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUHT.button_count == 1

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUHT, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUHT.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert ShellyBLUHT.plugin_props() is not ShellyBLUHT.plugin_props()


class TestValidateConfigUi:
    @pytest.mark.parametrize(
        "offset", ["0", "1", "-2", "1.5", "-0.25", "1e1", " 3 ", "", "   "]
    )
    def test_valid_temp_offset(self, offset):
        """Whole, decimal, and blank (no adjustment) offsets are accepted"""
        assert ShellyBLUHT.validate_config_ui({"temp-offset": offset}) == {}

    def test_missing_temp_offset(self):
        """Settings without an offset (ex: created before it existed) are valid"""
        assert ShellyBLUHT.validate_config_ui({}) == {}

    @pytest.mark.parametrize(
        "offset", ["abc", "1,5", "2F", "--1", "nan", "inf", "-inf"]
    )
    def test_invalid_temp_offset(self, offset):
        """Offsets that would fail or corrupt every temperature reading are rejected"""
        assert ShellyBLUHT.validate_config_ui({"temp-offset": offset}) == {
            "temp-offset": "Must be a number."
        }

    def test_other_values_ignored(self):
        """Only the offset is validated, since the unit is picked from a menu"""
        assert ShellyBLUHT.validate_config_ui({"temp-unit": "abc"}) == {}
