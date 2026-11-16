from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_door_window import ShellyBLUDoorWindow


class TestShellyBLUDoorWindow:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUDoorWindow.display_name == "Shelly BLU Door/Window"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUDoorWindow.button_count == 1

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUDoorWindow, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUDoorWindow.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert (
            ShellyBLUDoorWindow.plugin_props() is not ShellyBLUDoorWindow.plugin_props()
        )
