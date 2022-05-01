import indigo

from Shelly import Shelly
from ..components.functional.input import Input


class ShellyPlusI4(Shelly):
    """
    Creates a Shelly Plus I4 device class.
    """

    display_name = "Shelly Plus I4"

    def __init__(self, device):
        super(ShellyPlusI4, self).__init__(device)

        self.input_0 = self.register_component(Input, "Input 1", comp_id=0)
        self.input_1 = self.register_component(Input, "Input 2", comp_id=1)
        self.input_2 = self.register_component(Input, "Input 3", comp_id=2)
        self.input_3 = self.register_component(Input, "Input 4", comp_id=3)
