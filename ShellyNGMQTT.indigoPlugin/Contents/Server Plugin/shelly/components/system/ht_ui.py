from ..component import Component


class HT_UI(Component):
    """
    The Bluetooth Low Energy component handles bluetooth services of a device
    """

    component_type = "ht_ui"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a HT_UI component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(HT_UI, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of the HT_UI.

        :return: config
        """

        self.shelly.publish_rpc("HT_UI.GetConfig", {}, callback=self.process_config)

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
            'temperature-unit': config.get("temperature_unit", "C")
        }

        props = self.shelly.device.pluginProps
        props.update(self.latest_config)
        self.shelly.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the HT_UI.

        :param config: A config to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("HT_UI.SetConfig", {'config': config}, callback=self.process_set_config)

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
        The HT_UI component does not own any status properties.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("HT_UI.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the iHT_UInput.

        :param error:
        :param status: The status message
        :return:
        """

        # No status properties
        pass
