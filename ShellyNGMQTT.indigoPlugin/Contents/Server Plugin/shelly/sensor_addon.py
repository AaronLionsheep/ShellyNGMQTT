from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .devices.Shelly import Shelly

class SensorAddon:
    """
    The SensorAddon manages the exposure of add-on peripherals.
    """

    def __init__(self, shelly: "Shelly"):
        """
        Create a SensorAddon component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """
        self.shelly = shelly

    def add_peripheral(self):
        """
        Links an add-on peripheral to a Component instance.
        """
        pass

    def remove_peripheral(self):
        """
        
        """
        pass

    def update_peripheral(self):
        """
        
        """
        pass

    def get_peripherals(self):
        """
        
        """
        pass

    def one_wire_scan(self):
        """
        Scan the one wire bus for peripheral devices.

        An error is raised if a dht22 peripheral is currently in use, as dht22 occupies
        the same GPIOs used for OneWire. For now the only supported OneWire peripheral
        type is ds18b20.
        """
        self.shelly.publish_rpc("SensorAddon.OneWireScan", {}, callback=self._process_one_wire_scan_results)

    def _process_one_wire_scan_results(self, results: list[dict[str, str]], error=None):
        if error:
            self.shelly.logger.error(error)
            return
        
        self.shelly.logger.info(results)
