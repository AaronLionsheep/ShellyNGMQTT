import indigo  # pyright: ignore[reportMissingModuleSource]
import pytest

ERROR = "Must be a positive number of seconds."


class TestGetPrefsConfigUiValues:
    def test_missing_ble_ages_show_defaults(self, plugin):
        """Preferences saved before the BLE ages existed (ex: after an upgrade)"""
        values_dict, errors = plugin.get_prefs_config_ui_values()

        assert values_dict["ble-max-packet-age"] == "60"
        assert values_dict["ble-max-event-age"] == "3"
        assert errors == {}

    @pytest.mark.indigo_plugin_prefs(
        {"ble-max-packet-age": "", "ble-max-event-age": "  "}
    )
    def test_blank_ble_ages_show_defaults(self, plugin):
        values_dict, _ = plugin.get_prefs_config_ui_values()

        assert values_dict["ble-max-packet-age"] == "60"
        assert values_dict["ble-max-event-age"] == "3"

    @pytest.mark.indigo_plugin_prefs(
        {"ble-max-packet-age": "30", "ble-max-event-age": "1.5"}
    )
    def test_saved_ble_ages_kept(self, plugin):
        values_dict, _ = plugin.get_prefs_config_ui_values()

        assert values_dict["ble-max-packet-age"] == "30"
        assert values_dict["ble-max-event-age"] == "1.5"

    @pytest.mark.indigo_plugin_prefs({"log-level": "debug"})
    def test_other_prefs_kept(self, plugin):
        values_dict, _ = plugin.get_prefs_config_ui_values()

        assert values_dict["log-level"] == "debug"


class TestValidatePrefsConfigUi:
    @staticmethod
    def validate(plugin, **values):
        """Validate the preferences UI with the given BLE age values."""
        return plugin.validate_prefs_config_ui(
            indigo.Dict(
                {
                    "ble-max-packet-age": values.get("packet_age", "60"),
                    "ble-max-event-age": values.get("event_age", "3"),
                }
            )
        )

    @pytest.mark.parametrize("age", ["60", "3", "0.5", "1e3", " 5 "])
    def test_valid_ble_ages(self, plugin, age):
        is_valid, values_dict, errors = self.validate(
            plugin, packet_age=age, event_age=age
        )

        assert is_valid
        assert values_dict["ble-max-packet-age"] == age
        assert values_dict["ble-max-event-age"] == age
        assert errors == {}

    @pytest.mark.parametrize("age", ["", "   "])
    def test_blank_ble_ages_save_defaults(self, plugin, age):
        is_valid, values_dict, errors = self.validate(
            plugin, packet_age=age, event_age=age
        )

        assert is_valid
        assert values_dict["ble-max-packet-age"] == "60"
        assert values_dict["ble-max-event-age"] == "3"
        assert errors == {}

    def test_missing_ble_ages_save_defaults(self, plugin):
        is_valid, values_dict, errors = plugin.validate_prefs_config_ui(indigo.Dict())

        assert is_valid
        assert values_dict["ble-max-packet-age"] == "60"
        assert values_dict["ble-max-event-age"] == "3"
        assert errors == {}

    @pytest.mark.parametrize("age", ["abc", "0", "-1", "-0.5", "nan", "1,5", "5s"])
    def test_invalid_packet_age(self, plugin, age):
        is_valid, values_dict, errors = self.validate(plugin, packet_age=age)

        assert not is_valid
        assert errors == {"ble-max-packet-age": ERROR}
        assert values_dict["ble-max-packet-age"] == age

    @pytest.mark.parametrize("age", ["abc", "0", "-1", "-0.5", "nan", "1,5", "5s"])
    def test_invalid_event_age(self, plugin, age):
        is_valid, values_dict, errors = self.validate(plugin, event_age=age)

        assert not is_valid
        assert errors == {"ble-max-event-age": ERROR}
        assert values_dict["ble-max-event-age"] == age

    def test_both_invalid(self, plugin):
        is_valid, _, errors = self.validate(plugin, packet_age="abc", event_age="0")

        assert not is_valid
        assert errors == {"ble-max-packet-age": ERROR, "ble-max-event-age": ERROR}

    def test_returns_values_dict(self, plugin):
        values = indigo.Dict({"ble-max-packet-age": "60", "ble-max-event-age": "3"})

        _, values_dict, _ = plugin.validate_prefs_config_ui(values)

        assert values_dict is values
