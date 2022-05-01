from ..component import Component


class MQTT(Component):
    """
    The MQTT component handles configuration and status of the outbound MQTT connection
    """

    component_type = "mqtt"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a MQTT component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """

        super(MQTT, self).__init__(shelly)

    def get_config(self):
        """
        Get the configuration of MQTT.

        :return: config
        """

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for MQTT.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        # TODO: set the config
        return

    def get_status(self):
        """
        The status of the MQTT component shows whether the device is connected over MQTT.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("MQTT.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the input.

        :param error:
        :param status: The status message
        :return:
        """

        # Nothing very useful, just the MQTT connection state, which would always be true
        pass
