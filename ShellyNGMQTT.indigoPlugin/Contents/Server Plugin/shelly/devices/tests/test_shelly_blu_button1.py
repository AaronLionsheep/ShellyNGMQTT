from shelly.devices.ShellyBLU import ShellyBLU
from shelly.devices.ShellyBLUButton1 import ShellyBLUButton1


class TestShellyBLUButton1:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUButton1.display_name == "Shelly BLU Button1"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUButton1.button_count == 1

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUButton1, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUButton1.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert ShellyBLUButton1.plugin_props() is not ShellyBLUButton1.plugin_props()
