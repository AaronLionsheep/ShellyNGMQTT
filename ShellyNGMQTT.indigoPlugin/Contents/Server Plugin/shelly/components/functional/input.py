from ..component import Component


class Input(Component):
    """
    The Input component handles external SW input terminals of a device.
    """

    def __init__(self, shelly, device, comp_id):
        """
        Create an Input component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        :param comp_id: The integer identifier for the component
        """

        super(Input, self).__init__(shelly, device)

        if isinstance(comp_id, int):
            self.comp_id = comp_id
        else:
            # Let the except be raised if it can't be cast as an int
            self.comp_id = int(comp_id)

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        self.logger.info("{} - handle_action({})".format(self.device.name, action))

    def get_config(self):
        """
        Get the configuration of the input.

        :return: config
        """

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for the input.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        # TODO: set the config
        return

    def get_status(self):
        """
        The status of the Input component contains information about the state
        of the chosen input instance.

        :return: status (dict)
        """

        # TODO: get the status
        return

    def process_status(self, status):
        """
        A method that processes the status of the input.

        :param status: The status message
        :return:
        """

        self.logger.info(status)
