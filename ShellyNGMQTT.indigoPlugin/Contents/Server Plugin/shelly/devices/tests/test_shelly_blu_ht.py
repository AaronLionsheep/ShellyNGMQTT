from shelly.devices.ShellyBLUHT import ShellyBLUHT


class TestShellyBLUHT:
    def test_plugin_props(self):
        assert ShellyBLUHT.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }
