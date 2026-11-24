from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_wall_switch_4 import ShellyBLUWallSwitch4


class TestShellyBLUWallSwitch4:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUWallSwitch4.display_name == "Shelly BLU Wall Switch 4"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUWallSwitch4.button_count == 4

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUWallSwitch4, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUWallSwitch4.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert (
            ShellyBLUWallSwitch4.plugin_props()
            is not ShellyBLUWallSwitch4.plugin_props()
        )
