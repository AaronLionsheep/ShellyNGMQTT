from shelly.devices.ShellyBLUDoorWindow import ShellyBLUDoorWindow


class TestShellyBLUDoorWindow:
    def test_plugin_props(self):
        assert ShellyBLUDoorWindow.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }
