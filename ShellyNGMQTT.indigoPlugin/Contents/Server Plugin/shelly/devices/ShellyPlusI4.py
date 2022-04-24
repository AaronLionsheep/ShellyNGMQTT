import indigo

from Shelly import Shelly
from ..components.functional.input import Input


class ShellyPlusI4(Shelly):
    """
    Creates a Shelly Plus I4 device class.
    """

    def __init__(self, device):
        super(ShellyPlusI4, self).__init__(device)

        self.input_0 = None
        self.input_1 = None
        self.input_2 = None
        self.input_3 = None

        self.create_components()

        self.logger.debug(self.input_0)
        self.logger.debug(self.input_1)
        self.logger.debug(self.input_2)
        self.logger.debug(self.input_3)

    def create_components(self):
        """
        Creates the required components and devices that are missing from the group.

        :return:
        """

        component_devices = {
            'Input 1': None,
            'Input 2': None,
            'Input 3': None,
            'Input 4': None,
        }

        # Load in any devices already in the group and assign their roles
        group_ids = indigo.device.getGroupList(self.device)
        for dev_id in group_ids:
            device = indigo.devices[dev_id]
            if device.model in component_devices and component_devices[device.model] is None:
                component_devices[device.model] = device

        # Create any missing devices or load in existing devices
        for i in range(4):
            input_name = "Input {}".format(i + 1)
            if component_devices[input_name] is None:
                input_device = indigo.device.create(indigo.kProtocol.Plugin,
                                                    deviceTypeId="component-input",
                                                    groupWithDevice=self.device.id)
                input_device.model = input_name
                input_device.replaceOnServer()

                input_device_props = input_device.pluginProps
                # input_device_props["broker-id"] = valuesDict["broker-id"]
                input_device.replacePluginPropsOnServer(input_device_props)

                component_devices[input_name] = input_device

        self.input_0 = Input(self, component_devices['Input 1'], 0)
        self.input_1 = Input(self, component_devices['Input 2'], 1)
        self.input_2 = Input(self, component_devices['Input 3'], 2)
        self.input_3 = Input(self, component_devices['Input 4'], 3)