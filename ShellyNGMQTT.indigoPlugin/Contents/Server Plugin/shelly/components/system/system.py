from ..component import Component


class System(Component):
    """
    The Input component handles external SW input terminals of a device.
    """

    component_type = "sys"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a System component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(System, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the input.

        :return: config
        """

        self.shelly.publish_rpc("Sys.GetConfig", {}, callback=self.process_config)

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
            'system-device-name': config.get("device", {}).get("name", ""),
            'system-device-eco-mode': config.get("device", {}).get("eco_mode", ""),
            'system-device-mac-address': config.get("device", {}).get("mac", ""),
            'system-device-firmware': config.get("device", {}).get("fw_id", ""),
            'system-location-timezone': config.get("location", {}).get("tz", ""),
            'system-location-lat': config.get("location", {}).get("lat", ""),
            'system-location-lon': config.get("location", {}).get("lon", ""),
            'system-debug-mqtt':  config.get("debug", {}).get("mqtt", {}).get("enable", ""),
            'system-debug-websocket': config.get("debug", {}).get("websocket", {}).get("enable", ""),
            'system-debug-udp-address': config.get("debug", {}).get("udp", {}).get("addr", "")
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.shelly.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the system.

        :param config: A system config to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("Sys.SetConfig", {'config': config}, callback=self.process_set_config)

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

        self.shelly.publish_rpc("Sys.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the input.

        :param error:
        :param status: The status message
        :return:
        """

        if error:
            self.logger.error(error)
            return

        self.shelly.device.updateStatesOnServer([
            {'key': "mac-address", 'value': status.get('mac', None)},
            {'key': "uptime", 'value': status.get('uptime', None)},
            {'key': "available-firmware", 'value': status.get('available_updates', {}).get('stable', {}).get('version', None)},
            {'key': "available-beta-firmware", 'value': status.get('available_updates', {}).get('beta', {}).get('version', None)}
        ])
