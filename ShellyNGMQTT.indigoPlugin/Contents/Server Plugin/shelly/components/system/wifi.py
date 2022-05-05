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
        Get the configuration of the wifi.

        :return: config
        """

        self.shelly.publish_rpc("WiFi.GetConfig", {}, callback=self.process_config)

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
            'wifi-ap-ssid': config.get("ap", {}).get("ssid", ""),
            'wifi-ap-enable': config.get("ap", {}).get("enable", "")
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.shelly.device.replacePluginPropsOnServer(props)

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
