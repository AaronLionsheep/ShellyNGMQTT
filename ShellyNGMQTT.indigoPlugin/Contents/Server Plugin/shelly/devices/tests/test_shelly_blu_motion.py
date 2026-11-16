from shelly.devices.ShellyBLUMotion import ShellyBLUMotion


class TestShellyBLUMotion:
    def test_plugin_props(self):
        assert ShellyBLUMotion.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }
