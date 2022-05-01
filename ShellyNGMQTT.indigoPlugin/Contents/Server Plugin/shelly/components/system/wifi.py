from ..component import Component


class WiFi(Component):
    """
    The WiFi component handles wireless connection services of a device.
    """

    component_type = "wifi"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a WiFi component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(WiFi, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the WiFi.

        :return: config
        """

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for the WiFi.

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

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("Wifi.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the WiFi.

        :param error:
        :param status: The status message
        :return:
        """

        if error:
            self.logger.error(error)
            return

        if status and status.get('ssid', None):
            self.shelly.device.updateStatesOnServer([
                {'key': "ssid", 'value': status.get('ssid', None)},
                {'key': "rssi", 'value': status.get('rssi', None)},
                {'key': "ip-address", 'value': status.get('sta_ip', None)}
            ])
