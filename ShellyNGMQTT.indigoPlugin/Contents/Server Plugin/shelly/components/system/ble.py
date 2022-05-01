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

        # TODO: get the config
        return

    def set_config(self, config):
        """
        Set the configuration for the BLE.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        # TODO: set the config
        return

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
