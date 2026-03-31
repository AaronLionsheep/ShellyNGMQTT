import indigo # noqa

from bthome_ble.parser import BTHomeBluetoothDeviceData, UuidType
from habluetooth import BluetoothServiceInfoBleak
from typing import Any, Final
from dataclasses import dataclass
from contextlib import contextmanager

from .Shelly import Shelly

_UNSET: Final = object()

@dataclass
class BLERelayPacket:
    """A BLE packet relayed from another device."""
    address: str
    rssi: int
    service_data: dict[str, bytes]
    timestamp: float

    @classmethod
    def from_mqtt_event(cls, timestamp: float, event_data: dict):
        address = event_data["address"]
        rssi = event_data["rssi"]
        service_data = event_data["service_data"]

        # Convert short BTHome V2 service UUID to the long format
        if "fcd2" in service_data:
            service_data[UuidType.V2.value] = service_data.pop("fcd2")

        return cls(
            address=address,
            rssi=rssi,
            service_data={
                service: bytes.fromhex(data)
                for service, data in service_data.items()
            },
            timestamp=timestamp
        )


@dataclass
class BLEData:
    """Data processed from a BLE packet."""
    address: str
    rssi: int
    sensors: dict[str, Any]
    events: dict[str, Any]

    @contextmanager
    def sensor(self, name: str, required: bool = False, default: Any = _UNSET):
        if name not in self.sensors:
            if required:
                raise KeyError(f"Sensor '{name}' not found in BLE Data")
            
            if default is not _UNSET:
                yield default
        else:
            yield self.sensors[name]


class BLEPacketAlreadyProcessed(Exception):
    """A BLE Packet was already processed."""
    ...


class ShellyBLU(Shelly):
    """
    Base class used by all Shelly BLU model classes.
    """

    display_name = "ShellyBLUBase"

    def __init__(self, device_id):
        """Create a new Shelly BLU device.

        :param device_id: The indigo device id.
        """
        super(ShellyBLU, self).__init__(device_id)
        self.ble = BTHomeBluetoothDeviceData()

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        """Default pluginProps that all devices of this class will have."""
        return {}

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
        states = super(ShellyBLU, self).get_device_state_list()
        states.extend ([
            indigo.activePlugin.getDeviceStateDictForNumberType("pid", "Last Packet ID", "Last Packet ID"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rssi", "Signal Strength", "Signal Strength"),
            indigo.activePlugin.getDeviceStateDictForStringType("address", "MAC Address", "MAC Address")
        ])
        return states
    
    def parse_packet(self, packet: BLERelayPacket) -> BLEData:
        """
        Parse the raw BLE data from a BLE Relay packet.
        """
        update = self.ble.update(BluetoothServiceInfoBleak(
            name=self.device.name,
            address=packet.address,
            rssi=packet.rssi,
            manufacturer_data={},
            service_data=packet.service_data,
            service_uuids=list(packet.service_data.keys()),
            source="",
            device=None, 
            advertisement=None,
            connectable=False,
            time=packet.timestamp,
            tx_power=None
        ))

        return BLEData(
            address=packet.address,
            rssi=packet.rssi,
            sensors=dict(
                **{
                    sensor.device_key.key: sensor.native_value
                    for sensor in update.entity_values.values()
                },
                **{
                    sensor.device_key.key: sensor.native_value
                    for sensor in update.binary_entity_values.values()
                }
            ),
            events=dict(
                **{
                    event.device_key.key: event.event_type
                    for event in update.events.values()
                }
            )
        )
    
    def process_ble_data(self, data: BLEData):
        """
        Process BLE data.
        """
        self.logger.info(data)

        state_updates = []
        state_updates.append({'key': "pid", 'value': data.sensors.get("packet_id", -1)})
        state_updates.append({'key': "rssi", 'value': data.rssi})
        state_updates.append({'key': "address", 'value': data.address})
        self.device.updateStatesOnServer(state_updates)

    def handle_ble_relay_packet(self, packet: BLERelayPacket):
        ble_data = self.parse_packet(packet)
        self.process_ble_data(ble_data)
        self.update_state_image()
    