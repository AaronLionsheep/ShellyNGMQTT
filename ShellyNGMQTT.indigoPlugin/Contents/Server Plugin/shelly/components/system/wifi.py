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
            # AP
            'wifi-ap-ssid': config.get("ap", {}).get("ssid", ""),
            'wifi-ap-password': "",  # Never save the password
            'wifi-ap-open-network': config.get("ap", {}).get("is_open", False),
            'wifi-ap-enable': config.get("ap", {}).get("enable", ""),
            # WiFi 1
            'wifi-1-ssid': config.get("sta", {}).get("ssid", ""),
            'wifi-1-password': "",  # Never save the password
            'wifi-1-open-network': config.get("sta", {}).get("is_open", False),
            'wifi-1-enable': config.get("sta", {}).get("enable", ""),
            'wifi-1-ipv4-mode': config.get("sta", {}).get("ipv4mode", ""),
            'wifi-1-ip-address': config.get("sta", {}).get("ip", ""),
            'wifi-1-network-mask': config.get("sta", {}).get("netmask", ""),
            'wifi-1-gateway': config.get("sta", {}).get("gw", ""),
            'wifi-1-nameserver': config.get("sta", {}).get("nameserver", ""),
            # WiFi 2
            'wifi-2-ssid': config.get("sta1", {}).get("ssid", ""),
            'wifi-2-password': "",  # Never save the password
            'wifi-2-open-network': config.get("sta1", {}).get("is_open", False),
            'wifi-2-enable': config.get("sta1", {}).get("enable", ""),
            'wifi-2-ipv4-mode': config.get("sta1", {}).get("ipv4mode", ""),
            'wifi-2-ip-address': config.get("sta1", {}).get("ip", ""),
            'wifi-2-network-mask': config.get("sta1", {}).get("netmask", ""),
            'wifi-2-gateway': config.get("sta1", {}).get("gw", ""),
            'wifi-2-nameserver': config.get("sta1", {}).get("nameserver", ""),
            # Roaming
            'wifi-roaming-rssi-threshold': config.get("roam", {}).get("rssi_thr", ""),
            'wifi-roaming-interval': config.get("roam", {}).get("interval", "")
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.shelly.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the wifi.

        :param config: A wifi config to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("Wifi.SetConfig", {'config': config}, callback=self.process_set_config)

    def process_set_config(self, status, error=None):
        """
        A method that processes the response from setting the config.

        :param status: The status.
        :param error: The error.
        :return: None
        """

        if error:
            self.logger.error("Error writing configuration: {}".format(error.get("message", "<Unknown>")))
            return

        if status.get('restart_required', False):
            self.log_command_received("rebooting...")

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
