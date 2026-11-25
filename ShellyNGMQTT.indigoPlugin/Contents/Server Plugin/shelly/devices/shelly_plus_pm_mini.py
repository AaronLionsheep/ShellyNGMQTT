from ..components.functional.pm1 import PM1
from ..components.system.ble import BLE
from ..components.system.mqtt import MQTT
from ..components.system.script import Script
from ..components.system.system import System
from ..components.system.wifi import WiFi
from ..scripts.blu_relay import BluRelayScript
from .shelly_mqtt import ShellyMQTT


class ShellyPlusPMMini(ShellyMQTT):
    """
    Creates a Shelly Plus PM Mini device class.

    The PM Mini is a metering-only device: it measures the circuit it is
    attached to and has no relay, so it registers a PM1 component rather than
    a Switch.
    """

    display_name = "Shelly Plus PM Mini"

    def __init__(self, device_id):
        super().__init__(device_id)

        self.system_components = {
            "system": System(self),
            "wifi": WiFi(self),
            "ble": BLE(self),
            "mqtt": MQTT(self),
            "script": Script(self),
        }
        self.blu_relay = BluRelayScript(self.system_components["script"])
        self.blu_relay.sync()

        self.pm1 = self.register_component(PM1, "Power Meter")

    def handle_notify_status(self, component_type, instance_id, status):
        """
        Handler for NotifyStatus RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param status: Data for the notification.
        :return: None
        """

        super().handle_notify_status(component_type, instance_id, status)

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """

        super().handle_notify_event(component_type, instance_id, event)

    def handle_action(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        super().handle_action(action)
