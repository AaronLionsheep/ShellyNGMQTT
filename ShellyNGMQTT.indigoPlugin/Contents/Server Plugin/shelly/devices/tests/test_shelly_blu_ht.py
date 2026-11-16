from shelly.devices.ShellyBLU import ShellyBLU
from shelly.devices.ShellyBLUHT import ShellyBLUHT


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
