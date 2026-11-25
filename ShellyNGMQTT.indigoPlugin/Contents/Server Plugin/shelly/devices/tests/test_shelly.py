import logging
from urllib.parse import parse_qs, urlsplit

import plugin as plugin_module
import pytest
from shelly.devices.shelly import Shelly
from shelly.devices.shelly_blu_ht import ShellyBLUHT
from shelly.devices.shelly_plus_ht import ShellyPlusHT
from shelly.devices.shelly_pro_2 import ShellyPro2


def query(url):
    """The query parameters of a URL, with single values unwrapped."""
    return {key: value[0] for key, value in parse_qs(urlsplit(url).query).items()}


class TestPluginProps:
    def test_wifi_default(self):
        """Wi-Fi main devices hide the on/off state and sensor value they don't have"""
        assert ShellyPro2.plugin_props() == {
            "SupportsStatusRequest": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    def test_plus_ht(self):
        """The sleeping Plus H&T can't answer status requests and reports its battery"""
        assert ShellyPlusHT.plugin_props() == {
            "SupportsStatusRequest": False,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
            "SupportsBatteryLevel": True,
        }

    def test_returns_new_dict(self):
        """Each call returns a separate dict so devices never share props"""
        assert Shelly.plugin_props() is not Shelly.plugin_props()

    @pytest.mark.parametrize("model_class", plugin_module.shelly_model_classes.values())
    def test_every_model_sets_on_state_and_sensor_value(self, model_class):
        """Indigo falls back to showing an on/off state when these props are missing (#193)"""
        props = model_class.plugin_props()

        assert "SupportsOnState" in props
        assert "SupportsSensorValue" in props


class TestVerificationUrl:
    def test_issue_form(self):
        """The link opens the device verification form in the plugin's repository"""
        url = urlsplit(ShellyPro2.verification_url())

        assert url.netloc == "github.com"
        assert url.path == "/AaronLionsheep/ShellyNGMQTT/issues/new"
        assert query(ShellyPro2.verification_url())["template"] == (
            "device-verification.yml"
        )

    def test_model_details(self):
        """The title names the model, since GitHub can't fill in the model dropdown from a link"""
        fields = query(ShellyBLUHT.verification_url())

        assert fields["title"] == "Verify Shelly BLU H&T"
        assert "model" not in fields

    def test_versions(self):
        """Known versions are filled in so the reporter doesn't have to look them up"""
        fields = query(
            ShellyPro2.verification_url(firmware="1.4.4", plugin_version="1.5.0")
        )

        assert fields["firmware"] == "1.4.4"
        assert fields["plugin-version"] == "1.5.0"

    def test_unknown_versions_left_blank(self):
        """Empty versions are left out so the form shows its placeholders"""
        fields = query(ShellyPro2.verification_url())

        assert "firmware" not in fields
        assert "plugin-version" not in fields

    def test_special_characters_encoded(self):
        """Names with "&" and "/" can't break the query string"""
        url = ShellyBLUHT.verification_url(firmware="20241011/1.4.4&x=1")

        assert "&x=1" not in url
        assert query(url)["firmware"] == "20241011/1.4.4&x=1"


def log_rpc_error(device_name, action, error):
    """Log an RPC error through a bare Shelly, skipping __init__ which looks up the Indigo device."""
    shelly = object.__new__(Shelly)
    shelly.logger = logging.getLogger("Plugin.ShellyNGMQTT")
    shelly.log_rpc_error(device_name, action, error)


class TestLogRpcError:
    def test_readable_message(self, caplog):
        """The log names the device, what failed, and Shelly's message and code instead of a raw dict"""
        log_rpc_error(
            "Kitchen Light",
            "read status",
            {"code": -105, "message": "Argument 'id', value 3 not found!"},
        )

        assert caplog.record_tuples == [
            (
                "Plugin.ShellyNGMQTT",
                logging.ERROR,
                "\"Kitchen Light\" failed to read status: Argument 'id', value 3 not found! (code -105)",
            )
        ]

    def test_missing_message(self, caplog):
        """An error without a message still logs a readable line instead of raising"""
        log_rpc_error("Kitchen Shelly", "read configuration", {"code": 404})

        assert caplog.messages == [
            '"Kitchen Shelly" failed to read configuration: Unknown error (code 404)'
        ]
