import indigo # noqa
import json
import logging
import uuid


class Shelly(object):
    """
    Base class used by all Shelly model classes.
    """

    display_name = "ShellyBase"

    def __init__(self, device_id):
        """Create a new Shelly device.

        :param device_id: The indigo device id.
        """
        self.device_id = device_id
        self._device = None
        self.component_devices = {}
        self.logger = logging.getLogger("Plugin.ShellyNGMQTT")

        # Inspect devices in the group to find all components
        group_ids = indigo.device.getGroupList(self.device)
        for dev_id in group_ids:
            if dev_id != self.device.id:
                device = indigo.devices[dev_id]
                self.component_devices[device.model] = device

        self.device.updateStateImageOnServer(indigo.kStateImageSel.NoImage)

    @property
    def device(self):
        """
        Getter for the Indigo device.

        :return: Indigo device
        """
        device = indigo.devices.get(self.device_id, None)
        # Keep track of the last known device object
        if device is not None:
            self._device = device
        return self._device

    @property
    def components(self):
        """
        Getter for all device components.
        """
        return []

    def get_config(self):
        """
        Gets the config for all components

        :return: None
        """
        for component in self.components:
            component.get_config()

    #
    # Property getters
    #

    def get_address(self):
        """
        Helper function to get the base address of this device. Trailing '/' will be removed.

        :return: The cleaned base address.
        """

        address = self.device.pluginProps.get('address', None)
        if not address or address == '':
            return None

        address.strip()
        if address.endswith('/'):
            address = address[:-1]
        return address

    def get_component_for_device(self, device):
        """
        Utility to find a component that is associated with a specific indigo device.

        :param device:
        :return: Component
        """

        for component in self.components:
            if component.device_id and component.device_id == device.id:
                return component
        return None

    def get_device_state_list(self):
        """
        Build the device state list for the device.

        Possible state helpers are:
        - getDeviceStateDictForNumberType
        - getDeviceStateDictForRealType
        - getDeviceStateDictForStringType
        - getDeviceStateDictForBoolOnOffType
        - getDeviceStateDictForBoolYesNoType
        - getDeviceStateDictForBoolOneZeroType
        - getDeviceStateDictForBoolTrueFalseType

        :return: The device state list.
        """
        return []

    def get_device_display_state_id(self):
        """
        Determine which device state should be shown in the device list.

        :return: The state name.
        """
        return indigo.PluginBase.getDeviceDisplayStateId(indigo.activePlugin, self.device)

    def update_state_image(self):
        """
        A function that can be called to inspect the current device state and
        update the state image accordingly.

        :return:
        """
        return None

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """
        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.get_config()
            for component in self.system_components.values():
                component.get_status()

    #
    # Utilities
    #

    def log_command_sent(self, message):
        """
        Helper method that logs when a device command is sent.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("sent \"{}\" {}".format(self.device.name, message))

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("received \"{}\" {}".format(self.device.name, message))

    def register_component(self, component_class, name, comp_id=0, props=None):
        """
        Find or create the Indigo device for the functional component.

        This is used for functional components that have their own Indigo
        devices. This just performs the association of an indigo device with a
        component object and the main shelly object.

        :param component_class: The class of the component to create.
        :param name: The name of the component (device model).
        :param comp_id: The identifier for the component.
        :param props: Properties to set for the device.
        :return: The created component object.
        """

        if props is None:
            props = {}
        if name not in self.component_devices:
            # The component name we are trying to register is new, so we did
            # not find a device with that name already in the group. Create it
            # and add it to the group.
            ui_name = "{} {}".format(self.device.name, name)
            device = indigo.device.create(
                indigo.kProtocol.Plugin,
                name=ui_name,
                deviceTypeId=component_class.device_type_id,
                groupWithDevice=self.device.id)
            device.model = name
            device.replaceOnServer()
            self.component_devices[name] = device

        device = self.component_devices.get(name, None)
        if device is None:
            raise KeyError("component '{}' not found in '{}' when it should...".format(name, self.device.name))

        # Force any device properties
        if len(props) > 0:
            device_props = device.pluginProps
            device_props.update(props)
            device.replacePluginPropsOnServer(device_props)
            device.stateListOrDisplayStateIdChanged()

        # Create the component
        component = component_class(self, device.id, comp_id)
        self.functional_components.append(component)
        return component

    def get_component(self, component_class=None, component_type=None, comp_id=0):
        """
        Utility to find the component object matching the criteria.

        :param component_class: Only return components that are an instance of this class.
        :param component_type: Only return components that have this type.
        :param comp_id: Only return components with this id.
        :return: The matching component.
        """
        if comp_id is None:
            comp_id = 0

        for component in self.components:
            if component_class is not None and not isinstance(component, component_class):
                continue
            if component_type is not None and component.component_type != component_type:
                continue
            # Special case: let a component with id -1 handle any comp_id message
            if component.comp_id != -1 and component.comp_id != comp_id:
                continue
            # Made it this far, so all criteria matched
            return component
