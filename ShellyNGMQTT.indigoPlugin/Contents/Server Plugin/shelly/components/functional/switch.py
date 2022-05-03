import indigo

from ..component import Component


class Switch(Component):
    """
    The Switch component handles a switch (relay) output terminal with optional power metering capabilities.
    """

    component_type = "switch"
    device_type_id = "component-switch"

    def __init__(self, shelly, device, comp_id=0):
        """
        Create a Switch component and assign it to a ShellyNG device.

        :param shelly: The main ShellyNG device object.
        :param comp_id: The integer identifier for the component
        """

        super(Switch, self).__init__(shelly, device, comp_id)

    def handle_action(self, action):
        """
        The handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.set(True)
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.set(False)
        elif action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.get_status()
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            self.toggle()

    def get_config(self):
        """
        Get the configuration of the switch.

        :return: config
        """

        self.shelly.publish_rpc("Switch.GetConfig", {'id': self.comp_id}, callback=self.process_config)

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
            'in-mode': config.get("in_mode", ""),
            'initial-state': config.get("initial_state", ""),
            'auto-on': config.get("auto_on", False),
            'auto-on-delay': config.get("auto_on_delay", ""),
            'auto-off': config.get("auto_off", False),
            'auto-off-delay': config.get("auto_off_delay", ""),
            'input-id': config.get("input_id", ""),
            'power-limit': config.get("power_limit", ""),
            'voltage-limit': config.get("voltage_limit", ""),
            'current-limit': config.get("current_limit", ""),
        }

        props = self.device.pluginProps
        props.update(self.latest_config)
        self.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the input.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("Switch.SetConfig", {'id': self.comp_id, 'config': config}, callback=self.process_set_config)

    def process_set_config(self, status, error=None):
        """
        A method that processes the response from setting the config.

        :param status: The status.
        :param error: The error.
        :return: None
        """

        if error:
            self.logger.error("Error writing switch configuration: {}".format(error.get("message", "<Unknown>")))
            return

        if status.get('restart_required', False):
            self.log_command_received("rebooting...")

    def get_status(self):
        """
        The status of the Switch component contains information about the
        temperature, voltage, energy level and other physical characteristics
        of the switch instance.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("Switch.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the switch.

        :param status: The status message
        :param error:
        :return:
        """

        output = status.get('output', None)
        if output is True and self.device.states.get('onOffState', None) is not True:
            self.device.updateStateOnServer(key='onOffState', value=True)
            self.log_command_received("on")
        elif output is False and self.device.states.get('onOffState', None) is not False:
            self.device.updateStateOnServer(key='onOffState', value=False)
            self.log_command_received("off")
        else:
            # Do nothing on unknown value
            pass

    def set(self, on, toggle_after=None):
        """
        This method sets the output of the Switch component to on or off.

        :param on: True to turn the switch on, False otherwise.
        :param toggle_after: Optional time in seconds to undo the action.
        :return: None
        """

        params = {
            'id': self.comp_id,
            'on': on
        }
        if toggle_after is not None:
            params['toggle_after'] = toggle_after

        self.shelly.publish_rpc("Switch.Set", params)

        if on is True:
            self.device.updateStateOnServer(key='onOffState', value=True)
            self.log_command_sent("on")
        if on is False:
            self.device.updateStateOnServer(key='onOffState', value=False)
            self.log_command_sent("off")

    def toggle(self):
        """
        This method toggles the output state.

        :return: None
        """

        # TODO: toggle the device state
        return
