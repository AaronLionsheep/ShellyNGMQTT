import indigo

from Shelly import Shelly
from ..components.functional.temperature import Temperature
from ..components.functional.humidity import Humidity
from ..components.system.system import System
from ..components.system.wifi import WiFi
from ..components.system.ble import BLE
from ..components.system.mqtt import MQTT
from ..components.system.device_power import DevicePower
from ..components.system.ht_ui import HT_UI


class ShellyPlusHT(Shelly):
    """
    Creates a Shelly Plus HT device class.
    """

    display_name = "Shelly Plus H&T"

    def __init__(self, device_id):
        super(ShellyPlusHT, self).__init__(device_id)

        self.system_components = {
            "system": System(self),
            "wifi": WiFi(self),
            "ble": BLE(self),
            "mqtt": MQTT(self),
            "devicepower": DevicePower(self),
            "ht-ui": HT_UI(self)
        }

        props = self.device.pluginProps
        props.update({
            "SupportsStatusRequest": False,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
            "SupportsBatteryLevel": True
        })
        self.device.replacePluginPropsOnServer(props)

        self.temperature = self.register_component(Temperature, "Temperature", comp_id=0)
        self.humidity = self.register_component(Humidity, "Humidity", comp_id=0)

    def handle_notify_status(self, component_type, instance_id, status):
        """
        Handler for NotifyStatus RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param status: Data for the notification.
        :return: None
        """
        super(ShellyPlusHT, self).handle_notify_status(component_type, instance_id, status)

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """
        super(ShellyPlusHT, self).handle_notify_event(component_type, instance_id, event)

    def handle_action(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """
        super(ShellyPlusHT, self).handle_action(action)

    def get_device_state_list(self):
        """
        Build the device state list for the device.

        Possible state helpers are:
        - getDeviceStateDictForNumberType
        - getDeviceStateDictForRealType
        - getDeviceStateDictForStringType
        - getDeviceStateDictForBoolOnOffType
        - getDeviceStateDictForBoolYesNoType
        - getDeviceStateDictForBoolOneZeroType
        - getDeviceStateDictForBoolTrueFalseType

        :return: The device state list.
        """
        states = super(ShellyPlusHT, self).get_device_state_list()
        states.extend([
            indigo.activePlugin.getDeviceStateDictForRealType("battery-voltage", "Battery Voltage (V)", "Battery Voltage (V)"),
            indigo.activePlugin.getDeviceStateDictForBoolYesNoType("external-power", "External Power", "External Power")
        ])
        return states

    def get_device_display_state_id(self):
        """
        Determine which device state should be shown in the device list.

        :return: The state name.
        """
        return "batteryLevel"

    def update_state_image(self):
        """
        Update the state image for the device based on current properties.

        The main Indigo device will display battery information, so battery icon
        enumerations should be chosen.

        :return: None
        """
        if self.device.states["external-power"]:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryChargerOn)
        else:
            battery_level = self.device.batteryLevel or 0
            if battery_level > 75:
                self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryLevelHigh)
            elif battery_level > 50:
                self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryLevel75)
            elif battery_level > 25:
                self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryLevel50)
            elif battery_level > 10:
                self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryLevel25)
            else:
                self.device.updateStateImageOnServer(indigo.kStateImageSel.BatteryLevelLow)