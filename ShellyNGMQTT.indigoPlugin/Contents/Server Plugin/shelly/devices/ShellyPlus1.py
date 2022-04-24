import indigo

from Shelly import Shelly
from ..components.functional.switch import Switch
from ..components.functional.input import Input


class ShellyPlus1(Shelly):
    """
    Creates a Shelly Plus 1 device class.
    """

    def __init__(self, device):
        super(ShellyPlus1, self).__init__(device)

        self.switch = None
        self.input = None

        self.create_components()

    def create_components(self):
        """
        Creates the required components and devices that are missing from the group.

        :return:
        """

        component_devices = {
            'Switch': None,
            'Input': None
        }

        # Load in any devices already in the group and assign their roles
        group_ids = indigo.device.getGroupList(self.device)
        for dev_id in group_ids:
            device = indigo.devices[dev_id]
            if device.model in component_devices and component_devices[device.model] is None:
                component_devices[device.model] = device

        # Create any missing devices or load in existing devices
        if component_devices['Switch'] is None:
            switch_device = indigo.device.create(indigo.kProtocol.Plugin,
                                                 deviceTypeId="component-switch",
                                                 groupWithDevice=self.device.id)
            switch_device.model = "Switch"
            switch_device.replaceOnServer()

            switch_device_props = switch_device.pluginProps
            # switch_0_props["broker-id"] = valuesDict["broker-id"]
            switch_device.replacePluginPropsOnServer(switch_device_props)

            component_devices['Switch'] = switch_device
        if component_devices['Input'] is None:
            input_device = indigo.device.create(indigo.kProtocol.Plugin,
                                                deviceTypeId="component-input",
                                                groupWithDevice=self.device.id)
            input_device.model = "Input"
            input_device.replaceOnServer()

            input_device_props = input_device.pluginProps
            # input_device_props["broker-id"] = valuesDict["broker-id"]
            input_device.replacePluginPropsOnServer(input_device_props)

            component_devices['Input'] = input_device

        self.switch = Switch(self, component_devices['Switch'], 0)
        self.input = Input(self, component_devices['Input'], 0)

        self.components = [
            self.switch,
            self.input
        ]

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
        if component_type == "switch":
            if instance_id == 0:
                self.switch.process_status(status)
        elif component_type == "input":
            if instance_id == 0:
                self.input.process_status(status)

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """

        self.logger.info("handleNotifyEvent({}, {}, {})".format(component_type, instance_id, event))

    def handle_action(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        self.logger.info("handleAction({})".format(action))
