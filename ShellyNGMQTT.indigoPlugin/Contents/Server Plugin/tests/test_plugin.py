import logging

import indigo  # pyright: ignore[reportMissingModuleSource]
import plugin as plugin_module
import pytest

ERROR = "Must be a positive number of seconds."
DEVICE_ERROR = "You must select a device."
BUTTON_ERROR = "You must select a button."

DEVICE_EVENTS = [
    "btn-down",
    "btn-up",
    "ota-begin",
    "ota-success",
    "ota-error",
    "sta-connect-fail",
    "sta-disconnected",
    "sleep",
    "scheduled-restart",
]
BUTTON_EVENTS = ["single-push", "double-push", "triple-push", "long-push", "hold-push"]

LOG_LEVELS = [
    ("debug", logging.DEBUG),
    ("info", logging.INFO),
    ("warning", logging.WARNING),
]


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


class TestInit:
    def test_empty_state(self, plugin):
        """No devices, triggers, or messages are tracked until devices start"""
        assert plugin.shellies == {}
        assert plugin.triggers == {}
        assert plugin.message_types == []
        assert plugin.message_queue.empty()
        assert plugin.broker_device_topics == {}
        assert len(plugin.blu_address_devices) == 0

    def test_default_log_level(self, plugin):
        """Preferences saved before the log level existed log at info"""
        assert plugin.indigo_log_handler.level == logging.INFO

    @pytest.mark.parametrize(
        "handler_level",
        [
            pytest.param(
                handler_level,
                marks=pytest.mark.indigo_plugin_prefs({"log-level": level}),
            )
            for level, handler_level in LOG_LEVELS
        ],
    )
    def test_saved_log_level(self, plugin, handler_level):
        """The saved log level is applied when the plugin starts"""
        assert plugin.indigo_log_handler.level == handler_level

    @pytest.mark.indigo_plugin_prefs({"log-level": "verbose"})
    def test_invalid_saved_log_level(self, plugin, caplog):
        """An unknown saved level is reported and logging stays at info"""
        assert plugin.indigo_log_handler.level == logging.INFO
        assert (
            "Plugin",
            logging.ERROR,
            "Attempted to set the log level to an unhandled value: verbose",
        ) in [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records("setup")]


class TestSetLogLevel:
    @pytest.mark.parametrize(("level", "handler_level"), LOG_LEVELS)
    def test_valid_levels(self, plugin, caplog, level, handler_level):
        """Each preference level filters the Indigo event log and confirms the change"""
        plugin.setLogLevel(level)

        assert plugin.indigo_log_handler.level == handler_level
        assert caplog.record_tuples == [
            ("Plugin", handler_level, f"Log level set to {level}")
        ]

    @pytest.mark.parametrize("level", ["verbose", "error", "DEBUG", ""])
    def test_invalid_level_keeps_current_level(self, plugin, caplog, level):
        """An unknown level is reported without changing the current level"""
        plugin.setLogLevel("debug")
        caplog.clear()

        plugin.setLogLevel(level)

        assert plugin.indigo_log_handler.level == logging.DEBUG
        assert caplog.record_tuples == [
            (
                "Plugin",
                logging.ERROR,
                f"Attempted to set the log level to an unhandled value: {level}",
            )
        ]

    def test_only_indigo_log_handler_changes(self, plugin):
        """The plugin log file keeps every level for troubleshooting"""
        file_handler_level = plugin.plugin_file_handler.level

        plugin.setLogLevel("warning")

        assert plugin.plugin_file_handler.level == file_handler_level


class TestClosedPrefsConfigUi:
    @pytest.mark.parametrize(("level", "handler_level"), LOG_LEVELS)
    def test_saved_log_level_applied(self, plugin, level, handler_level):
        """Saving the preferences applies the new log level without a restart"""
        plugin.closedPrefsConfigUi(indigo.Dict({"log-level": level}), False)

        assert plugin.indigo_log_handler.level == handler_level

    @pytest.mark.indigo_plugin_prefs({"log-level": "debug"})
    def test_missing_log_level_uses_info(self, plugin):
        """Preferences saved without a log level fall back to info"""
        plugin.closedPrefsConfigUi(indigo.Dict(), False)

        assert plugin.indigo_log_handler.level == logging.INFO

    def test_cancelled_keeps_log_level(self, plugin):
        """Cancelling the preferences dialog discards the selected log level"""
        plugin.closedPrefsConfigUi(indigo.Dict({"log-level": "debug"}), True)

        assert plugin.indigo_log_handler.level == logging.INFO


