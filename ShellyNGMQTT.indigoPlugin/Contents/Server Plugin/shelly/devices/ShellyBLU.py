import indigo # noqa
import json
import logging
import uuid


class ShellyBLU(object):
    """
    Base class used by all Shelly BLU model classes.
    """

    display_name = "ShellyBLUBase"

    def __init__(self, device_id):
        """Create a new Shelly BLU device.

        :param device_id: The indigo device id.
        """

        self.device_id = device_id
        self._device = None
        self.logger = logging.getLogger("Plugin.ShellyNGMQTT")

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
    
    def get_address(self):
        address = self.device.pluginProps.get('address', None)
        if not address or address == '':
            return None

        return address
    
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
        return [
            indigo.activePlugin.getDeviceStateDictForBoolTrueFalseType("encryption", "Encryption", "Encryption"),
            indigo.activePlugin.getDeviceStateDictForNumberType("bthome-version", "BTHome Version", "BTHome Version"),
            indigo.activePlugin.getDeviceStateDictForNumberType("pid", "Last Packet ID", "Last Packet ID"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rssi", "rssi", "rssi"),
            indigo.activePlugin.getDeviceStateDictForStringType("address", "MAC Address", "MAC Address")
        ]
    
    def get_device_display_state_id(self):
        """
        Determine which device state should be shown in the device list.

        :return: The state name.
        """
        return indigo.PluginBase.getDeviceDisplayStateId(indigo.activePlugin, self.device)
    
    def process_packet(self, packet: dict):
        if packet.get("pid", -1) == self.device.states.get("pid", -1):
            self.logger.debug(f"Not processing duplicated packet: {packet}")
            return

        state_updates = []

        state_updates.append({'key': "encryption", 'value': packet.get("encryption", False)})
        state_updates.append({'key': "bthome-version", 'value': packet.get("BTHome_version", -1)})
        state_updates.append({'key': "pid", 'value': packet.get("pid", -1)})
        state_updates.append({'key': "rssi", 'value': packet.get("rssi", 999)})
        state_updates.append({'key': "address", 'value': packet.get("address", "UNKNOWN")})

        self.device.updateStatesOnServer(state_updates)