import logging

import pytest
from shelly.devices.shelly_blu_motion import ShellyBLUMotion
from shelly.devices.shelly_blu_motion_zb import LightLevel, ShellyBLUMotionZB
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    shelly = object.__new__(ShellyBLUMotionZB)
    shelly.logger = logging.getLogger("Plugin.ShellyNGMQTT")
    return shelly.get_state_updates(make_data(sensors))


class TestShellyBLUMotionZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUMotionZB.display_name == "Shelly BLU Motion ZB"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUMotionZB.button_count == 1

    def test_is_shelly_blu_motion(self):
        """Motion handling and the motion state image are shared with the BLU Motion"""
        assert issubclass(ShellyBLUMotionZB, ShellyBLUMotion)

    def test_plugin_props(self):
        """Same props as the BLU Motion: on state for motion and no sensor value"""
        assert ShellyBLUMotionZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": True,
            "SupportsSensorValue": False,
        }


class TestGetStateUpdates:
    def test_includes_base_states(self):
        """The base BLU states are written in the same update as the motion states"""
        keys = [update["key"] for update in get_state_updates({"motion": 1})]
        assert keys == ["pid", "rssi", "address", "onOffState"]

    def test_motion_and_light_level(self):
        """Motion and light level are written in the same update"""
        keys = [
            update["key"]
            for update in get_state_updates({"motion": 1, "light_level": 0})
        ]
        assert keys[-2:] == ["onOffState", "lightLevel"]

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

    def test_no_motion(self):
        """A motion value of 0 is still written, so the sensor clears"""
        assert {"key": "onOffState", "value": 0} in get_state_updates({"motion": 0})

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