class TestValidateEventConfigUi:
    @pytest.mark.parametrize("type_id", DEVICE_EVENTS)
    def test_device_event_with_device(self, plugin, type_id):
        """Device events only need the device that fires them"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict({"device-id": "123"}), type_id, 0
        )

        assert is_valid
        assert errors == {}

    @pytest.mark.parametrize("type_id", DEVICE_EVENTS)
    @pytest.mark.parametrize("values", [{}, {"device-id": ""}])
    def test_device_event_without_device(self, plugin, type_id, values):
        """A device event can't fire without a device selected"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict(values), type_id, 0
        )

        assert not is_valid
        assert errors == {"device-id": DEVICE_ERROR}

    @pytest.mark.parametrize("type_id", BUTTON_EVENTS)
    def test_button_event_with_device_and_button(self, plugin, type_id):
        """Button events need the device and which of its buttons was pushed"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict({"device-id": "123", "button-id": "1"}), type_id, 0
        )

        assert is_valid
        assert errors == {}

    @pytest.mark.parametrize("type_id", BUTTON_EVENTS)
    @pytest.mark.parametrize(
        "values", [{"button-id": "1"}, {"device-id": "", "button-id": "1"}]
    )
    def test_button_event_without_device(self, plugin, type_id, values):
        """A button event can't fire without a device selected"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict(values), type_id, 0
        )

        assert not is_valid
        assert errors == {"device-id": DEVICE_ERROR}

    @pytest.mark.parametrize("type_id", BUTTON_EVENTS)
    @pytest.mark.parametrize(
        "values", [{"device-id": "123"}, {"device-id": "123", "button-id": ""}]
    )
    def test_button_event_without_button(self, plugin, type_id, values):
        """A button event can't fire without knowing which button to watch"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict(values), type_id, 0
        )

        assert not is_valid
        assert errors == {"button-id": BUTTON_ERROR}

    @pytest.mark.parametrize("type_id", BUTTON_EVENTS)
    def test_button_event_without_device_or_button(self, plugin, type_id):
        """Both missing fields are reported together so the user fixes them at once"""
        is_valid, _, errors = plugin.validate_event_config_ui(indigo.Dict(), type_id, 0)

        assert not is_valid
        assert errors == {"device-id": DEVICE_ERROR, "button-id": BUTTON_ERROR}

    def test_unknown_event_is_valid(self, plugin):
        """Events without required fields are saved as entered"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict(), "unknown-event", 0
        )

        assert is_valid
        assert errors == {}

    def test_existing_event(self, plugin):
        """Editing an existing event is validated the same as a new one"""
        is_valid, _, errors = plugin.validate_event_config_ui(
            indigo.Dict(), "btn-down", 456
        )

        assert not is_valid
        assert errors == {"device-id": DEVICE_ERROR}

    def test_returns_values_dict(self, plugin):
        """The values are saved as entered, without changes"""
        values = indigo.Dict({"device-id": "123"})

        _, values_dict, _ = plugin.validate_event_config_ui(values, "btn-down", 0)

        assert values_dict is values


