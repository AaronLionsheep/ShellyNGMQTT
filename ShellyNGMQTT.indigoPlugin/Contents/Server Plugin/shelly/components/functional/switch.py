import indigo

from ..component import Component


class Switch(Component):
    """
    The Switch component handles a switch (relay) output terminal with optional power metering capabilities.
    """

    def __init__(self, shelly, device, comp_id):
        """
        Create a Switch component and assign it to a ShellyNG device.

        :param shelly: The ShellyNG device object.
        :param comp_id: The integer identifier for the component
        """

        super(Switch, self).__init__(shelly, device)

        if isinstance(comp_id, int):
            self.comp_id = comp_id
        else:
            # Let the except be raised if it can't be cast as an int
            self.comp_id = int(comp_id)

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
        Get the configuration of the switch (relay).

        :return: config
        """

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for the switch (relay).

        :param config: A SwitchConfig object to upload to the device.
        :return: None
        """

        # TODO: set the config
        return

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

        self.logger.info(status)

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


class SwitchConfig(object):
    """
    The configuration of the Switch component contains information about the
    input mode, the timers and the protection settings of the chosen switch instance.
    """

    def __init__(self, comp_id=None, name=None, in_mode=None,
                 initial_state=None, auto_on=None, auto_on_delay=None,
                 auto_off=None, auto_off_delay=None, input_id=None,
                 power_limit=None, voltage_limit=None, current_limit=None):
        """
        Creates a new configuration for a switch component.

        :param comp_id: Component identifier.
        :param name: Name of the switch.
        :param in_mode: Mode of the associated input. Allowed values: momentary, follow, flip, detached.
        :param initial_state: Output state to set on power_on. Allowed values: off, on, restore_last, match_input.
        :param auto_on: True if the "Automatic ON" function is enabled, False otherwise.
        :param auto_on_delay: Number of seconds to pass until the component is switched back on.
        :param auto_off: True if the "Automatic OFF" function is enabled, False otherwise.
        :param auto_off_delay: Number of seconds to pass until the component is switched back off.
        :param input_id: The id of the Input component which controls the Switch. Applicable only to Pro1 and Pro1PM devices. Allowed values: 0, 1.
        :param power_limit: Limit (in Watts) over which overpower condition occurs.
        :param voltage_limit: Limit (in Volts) over which overvoltage condition occurs.
        :param current_limit: Limit (in Amperes) over which overcurrent condition occurs.
        """

        # Attribute storage
        self._comp_id = None
        self._name = None
        self._in_mode = None
        self._initial_state = None
        self._auto_on = None
        self._auto_on_delay = None
        self._auto_off = None
        self._auto_off_delay = None
        self._input_id = None
        self._power_limit = None
        self._voltage_limit = None
        self._current_limit = None

        # Set the properties
        self.comp_id = comp_id

    @property
    def comp_id(self):
        return self._comp_id

    @comp_id.setter
    def comp_id(self, value):
        if isinstance(value, int):
            self._comp_id = value
        else:
            self._comp_id = int(value)