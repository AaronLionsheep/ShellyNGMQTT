import logging

import pytest
from shelly.devices.shelly_blu_door_window import ShellyBLUDoorWindow
from shelly.devices.shelly_blu_door_window_zb import LightLevel, ShellyBLUDoorWindowZB
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    shelly = object.__new__(ShellyBLUDoorWindowZB)
    shelly.logger = logging.getLogger("Plugin.ShellyNGMQTT")
    return shelly.get_state_updates(make_data(sensors))


class TestShellyBLUDoorWindowZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUDoorWindowZB.display_name == "Shelly BLU Door/Window ZB"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUDoorWindowZB.button_count == 1

    def test_is_shelly_blu_door_window(self):
        """Window, rotation, and state image handling are shared with the BLU Door/Window"""
        assert issubclass(ShellyBLUDoorWindowZB, ShellyBLUDoorWindow)

    def test_plugin_props(self):
        """Base ShellyBLU props plus the model's on state and sensor value support"""
        assert ShellyBLUDoorWindowZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }


class TestGetStateUpdates:
    def test_includes_door_window_states(self):
        """The base BLU and Door/Window states are written with the light level"""
        state_updates = get_state_updates(
            {"window": True, "rotation": 12.5, "light_level": 2}
        )
        assert [update["key"] for update in state_updates] == [
            "pid",
            "rssi",
            "address",
            "rotation",
            "onOffState",
            "lightLevel",
        ]
        assert state_updates[-3:-1] == [
            {"key": "rotation", "value": 12.5},
            {"key": "onOffState", "value": True, "uiValue": "open"},
        ]

    @pytest.mark.parametrize(
        ("level", "value", "ui_value"),
        [(0, "dark", "Dark"), (1, "twilight", "Twilight"), (2, "bright", "Bright")],
    )
    def test_light_level(self, level, value, ui_value):
        """Each level is written as the enumeration value Indigo triggers match on"""
        assert get_state_updates({"light_level": level})[-1] == {
            "key": "lightLevel",
            "value": value,
            "uiValue": ui_value,
        }

    def test_light_levels(self):
        """The enumeration matches the three levels Shelly documents for object 0x64"""
        assert {level.value: level.name for level in LightLevel} == {
            0: "DARK",
            1: "TWILIGHT",
            2: "BRIGHT",
        }

    def test_unknown_light_level(self, caplog):
        """An unknown level is skipped and logged, since the enumeration can't hold it"""
        updates = get_state_updates({"light_level": 3})
        assert "lightLevel" not in [update["key"] for update in updates]
        assert "Unknown light level 3" in caplog.text

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