class TestValidateDeviceConfigUi:
    def test_valid_model_settings(self, plugin):
        """Valid settings for a model with validation are saved"""
        is_valid, _, errors = plugin.validateDeviceConfigUi(
            indigo.Dict({"temp-offset": "1.5"}), "shelly-blu-ht", 123
        )

        assert is_valid
        assert errors == {}

    def test_invalid_model_settings(self, plugin):
        """The model class's field errors are shown in the device dialog"""
        is_valid, _, errors = plugin.validateDeviceConfigUi(
            indigo.Dict(
                {
                    "offset": "abc",
                    "measure-contents-level": True,
                    "measure-contents-level-container-height": "0",
                    "measure-contents-level-sensor-height": "100",
                }
            ),
            "shelly-blu-distance",
            123,
        )

        assert not is_valid
        assert errors == {
            "offset": "Must be a whole number of mm.",
            "measure-contents-level-container-height": (
                "Must be a whole number of mm greater than 0."
            ),
        }

    def test_errors_are_indigo_dict(self, plugin):
        """Indigo needs an indigo.Dict to show the field errors"""
        _, _, errors = plugin.validateDeviceConfigUi(
            indigo.Dict({"temp-offset": "abc"}), "shelly-blu-ht", 123
        )

        assert isinstance(errors, indigo.Dict)

    @pytest.mark.parametrize("type_id", ["shelly-plus-1", "shelly-blu-button1"])
    def test_model_without_validation(self, plugin, type_id):
        """Models without their own validation use the base class and are saved as entered"""
        is_valid, _, errors = plugin.validateDeviceConfigUi(
            indigo.Dict({"temp-offset": "abc"}), type_id, 123
        )

        assert is_valid
        assert errors == {}

    @pytest.mark.parametrize("type_id", ["component-humidity", "component-switch"])
    def test_component_device(self, plugin, type_id):
        """Component devices have no model class and are saved as entered"""
        is_valid, _, errors = plugin.validateDeviceConfigUi(
            indigo.Dict({"offset": "abc"}), type_id, 123
        )

        assert is_valid
        assert errors == {}

    def test_returns_values_dict(self, plugin):
        """The values are saved as entered, without changes"""
        values = indigo.Dict({"temp-offset": "1"})

        _, values_dict, _ = plugin.validateDeviceConfigUi(values, "shelly-blu-ht", 123)

        assert values_dict is values


class TestDeviceFactoryModelChanged:
    @pytest.mark.parametrize(
        "model", ["shelly-blu-ht", "shelly-blu-button1", "shelly-blu-rc-button-4"]
    )
    def test_blu_model(self, plugin, model):
        """BLU models show the MAC address fields instead of the MQTT fields"""
        values_dict = plugin.deviceFactoryModelChanged(
            indigo.Dict({"shelly-model": model}), "", 0
        )

        assert values_dict["is-blu-model"] is True
        assert values_dict["is-mqtt-model"] is False

    @pytest.mark.parametrize(
        "model", ["shelly-plus-1", "shelly-pro-4-pm", "shelly-plus-walldimmer"]
    )
    def test_mqtt_model(self, plugin, model):
        """MQTT models show the broker, address, and message type fields"""
        values_dict = plugin.deviceFactoryModelChanged(
            indigo.Dict({"shelly-model": model}), "", 0
        )

        assert values_dict["is-mqtt-model"] is True
        assert values_dict["is-blu-model"] is False

    @pytest.mark.parametrize("values", [{}, {"shelly-model": ""}])
    def test_no_model_shows_mqtt_fields(self, plugin, values):
        """The MQTT fields are shown until a model is selected"""
        values_dict = plugin.deviceFactoryModelChanged(indigo.Dict(values), "", 0)

        assert values_dict["is-mqtt-model"] is True
        assert values_dict["is-blu-model"] is False

    def test_changing_model_type_replaces_flags(self, plugin):
        """Switching from a BLU model to an MQTT model hides the BLU fields"""
        values = indigo.Dict(
            {
                "shelly-model": "shelly-plus-1",
                "is-mqtt-model": False,
                "is-blu-model": True,
            }
        )

        values_dict = plugin.deviceFactoryModelChanged(values, "", 0)

        assert values_dict["is-mqtt-model"] is True
        assert values_dict["is-blu-model"] is False

    def test_other_values_kept(self, plugin):
        """Changing the model keeps the other values already entered"""
        values = indigo.Dict({"shelly-model": "shelly-blu-ht", "mac-address": "abc"})

        values_dict = plugin.deviceFactoryModelChanged(values, "", 0)

        assert values_dict is values
        assert values_dict["shelly-model"] == "shelly-blu-ht"
        assert values_dict["mac-address"] == "abc"

    @pytest.mark.parametrize("model", ["shelly-pro-2", "shelly-blu-ht"])
    def test_unverified_model_shows_warning(self, plugin, model, monkeypatch):
        """Models nobody has verified on a real device warn before they're created"""
        monkeypatch.setitem(plugin_module.verified_devices[model], "verified_by", [])

        values_dict = plugin.deviceFactoryModelChanged(
            indigo.Dict({"shelly-model": model}), "", 0
        )

        assert values_dict["is-verified-model"] is False

    def test_verified_model_hides_warning(self, plugin, monkeypatch):
        """Switching to a verified model hides a warning shown for the previous model"""
        monkeypatch.setitem(
            plugin_module.verified_devices["shelly-pro-2"],
            "verified_by",
            [{"github_username": "tester"}],
        )
        values = indigo.Dict(
            {"shelly-model": "shelly-pro-2", "is-verified-model": False}
        )

        values_dict = plugin.deviceFactoryModelChanged(values, "", 0)

        assert values_dict["is-verified-model"] is True

    @pytest.mark.parametrize("model", ["", "-1", "shelly-pro-3-em"])
    def test_non_model_hides_warning(self, plugin, model):
        """Menu headers, separators, and unavailable models aren't models to warn about"""
        values_dict = plugin.deviceFactoryModelChanged(
            indigo.Dict({"shelly-model": model}), "", 0
        )

        assert values_dict["is-verified-model"] is True


