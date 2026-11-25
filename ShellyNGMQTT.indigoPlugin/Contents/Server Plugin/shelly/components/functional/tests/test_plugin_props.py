import pytest
from shelly.components.component import Component
from shelly.components.functional.cover import Cover
from shelly.components.functional.humidity import Humidity
from shelly.components.functional.input import Input
from shelly.components.functional.light import Light
from shelly.components.functional.pm1 import PM1
from shelly.components.functional.switch import Switch
from shelly.components.functional.temperature import Temperature


def test_default_supports_status_request():
    """Every component answers status requests through Component.handle_action"""
    assert Component.plugin_props() == {"SupportsStatusRequest": True}


@pytest.mark.parametrize("component_class", [Switch, Light, Cover])
def test_metering_left_to_model(component_class):
    """Whether a switch, light, or cover meters power depends on the model, so they only set the default"""
    assert component_class.plugin_props() == {"SupportsStatusRequest": True}


@pytest.mark.parametrize("component_class", [Temperature, Humidity])
def test_sensors_show_value_not_on_state(component_class):
    """Temperature and humidity show their reading instead of an on/off state"""
    assert component_class.plugin_props() == {
        "SupportsStatusRequest": True,
        "SupportsOnState": False,
        "SupportsSensorValue": True,
    }


def test_input_shows_on_state():
    """An input is pressed or released, so it shows an on/off state and no sensor value"""
    assert Input.plugin_props() == {
        "SupportsStatusRequest": True,
        "SupportsOnState": True,
        "SupportsSensorValue": False,
    }


def test_pm1_meters_without_on_state():
    """A power meter has no output to switch, but always reports power and energy"""
    assert PM1.plugin_props() == {
        "SupportsStatusRequest": True,
        "SupportsOnState": False,
        "SupportsSensorValue": False,
        "SupportsPowerMeter": True,
        "SupportsEnergyMeter": True,
        "SupportsEnergyMeterCurPower": True,
    }


@pytest.mark.parametrize("component_class", [Component, Temperature, Input, PM1])
def test_returns_new_dict(component_class):
    """Each call returns a separate dict so devices never share props"""
    assert component_class.plugin_props() is not component_class.plugin_props()
