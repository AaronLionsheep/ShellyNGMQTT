from shelly.devices.shelly_blu_rc_button_4 import ShellyBLURCButton4
from shelly.devices.shelly_blu_rc_button_4_zb import ShellyBLURCButton4ZB


class TestShellyBLURCButton4ZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLURCButton4ZB.display_name == "Shelly BLU RC Button 4 ZB"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLURCButton4ZB.button_count == 4

    def test_is_shelly_blu_rc_button_4(self):
        """The ZB variant sends the same BTHome buttons as the RC Button 4"""
        assert issubclass(ShellyBLURCButton4ZB, ShellyBLURCButton4)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLURCButton4ZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert (
            ShellyBLURCButton4ZB.plugin_props()
            is not ShellyBLURCButton4ZB.plugin_props()
        )
