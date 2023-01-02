from ..component import Component


class DevicePower(Component):
    """
    The Input component handles the monitoring of device's battery charge and is only available on battery-operated devices.
    """

    component_type = "devicepower"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a System component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(DevicePower, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the input.

        :return: config
        """

        self.shelly.publish_rpc("DevicePower.GetConfig", {}, callback=self.process_config)

    def process_config(self, config, error=None):
        """
        A method that processes the configuration message.

        :param config: The returned configuration data.
        :param error: Any errors.
        :return: None
        """
        return

    def set_config(self, config):
        """
        Set the configuration for the system.

        :param config: A system config to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("DevicePower.SetConfig", {'config': config}, callback=self.process_set_config)

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

        self.shelly.publish_rpc("DevicePower.GetStatus", params, callback=self.process_status)

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

        voltage = status.get('battery', {}).get("V", None)
        level = status.get('battery', {}).get("percent", None)
        external = status.get('external', {}).get("present", False)

        self.shelly.device.updateStatesOnServer([
            {"key": "battery-voltage", "value": voltage, "uiValue": "{} V".format(voltage)},
            {"key": "batteryLevel", "value": level, "uiValue": "{}%".format(level)},
            {"key": "external-power", "value": external}
        ])
        self.shelly.update_state_image()
