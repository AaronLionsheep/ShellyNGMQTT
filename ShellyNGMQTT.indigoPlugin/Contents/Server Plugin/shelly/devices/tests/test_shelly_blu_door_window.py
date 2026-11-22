import pytest
from shelly.devices.shelly_blu import ShellyBLU
from shelly.devices.shelly_blu_door_window import ShellyBLUDoorWindow
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    return ShellyBLUDoorWindow.get_state_updates(
        object.__new__(ShellyBLUDoorWindow), make_data(sensors)
    )


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


class TestGetStateUpdates:
    def test_includes_base_states(self):
        """The base BLU states are written in the same update as the window states"""
        keys = [update["key"] for update in get_state_updates({"window": 1})]
        assert keys == ["pid", "rssi", "address", "onOffState"]

    @pytest.mark.parametrize(
        ("window", "is_open", "ui_value"),
        [
            pytest.param(1, True, "open", id="open"),
            pytest.param(0, False, "closed", id="closed"),
        ],
    )
    def test_window(self, window, is_open, ui_value):
        """The window sensor sets the on state, shown as open or closed"""
        assert get_state_updates({"window": window})[-1] == {
            "key": "onOffState",
            "value": is_open,
            "uiValue": ui_value,
        }

    def test_illuminance_and_rotation(self):
        """Illuminance and rotation are written as reported"""
        state_updates = get_state_updates({"illuminance": 120, "rotation": 45.5})
        assert state_updates[-2:] == [
            {"key": "illuminance", "value": 120},
            {"key": "rotation", "value": 45.5},
        ]

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
