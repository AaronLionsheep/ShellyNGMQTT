import indigo

from ..component import Component


class Input(Component):
    """
    The Input component handles external SW input terminals of a device.
    """

    component_type = "input"
    device_type_id = "component-input"

    def __init__(self, shelly, device, comp_id=0):
        """
        Create an Input component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        :param comp_id: The integer identifier for the component
        """

        super(Input, self).__init__(shelly, device, comp_id)

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.get_status()

    def handle_notify_event(self, event):
        """
        Handler for events coming from the device.

        Look for button presses sent when the component is configured as a button.

        :param event: The event from the device.
        :return: None
        """

        if event == "btn_down":
            self.device.updateStateOnServer(key='onOffState', value=True)
            # TODO: Fire any triggers
        elif event == "btn_up":
            self.device.updateStateOnServer(key='onOffState', value=False)
            # TODO: Fire any triggers
        else:
            Component.handle_notify_event(self, event)

    def get_config(self):
        """
        Get the configuration of the switch.

        :return: config
        """

        self.shelly.publish_rpc("Input.GetConfig", {'id': self.comp_id}, callback=self.process_config)

    def process_config(self, config, error=None):
        """
        A method that processes the configuration message.

        :param config: The returned configuration data.
        :param error: Any errors.
        :return: None
        """

        if error:
            self.logger.error(error)
            return

        self.latest_config = {
            'name': config.get("name", ""),
            'type': config.get("type", ""),
            'invert': config.get("invert", False),
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the input.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("Input.SetConfig", {'id': self.comp_id, 'config': config}, callback=self.process_set_config)

    def process_set_config(self, status, error=None):
        """
        A method that processes the response from setting the config.

        :param status: The status.
        :param error: The error.
        :return: None
        """

        if error:
            self.logger.error("Error writing input configuration: {}".format(error.get("message", "<Unknown>")))
            return

        if status.get('restart_required', False):
            self.log_command_received("rebooting...")

    def get_status(self):
        """
        The status of the Input component contains information about the state
        of the chosen input instance.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("Input.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the input.

        :param error:
        :param status: The status message
        :return:
        """

        state = status.get('state', False)
        if state is not None:
            self.device.updateStateOnServer(key='onOffState', value=state)
