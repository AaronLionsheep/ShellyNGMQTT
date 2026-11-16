from shelly.devices.ShellyBLUDistance import ShellyBLUDistance


class TestShellyBLUDistance:
    def test_plugin_props(self):
        assert ShellyBLUDistance.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }
