from shelly.devices.ShellyBLURCButton4 import ShellyBLURCButton4


class TestShellyBLURCButton4:
    def test_plugin_props(self):
        assert ShellyBLURCButton4.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }
