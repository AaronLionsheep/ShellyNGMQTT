import indigo

from ..devices.Shelly import Shelly


class Component(object):
    """

    """

    def __init__(self, shelly, device):
        """

        :param shelly:
        :param device:
        """

        if isinstance(shelly, Shelly):
            self.shelly = shelly
        else:
            raise TypeError("{} is not a Shelly device!".format(shelly))

        self.device = device
        self.logger = shelly.logger

    def log_command_sent(self, message):
        """
        Helper method that logs when a device command is sent.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("sent \"{}\" {}".format(self.device.name, message))

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("received \"{}\" {}".format(self.device.name, message))

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        pass

    def process_status(self, status):
        """
        A method that processes a status message.

        :param status: The status message
        :return:
        """

        pass