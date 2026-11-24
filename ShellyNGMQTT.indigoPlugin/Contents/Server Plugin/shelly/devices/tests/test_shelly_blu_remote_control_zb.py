from dataclasses import replace

from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_remote_control_zb import ShellyBLURemoteControlZB
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict, events: dict | None = None) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    return ShellyBLURemoteControlZB.get_state_updates(
        object.__new__(ShellyBLURemoteControlZB),
        replace(make_data(sensors), events=events or {}),
    )


class TestShellyBLURemoteControlZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLURemoteControlZB.display_name == "Shelly BLU Remote Control ZB"

    def test_button_count(self):
        """Both ring buttons are offered when configuring button triggers"""
        assert ShellyBLURemoteControlZB.button_count == 2

    def test_is_shelly_blu(self):
        """BLE packets and MAC address handling are routed to ShellyBLU subclasses"""
        assert issubclass(ShellyBLURemoteControlZB, ShellyBLU)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLURemoteControlZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    def test_plugin_props_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert (
            ShellyBLURemoteControlZB.plugin_props()
            is not ShellyBLURemoteControlZB.plugin_props()
        )


class TestGetStateUpdates:
    def test_includes_base_states(self):
        """The base BLU states are written in the same update as the remote's states"""
        keys = [update["key"] for update in get_state_updates({"channel": 0})]
        assert keys == ["pid", "rssi", "address", "channel"]

    def test_channel(self):
        """The active channel is written as reported, including channel 0"""
        assert {"key": "channel", "value": 0} in get_state_updates({"channel": 0})
        assert {"key": "channel", "value": 3} in get_state_updates({"channel": 3})

    def test_rotations(self):
        """Each magic wand rotation object is written to its own numbered state"""
        state_updates = get_state_updates(
            {"rotation_1": 1.6, "rotation_2": -3.2, "rotation_3": 0.0}
        )
        assert state_updates[-3:] == [
            {"key": "rotation1", "value": 1.6},
            {"key": "rotation2", "value": -3.2},
            {"key": "rotation3", "value": 0.0},
        ]

    def test_partial_rotations(self):
        """Firmware sending fewer rotation objects only updates the ones it sends"""
        keys = [
            update["key"]
            for update in get_state_updates({"rotation_1": 1.0, "rotation_2": 2.0})
        ]
        assert keys[-2:] == ["rotation1", "rotation2"]
        assert "rotation3" not in keys

    def test_wheel_rotate_right(self):
        """Turning the wheel right writes a positive step count"""
        state_updates = get_state_updates(
            {}, {"dimmer": {"rotate_right": {"steps": 3}}}
        )
        assert state_updates[-1] == {"key": "wheel", "value": 3}

    def test_wheel_rotate_left(self):
        """Turning the wheel left writes a negative step count"""
        state_updates = get_state_updates({}, {"dimmer": {"rotate_left": {"steps": 5}}})
        assert state_updates[-1] == {"key": "wheel", "value": -5}

    def test_wheel_missing_steps(self):
        """A wheel event without step properties writes 0 instead of failing"""
        state_updates = get_state_updates({}, {"dimmer": {"rotate_right": None}})
        assert state_updates[-1] == {"key": "wheel", "value": 0}

    def test_button_event_does_not_update_wheel(self):
        """Button presses leave the wheel state unchanged"""
        keys = [
            update["key"]
            for update in get_state_updates(
                {"channel": 1}, {"button_1": {"press": None}}
            )
        ]
        assert "wheel" not in keys

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
