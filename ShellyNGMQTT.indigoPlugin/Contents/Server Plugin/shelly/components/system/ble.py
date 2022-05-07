from ..component import Component


class BLE(Component):
    """
    The Bluetooth Low Energy component handles bluetooth services of a device
    """

    component_type = "ble"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a WiFi component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(BLE, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the BLE.

        :return: config
        """

        self.shelly.publish_rpc("BLE.GetConfig", {}, callback=self.process_config)

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
            'ble-enable': config.get("enable", False)
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.shelly.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the BLE.

        :param config: A config to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("BLE.SetConfig", {'config': config}, callback=self.process_set_config)

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
        The BLE component does not own any status properties.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("BLE.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the input.

        :param error:
        :param status: The status message
        :return:
        """

        # No status properties
        pass
