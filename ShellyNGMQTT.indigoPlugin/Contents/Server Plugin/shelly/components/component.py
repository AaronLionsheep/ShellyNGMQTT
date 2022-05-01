import indigo


class Component(object):
    """

    """

    component_type = None
    device_type_id = None

    def __init__(self, shelly, device=None, comp_id=0):
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
        self.device = device
        self.logger = shelly.logger
        self.latest_config = {}

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

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        pass

    def handle_notify_event(self, event):
        """
        Default handler for events coming from a device.

        This default handler catches the common events for all components such
        as configuration changes.

        :param event: The event from the device.
        :return: None
        """

        if event == "config_changed":
            self.get_config()
        else:
            self.logger.info("no handler for event '{}'".format(event))

    def handle_notify_status(self, status):
        """

        :param status:
        :return:
        """

        pass

    def get_status(self):
        """

        :return:
        """

        pass

    def process_status(self, status):
        """
        A method that processes a status message.

        :param status: The status message
        :return:
        """

        pass

    def get_config(self):
        """

        :return:
        """

        pass

    def process_config(self, config, error=None):
        """

        :param config:
        :param error:
        :return:
        """

        pass

    def set_config(self, config):
        """

        :param config:
        :return:
        """

        pass

    def process_set_config(self, status, error=None):
        """

        :param status:
        :param error:
        :return:
        """

        pass