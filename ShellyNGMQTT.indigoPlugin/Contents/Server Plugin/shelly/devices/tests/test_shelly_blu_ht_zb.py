from shelly.devices.shelly_blu_ht import ShellyBLUHT
from shelly.devices.shelly_blu_ht_zb import ShellyBLUHTZB


class TestShellyBLUHTZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUHTZB.display_name == "Shelly BLU H&T ZB"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUHTZB.button_count == 1

    def test_is_shelly_blu_ht(self):
        """It broadcasts the same BTHome data as the BLU H&T, so it shares its logic"""
        assert issubclass(ShellyBLUHTZB, ShellyBLUHT)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUHTZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }

    def test_validate_config_ui(self):
        """The temperature offset is validated like the BLU H&T's"""
        assert ShellyBLUHTZB.validate_config_ui({"temp-offset": "1.5"}) == {}
        assert ShellyBLUHTZB.validate_config_ui({"temp-offset": "abc"}) == {
            "temp-offset": "Must be a number."
        }
