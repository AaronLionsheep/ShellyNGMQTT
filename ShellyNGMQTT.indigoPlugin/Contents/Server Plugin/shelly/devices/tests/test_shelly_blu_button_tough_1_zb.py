from shelly.devices.shelly_blu_button1 import ShellyBLUButton1
from shelly.devices.shelly_blu_button_tough_1_zb import ShellyBLUButtonTough1ZB


class TestShellyBLUButtonTough1ZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUButtonTough1ZB.display_name == "Shelly BLU Button Tough 1 ZB"

    def test_is_shelly_blu_button1(self):
        """Behaves exactly like the BLU Button1, so it inherits its buttons and props"""
        assert issubclass(ShellyBLUButtonTough1ZB, ShellyBLUButton1)

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUButtonTough1ZB.button_count == 1

    def test_plugin_props(self):
        """Same props as the BLU Button1: battery level, no on state or sensor value"""
        assert ShellyBLUButtonTough1ZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }
