import indigo


class Component(object):
    """

    """

    component_type = None
    device_type_id = None

    def __init__(self, shelly, device_id=None, comp_id=0):
        """

        :param shelly:
        :param device:
        """

        if isinstance(comp_id, int):
            self.comp_id = comp_id
        else:
            # Let the except be raised if it can't be cast as an int
            self.comp_id = int(comp_id)

        self.shelly = shelly
        self.device_id = device_id
        self.logger = shelly.logger
        self.latest_config = {}

    @property
    def device(self):
        """
        Getter for the indigo device object.

        :return: Indigo device
        """
        return indigo.devices[self.device_id]

    def log_command_sent(self, message):
        """
        Helper method that logs when a device command is sent.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            if self.device:
                device_name = self.device.name
            else:
                device_name = self.shelly.device.name
            self.logger.info("sent \"{}\" {}".format(device_name, message))

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            if self.device:
                device_name = self.device.name
            else:
                device_name = self.shelly.device.name
            self.logger.info("received \"{}\" {}".format(device_name, message))

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
        return indigo.PluginBase.getDeviceStateList(indigo.activePlugin, self.device)

    def get_device_display_state_id(self):
        """
        Determine which device state should be shown in the device list.

        :return: The state name.
        """
        return indigo.PluginBase.getDeviceDisplayStateId(indigo.activePlugin, self.device)

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
        Default handler for events coming from a device.

        This default handler catches the common events for all components such
        as configuration changes.

        :param event: The event from the device.
        :return: None
        """

        # Fire any triggers matching this event for the device associated with the component
        for trigger in indigo.activePlugin.triggers.values():
            if trigger.pluginTypeId == event.replace('_', '-') and int(trigger.pluginProps.get('device-id', -1)) == self.device.id:
                indigo.trigger.execute(trigger)

        # Handle base events
        if event == "config_changed":
            self.get_config()

    def handle_notify_status(self, status):
        """

        :param status:
        :return:
        """

        raise NotImplementedError

    def get_status(self):
        """

        :return:
        """

        raise NotImplementedError

    def process_status(self, status):
        """
        A method that processes a status message.

        :param status: The status message
        :return:
        """

        raise NotImplementedError

    def get_config(self):
        """

        :return:
        """

        raise NotImplementedError

    def process_config(self, config, error=None):
        """

        :param config:
        :param error:
        :return:
        """

        raise NotImplementedError

    def set_config(self, config):
        """

        :param config:
        :return:
        """

        raise NotImplementedError

    def process_set_config(self, status, error=None):
        """

        :param status:
        :param error:
        :return:
        """

        raise NotImplementedError
