import json
import logging
from pathlib import Path
from urllib.parse import urlencode

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

# Every model keyed by device type id, with the people who confirmed it works on a real device.
# Models with an empty "verified_by" list were built from Shelly's API docs alone.
# Loaded here rather than in plugin.py, which Indigo runs without defining __file__.
with open(Path(__file__).parents[3] / "Resources" / "verified_devices.json") as f:
    verified_devices: dict[str, dict] = json.load(f)


class Shelly:
    """
    Base class used by all Shelly model classes.
    """

    display_name = "ShellyBase"
    supports_cover_profile = False
    """Whether the device factory offers the cover (roller/shutter) profile"""

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

        self.update_state_image()

    @classmethod
    def plugin_props(cls) -> dict:
        """
        Default pluginProps that all devices of this class will have.

        Applied every time the device starts, because Indigo only fills in the
        hidden Supports* fields from Devices.xml when the settings dialog is saved.
        """
        return {
            "SupportsStatusRequest": True,
            "SupportsOnState": False,
            "SupportsSensorValue": False,
        }

    @classmethod
    def validate_config_ui(cls, values_dict) -> dict[str, str]:
        """
        Validate the values from the device settings dialog.

        :param values_dict: The values from the dialog.
        :return: Error messages keyed by field id, empty when the values are valid.
        """
        return {}

    @classmethod
    def verification_url(cls, firmware: str = "", plugin_version: str = "") -> str:
        """
        Link to a new device verification issue with this model's details filled in.

        :param firmware: The device's firmware version, left blank when empty.
        :param plugin_version: The plugin version, left blank when empty.
        :return: The URL of the issue form.
        """
        # GitHub can't fill in the model dropdown from a link, so the title names the model
        fields = {
            "template": "device-verification.yml",
            "title": f"Verify {cls.display_name}",
            "firmware": firmware,
            "plugin-version": plugin_version,
        }
        return "https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?" + urlencode(
            {key: value for key, value in fields.items() if value}
        )

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

    def log_rpc_error(self, device_name, action, error):
        """
        Log an RPC error response with the name of the device that produced it.

        :param device_name: The name of the Indigo device the RPC was for.
        :param action: What the failed RPC was doing, such as "read configuration".
        :param error: The error from the RPC response, with "code" and "message" keys.
        :return: None
        """
        message = error.get("message", "Unknown error")
        self.logger.error(
            f'"{device_name}" failed to {action}: {message} (code {error.get("code")})'
        )

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
        Helper function to get the base address of this device.

        Leading and trailing whitespace is removed, and trailing '/' characters will be
        removed.

        :return: The cleaned base address.
        """
        address = self.device.pluginProps.get("address") or ""
        return address.strip().rstrip("/") or None

    def get_number_prop(self, key: str, number_type: type = float, minimum=None):
        """
        Read a numeric pluginProp, where a blank value is 0.

        An invalid value (ex: saved before the settings were validated) is warned about
        each time it's used so the configuration error isn't missed.

        :param key: The pluginProp to read.
        :param number_type: The type to convert the value to (ex: int).
        :param minimum: The smallest valid value, if any.
        :return: The number, or None when the value is invalid.
        """
        value = self.device.pluginProps.get(key, "").strip()
        try:
            number = number_type(value or 0)
            if minimum is None or number >= minimum:
                return number
        except ValueError:
            pass

        self.logger.warning(
            f"'{self.device.name}' is ignoring an invalid {key} setting: '{value}'"
        )
        return None

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
        return indigo.PluginBase.getDeviceDisplayStateId(
            indigo.activePlugin, self.device
        )

    def update_state_image(self):
        """
        A function that can be called to inspect the current device state and
        update the state image accordingly.

        :return:
        """
        self.device.updateStateImageOnServer(indigo.kStateImageSel.NoImage)

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

        if indigo.activePlugin.pluginPrefs.get("log-device-activity", True):
            self.logger.info(f'sent "{self.device.name}" {message}')

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get("log-device-activity", True):
            self.logger.info(f'received "{self.device.name}" {message}')

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
            ui_name = f"{self.device.name} {name}"
            device = indigo.device.create(
                indigo.kProtocol.Plugin,
                name=ui_name,
                deviceTypeId=component_class.device_type_id,
                groupWithDevice=self.device.id,
            )
            device.model = name
            device.replaceOnServer()
            self.component_devices[name] = device

        device = self.component_devices.get(name, None)
        if device is None:
            raise KeyError(
                f"component '{name}' not found in '{self.device.name}' when it should..."
            )

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
            if component_class is not None and not isinstance(
                component, component_class
            ):
                continue
            if (
                component_type is not None
                and component.component_type != component_type
            ):
                continue
            # Special case: let a component with id -1 handle any comp_id message
            if component.comp_id != -1 and component.comp_id != comp_id:
                continue
            # Made it this far, so all criteria matched
            return component
