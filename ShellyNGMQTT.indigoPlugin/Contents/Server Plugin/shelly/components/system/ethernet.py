from ..component import Component


class Ethernet(Component):
    """
    The Ethernet component handles the ethernet interface of devices.
    """

    component_type = "ethernet"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create an Ethernet component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(Ethernet, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the Ethernet.

        :return: config
        """

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for the Ethernet.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        # TODO: set the config
        return

    def get_status(self):
        """
        The status of the Ethernet component contains the IP address which can
        be used to access the device over ethernet.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("Eth.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the Ethernet.

        :param error:
        :param status: The status message
        :return:
        """

        if error and error.get('code', 0) != 404:
            self.logger.error(error)
            return

        if status and status.get('ip', None):
            self.shelly.device.updateStatesOnServer([
                {'key': "ip-address", 'value': status.get('ip_address', None)}
            ])
