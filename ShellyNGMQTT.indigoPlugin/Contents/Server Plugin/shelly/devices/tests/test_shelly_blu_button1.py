from shelly.devices.ShellyBLUButton1 import ShellyBLUButton1


class TestShellyBLUButton1:
    def test_plugin_props(self):
        assert ShellyBLUButton1.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }
