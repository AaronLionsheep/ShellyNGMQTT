import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]


class Component:
    """
    A base class used for all components.
    """

    component_type = None
    device_type_id = None

    @classmethod
    def plugin_props(cls) -> dict:
        """
        Default pluginProps that every device of this component will have.

        Models can override these with the props they pass to register_component.
        Indigo only fills in the hidden Supports* fields from Devices.xml when the
        settings dialog is saved, so props the component always needs belong here.
        """
        return {"SupportsStatusRequest": True}

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

        if indigo.activePlugin.pluginPrefs.get("log-device-activity", True):
            if self.device:
                device_name = self.device.name
            else:
                device_name = self.shelly.device.name
            self.logger.info(f'sent "{device_name}" {message}')

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get("log-device-activity", True):
            if self.device:
                device_name = self.device.name
            else:
                device_name = self.shelly.device.name
            self.logger.info(f'received "{device_name}" {message}')

    def log_rpc_error(self, action, error):
        """
        Log an RPC error response with the name of the device that produced it.

        :param action: What the failed RPC was doing, such as "read configuration".
        :param error: The error from the RPC response, with "code" and "message" keys.
        :return: None
        """

        # System components have no device of their own, so use the main device
        device = self.device if self.device_id else self.shelly.device
        self.shelly.log_rpc_error(device.name, action, error)

    def command_callback(self, action):
        """
        Build an RPC callback that logs a failed command with this component's device name.

        :param action: What the command does, such as "turn on".
        :return: A callback for publish_rpc.
        """

        def callback(result, error=None):
            if error:
                self.log_rpc_error(action, error)

        return callback

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
        return indigo.PluginBase.getDeviceDisplayStateId(
            indigo.activePlugin, self.device
        )

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
            if (
                trigger.pluginTypeId == event["name"].replace("_", "-")
                and int(trigger.pluginProps.get("device-id", -1)) == self.device.id
            ):
                indigo.trigger.execute(trigger)

        # Handle base events
        if event["name"] == "config_changed":
            self.get_config()

    def handle_notify_status(self, status):
        """

        :param status:
        :return:
        """

        raise NotImplementedError("No default implementation for handle_notify_status")

    def get_status(self):
        """

        :return:
        """

        raise NotImplementedError("No default implementation for get_status")

    def process_status(self, status):
        """
        A method that processes a status message.

        :param status: The status message
        :return:
        """

        raise NotImplementedError("No default implementation for process_status")

    def get_config(self):
        """

        :return:
        """

        raise NotImplementedError("No default implementation for get_config")

    def process_config(self, config, error=None):
        """

        :param config:
        :param error:
        :return:
        """

        raise NotImplementedError("No default implementation for process_config")

    def set_config(self, config):
        """

        :param config:
        :return:
        """

        raise NotImplementedError("No default implementation for set_config")

    def process_set_config(self, status, error=None):
        """

        :param status:
        :param error:
        :return:
        """

        raise NotImplementedError("No default implementation for process_set_config")
