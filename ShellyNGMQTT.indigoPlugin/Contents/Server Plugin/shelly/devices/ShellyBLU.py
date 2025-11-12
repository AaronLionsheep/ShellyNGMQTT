import indigo # noqa
import json
import logging
import uuid

from .Shelly import Shelly


class BLEPacketAlreadyProcessed(Exception):
    """A BLE Packet was already processed."""
    ...

class ShellyBLU(object):
    """
    Base class used by all Shelly BLU model classes.
    """

    display_name = "ShellyBLUBase"

    def __init__(self, device_id):
        """Create a new Shelly BLU device.

        :param device_id: The indigo device id.
        """
        super(Shelly, self).__init__(device_id)

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
        states = super(Shelly, self).get_device_state_list()
        states.extend ([
            indigo.activePlugin.getDeviceStateDictForBoolTrueFalseType("encryption", "Encryption", "Encryption"),
            indigo.activePlugin.getDeviceStateDictForNumberType("bthome-version", "BTHome Version", "BTHome Version"),
            indigo.activePlugin.getDeviceStateDictForNumberType("pid", "Last Packet ID", "Last Packet ID"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rssi", "rssi", "rssi"),
            indigo.activePlugin.getDeviceStateDictForStringType("address", "MAC Address", "MAC Address")
        ])
        return states
    
    def process_packet(self, packet: dict):
        pid = packet.get("pid", -1)
        if pid == self.device.states.get("pid", -1):
            self.logger.debug(f"Not processing duplicated packet: {packet}")
            raise BLEPacketAlreadyProcessed(f"BLE packet (pid={pid}) already processed!")

        state_updates = []

        state_updates.append({'key': "encryption", 'value': packet.get("encryption", False)})
        state_updates.append({'key': "bthome-version", 'value': packet.get("BTHome_version", -1)})
        state_updates.append({'key': "pid", 'value': packet.get("pid", -1)})
        state_updates.append({'key': "rssi", 'value': packet.get("rssi", 999)})
        state_updates.append({'key': "address", 'value': packet.get("address", "UNKNOWN")})

        self.device.updateStatesOnServer(state_updates)