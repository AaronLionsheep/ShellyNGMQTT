from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]
from bthome_ble.parser import BTHomeBluetoothDeviceData, UuidType
from habluetooth import BluetoothServiceInfoBleak

from .Shelly import Shelly


class ServiceData(dict[str, bytes]):
    def __repr__(self):
        items = []
        for key, value in self.items():
            items.append(f"'{key}': '{value.hex()}'")

        return f"{{{', '.join(items)}}}"


@dataclass
class BLERelayPacket:
    """A BLE packet relayed from another device."""

    version: int
    relay_device_id: int
    address: str
    rssi: int
    service_data: ServiceData
    timestamp: float

    @classmethod
    def from_mqtt_event(cls, relay_device_id: int, timestamp: float, event_data: dict):
        version = int(event_data.get("version", 1))
        address = event_data["address"]
        rssi = event_data["rssi"]
        service_data = event_data["service_data"]

        # Convert short BTHome V2 service UUID to the long format
        if "fcd2" in service_data:
            service_data[UuidType.V2.value] = service_data.pop("fcd2")

        return cls(
            version=version,
            relay_device_id=relay_device_id,
            address=address,
            rssi=rssi,
            service_data=ServiceData(
                {service: bytes.fromhex(data) for service, data in service_data.items()}
            ),
            timestamp=timestamp,
        )


@dataclass
class BLEData:
    """Data processed from a BLE packet."""

    packet: BLERelayPacket
    sensors: dict[str, Any]
    events: dict[str, dict[str, Any]]

    @property
    def address(self) -> str:
        return self.packet.address

    @property
    def rssi(self) -> int:
        return self.packet.rssi

    # I don't recall why this is a contextmanager.
    # I think it was only to make readability better when parsing each sensor value.
    @contextmanager
    def sensor(self, name: str, required: bool = False, default: Any = None):
        if name not in self.sensors:
            if required:
                raise KeyError(f"Sensor '{name}' not found in BLE Data")

            yield default
        else:
            yield self.sensors[name]


class ShellyBLU(Shelly):
    """
    Base class used by all Shelly BLU model classes.
    """

    display_name = "ShellyBLUBase"
    button_count = 0

    def __init__(self, device_id):
        """Create a new Shelly BLU device.

        :param device_id: The indigo device id.
        """
        super().__init__(device_id)
        self.ble = BTHomeBluetoothDeviceData()

    @classmethod
    def plugin_props(cls) -> dict[str, Any]:
        """Default pluginProps that all devices of this class will have."""
        return {}

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
        states = super().get_device_state_list()
        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "pid", "Last Packet ID", "Last Packet ID"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "rssi", "Signal Strength", "Signal Strength"
                ),
                indigo.activePlugin.getDeviceStateDictForStringType(
                    "address", "MAC Address", "MAC Address"
                ),
            ]
        )
        return states

    def parse_packet(self, packet: BLERelayPacket) -> BLEData:
        """
        Parse the raw BLE data from a BLE Relay packet.
        """
        update = self.ble.update(
            BluetoothServiceInfoBleak(
                name=self.device.name,
                address=packet.address,
                rssi=packet.rssi,
                manufacturer_data={},
                service_data=dict(packet.service_data),
                service_uuids=list(packet.service_data.keys()),
                source="",
                device=None,
                advertisement=None,
                connectable=False,
                time=packet.timestamp,
                tx_power=None,
            )
        )

        return BLEData(
            packet=packet,
            sensors=dict(
                **{
                    sensor.device_key.key: sensor.native_value
                    for sensor in update.entity_values.values()
                },
                **{
                    sensor.device_key.key: sensor.native_value
                    for sensor in update.binary_entity_values.values()
                },
            ),
            events=dict(
                **{
                    event.device_key.key: {event.event_type: event.event_properties}
                    for event in update.events.values()
                }
            ),
        )

    def process_ble_data(self, data: BLEData):
        """
        Process BLE data.
        """
        if indigo.activePlugin.pluginPrefs.get("debug-ble-activity", False):
            relay_device_name = "<Unknown>"
            if relay_device := indigo.devices.get(data.packet.relay_device_id):
                relay_device_name = relay_device.name
            self.logger.info(
                f"{self.device.name} processing BLE data from {relay_device_name} ({data.packet.rssi} dBm): sensors={data.sensors} events={data.events}"
            )

        state_updates = []
        state_updates.append({"key": "pid", "value": data.sensors.get("packet_id", -1)})
        state_updates.append({"key": "rssi", "value": data.rssi})
        state_updates.append({"key": "address", "value": data.address})
        self.device.updateStatesOnServer(state_updates)

    def handle_ble_relay_packet(self, packet: BLERelayPacket):
        ble_data = self.parse_packet(packet)
        self.process_ble_data(ble_data)
        self.update_state_image()