class TestReportDeviceVerification:
    @pytest.mark.parametrize(
        "values",
        [{}, {"device-id": ""}, {"device-id": "none"}, {"device-id": "123"}],
    )
    def test_no_started_device(self, plugin, values):
        """A device must be chosen, and menu headers or unknown ids don't count"""
        result = plugin.report_device_verification(indigo.Dict(values), "")

        assert result[0] is False
        assert result[2] == {"device-id": "You must select a device."}


class TestGetShellyDevicesForVerification:
    def test_no_devices(self, plugin):
        """Both sections show a disabled "None" until a Shelly device has started"""
        assert plugin.get_shelly_devices_for_verification() == [
            ("none", "%%disabled:Unverified Models%%"),
            ("none", "%%separator%%"),
            ("none", "%%disabled:None%%"),
            ("none", "%%disabled: %%"),
            ("none", "%%disabled:Community Verified Models%%"),
            ("none", "%%separator%%"),
            ("none", "%%disabled:None%%"),
        ]


class TestGetDiscoveredBluAddresses:
    def test_no_addresses(self, plugin):
        """A single disabled item explains that nothing has been relayed yet"""
        assert plugin.get_discovered_blu_addresses() == [
            ("none", "%%disabled:No discovered BLU devices%%")
        ]

    def test_unidentified_addresses(self, plugin):
        """Addresses relayed without a device using them can be selected for a new device"""
        plugin.blu_address_devices["38:39:8f:a0:1d:a6"] = set()
        plugin.blu_address_devices["7c:c6:b6:61:e2:4b"] = set()

        assert plugin.get_discovered_blu_addresses() == [
            ("none", "%%disabled:Unidentified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("38:39:8f:a0:1d:a6", "38:39:8f:a0:1d:a6"),
            ("7c:c6:b6:61:e2:4b", "7c:c6:b6:61:e2:4b"),
            ("none", "%%disabled: %%"),
            ("none", "%%disabled:Identified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("none", "%%disabled:None%%"),
        ]

    def test_identified_address_without_loaded_device(self, plugin):
        """An address used by a device that hasn't started is identified with an unknown name"""
        plugin.blu_address_devices["38:39:8f:a0:1d:a6"] = {123}

        assert plugin.get_discovered_blu_addresses() == [
            ("none", "%%disabled:Unidentified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("none", "%%disabled:None%%"),
            ("none", "%%disabled: %%"),
            ("none", "%%disabled:Identified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("38:39:8f:a0:1d:a6", "38:39:8f:a0:1d:a6 - <unknown>"),
        ]

    def test_address_used_by_multiple_devices(self, plugin):
        """An address shared by several devices is flagged instead of naming one of them"""
        plugin.blu_address_devices["38:39:8f:a0:1d:a6"] = {123, 456}

        assert plugin.get_discovered_blu_addresses() == [
            ("none", "%%disabled:Unidentified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("none", "%%disabled:None%%"),
            ("none", "%%disabled: %%"),
            ("none", "%%disabled:Identified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("38:39:8f:a0:1d:a6", "38:39:8f:a0:1d:a6 - <multiple>"),
        ]

    def test_identified_and_unidentified_addresses(self, plugin):
        """Each address is listed in its section in the order it was discovered"""
        plugin.blu_address_devices["38:39:8f:a0:1d:a6"] = {123}
        plugin.blu_address_devices["7c:c6:b6:61:e2:4b"] = set()
        plugin.blu_address_devices["b0:c7:de:11:22:33"] = {456, 789}

        assert plugin.get_discovered_blu_addresses() == [
            ("none", "%%disabled:Unidentified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("7c:c6:b6:61:e2:4b", "7c:c6:b6:61:e2:4b"),
            ("none", "%%disabled: %%"),
            ("none", "%%disabled:Identified BLE Addresses%%"),
            ("none", "%%separator%%"),
            ("38:39:8f:a0:1d:a6", "38:39:8f:a0:1d:a6 - <unknown>"),
            ("b0:c7:de:11:22:33", "b0:c7:de:11:22:33 - <multiple>"),
        ]

    def test_addresses_not_changed(self, plugin):
        """Building the menu doesn't change the discovered addresses"""
        plugin.blu_address_devices["38:39:8f:a0:1d:a6"] = {123}

        plugin.get_discovered_blu_addresses()

        assert plugin.blu_address_devices == {"38:39:8f:a0:1d:a6": {123}}


class TestGetDeviceButtons:
    @pytest.mark.parametrize("values", [{}, {"device-id": ""}])
    def test_no_device_selected(self, plugin, values):
        """A single button is offered before a device is selected"""
        assert plugin.get_device_buttons(valuesDict=indigo.Dict(values)) == [
            ("1", "Button 1")
        ]

    def test_device_not_loaded(self, plugin):
        """A selected device that hasn't started offers a single button"""
        assert plugin.get_device_buttons(
            valuesDict=indigo.Dict({"device-id": "123"})
        ) == [("1", "Button 1")]


class TestMessageHandler:
    @staticmethod
    def notification(message_type):
        """A message queued notification from the MQTT Connector plugin"""
        return indigo.Dict({"message_type": message_type, "brokerID": "12"})

    def test_subscribed_message_type_queued(self, plugin):
        """Notifications for a device's message type are queued for processing"""
        plugin.message_types = ["shellies"]
        notification = self.notification("shellies")

        plugin.message_handler(notification)

        assert plugin.message_queue.get_nowait() is notification
        assert plugin.message_queue.empty()

    def test_other_message_type_ignored(self, plugin):
        """Messages for other plugins' message types are not fetched"""
        plugin.message_types = ["shellies"]

        plugin.message_handler(self.notification("other"))

        assert plugin.message_queue.empty()

    def test_ignored_without_devices(self, plugin):
        """No message types are handled until a device starts"""
        plugin.message_handler(self.notification("shellies"))

        assert plugin.message_queue.empty()

    def test_messages_queued_in_order(self, plugin):
        """Messages are processed in the order the broker received them"""
        plugin.message_types = ["shellies", "shellies-2"]
        first = self.notification("shellies")
        second = self.notification("shellies-2")
        third = self.notification("shellies")

        plugin.message_handler(first)
        plugin.message_handler(second)
        plugin.message_handler(third)

        assert plugin.message_queue.get_nowait() is first
        assert plugin.message_queue.get_nowait() is second
        assert plugin.message_queue.get_nowait() is third
