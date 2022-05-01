import indigo

from Shelly import Shelly
from ..components.functional.switch import Switch
from ..components.functional.input import Input


class ShellyPlus1(Shelly):
    """
    Creates a Shelly Plus 1 device class.
    """

    display_name = "Shelly Plus 1"

    def __init__(self, device):
        super(ShellyPlus1, self).__init__(device)

        self.switch = self.register_component(Switch, "Switch")
        self.input = self.register_component(Input, "Input")

    def get_topics(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list.
        """

        address = self.get_address()
        if address is None:
            return []
        else:
            return [
                "{}/online".format(address),
                "{}/rpc".format(address),
                "{}/events/rpc".format(address)
            ]

    def handle_notify_status(self, component_type, instance_id, status):
        """
        Handler for NotifyStatus RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param status: Data for the notification.
        :return: None
        """

        self.logger.debug("handleNotifyStatus({}, {}, {})".format(component_type, instance_id, status))
        component = self.get_component(component_type=component_type, comp_id=instance_id)
        if component:
            component.process_status(status)

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """

        self.logger.debug("handleNotifyEvent({}, {}, {})".format(component_type, instance_id, event))
        Shelly.handle_notify_event(self, component_type=component_type, instance_id=instance_id, event=event)

    def handle_action(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly.handle_action(self, action)
