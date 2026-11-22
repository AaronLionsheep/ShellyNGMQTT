from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_motion import ShellyBLUMotion
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    return ShellyBLUMotion.get_state_updates(
        object.__new__(ShellyBLUMotion), make_data(sensors)
    )


class TestShellyBLUMotion:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUMotion.display_name == "Shelly BLU Motion"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUMotion.button_count == 1

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLUMotion, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUMotion.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert ShellyBLUMotion.plugin_props() is not ShellyBLUMotion.plugin_props()


class TestGetStateUpdates:
    def test_includes_base_states(self):
        """The base BLU states are written in the same update as the motion states"""
        keys = [update["key"] for update in get_state_updates({"motion": 1})]
        assert keys == ["pid", "rssi", "address", "onOffState"]

    def test_motion_and_illuminance(self):
        """Motion sets the on state and illuminance is written as reported"""
        state_updates = get_state_updates({"motion": 1, "illuminance": 120})
        assert state_updates[-2:] == [
            {"key": "illuminance", "value": 120},
            {"key": "onOffState", "value": 1},
        ]

    def test_no_motion(self):
        """A motion value of 0 is still written, so the sensor clears"""
        assert {"key": "onOffState", "value": 0} in get_state_updates({"motion": 0})

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
