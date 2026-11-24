import logging

import pytest
from shelly.devices.shelly_blu_ht import ShellyBLUHT
from shelly.devices.shelly_blu_ht_display_zb import LightLevel, ShellyBLUHTDisplayZB
from shelly.devices.tests.test_shelly_blu import make_data


def get_state_updates(sensors: dict) -> list[dict]:
    # Skip __init__, which looks up the Indigo device
    shelly = object.__new__(ShellyBLUHTDisplayZB)
    shelly.logger = logging.getLogger("Plugin.ShellyNGMQTT")
    return shelly.get_state_updates(make_data(sensors))


class TestShellyBLUHTDisplayZB:
    def test_display_name(self):
        """Display name matches the Devices.xml label used for the device model"""
        assert ShellyBLUHTDisplayZB.display_name == "Shelly BLU H&T Display ZB"

    def test_button_count(self):
        """Number of buttons offered when configuring button triggers"""
        assert ShellyBLUHTDisplayZB.button_count == 1

    def test_is_shelly_blu_ht(self):
        """Temperature, humidity and settings validation are shared with the BLU H&T"""
        assert issubclass(ShellyBLUHTDisplayZB, ShellyBLUHT)

    def test_plugin_props(self):
        """Same props as the BLU H&T: a sensor value and no on state"""
        assert ShellyBLUHTDisplayZB.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsBatteryLevel": True,
            "SupportsOnState": False,
            "SupportsSensorValue": True,
        }

    def test_validate_config_ui(self):
        """The temperature offset is validated like the BLU H&T's"""
        assert ShellyBLUHTDisplayZB.validate_config_ui({"temp-offset": "abc"}) == {
            "temp-offset": "Must be a number."
        }


class TestGetStateUpdates:
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
        updates = get_state_updates({"light_level": 7})
        assert "lightLevel" not in [update["key"] for update in updates]
        assert "Unknown light level 7" in caplog.text

    @pytest.mark.parametrize("light", [True, False])
    def test_light_detected(self, light):
        """Light detected is written both when light is and isn't detected"""
        assert {"key": "light", "value": light} in get_state_updates({"light": light})

    def test_humidity_and_light(self):
        """Inherited H&T states are written in the same update as the light states"""
        keys = [
            update["key"]
            for update in get_state_updates(
                {"humidity": 50, "light": True, "light_level": 2}
            )
        ]
        assert keys == ["pid", "rssi", "address", "humidity", "light", "lightLevel"]

    def test_missing_sensors(self):
        """Sensors not in the packet are not written, keeping their previous values"""
        keys = [update["key"] for update in get_state_updates({})]
        assert keys == ["pid", "rssi", "address"]
