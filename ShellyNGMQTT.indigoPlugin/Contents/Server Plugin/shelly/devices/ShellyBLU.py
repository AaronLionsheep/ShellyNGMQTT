from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]
from bthome_ble.const import MEAS_TYPES, MeasTypes
from bthome_ble.parser import BTHomeBluetoothDeviceData, UuidType
from habluetooth import BluetoothServiceInfoBleak

from .Shelly import Shelly

BUTTON_TRIGGER_TYPES = {
    "press": "single-push",
    "double_press": "double-push",
    "triple_press": "triple-push",
    "long_press": "long-push",
    "hold_press": "hold-push",
}

# BTHome device information objects, matching their definitions in bthome-ble>=3.24.
# These are not parsed by bthome-ble<3.24, which is required to support intel macs.
DEVICE_INFO_MEAS_TYPES = {
    0xF0: MeasTypes(
        meas_format=None,  # pyright: ignore[reportArgumentType]
        data_length=2,
        data_format="device_type_id",
    ),
    0xF1: MeasTypes(
        meas_format=None,  # pyright: ignore[reportArgumentType]
        data_length=4,
        data_format="firmware_version_4",
    ),
    0xF2: MeasTypes(
        meas_format=None,  # pyright: ignore[reportArgumentType]
        data_length=3,
        data_format="firmware_version_3",
    ),
}
BTHOME_MEAS_TYPES = {**MEAS_TYPES, **DEVICE_INFO_MEAS_TYPES}


@dataclass(frozen=True)
class BTHomeDeviceInfo:
    """Device information objects sent in a BTHome payload."""

    device_type_id: int | None = None
    firmware_version: str | None = None

    @classmethod
    def from_payload(cls, payload: bytes) -> "BTHomeDeviceInfo":
        """
        Extract the device type id and firmware version from an unencrypted BTHome V2 payload.

        The payload is walked object by object, since a device information object id
        may also appear as a byte within another object's data. Parsing stops at the
        first malformed or unknown object, keeping anything found before it.

        :param payload: The BTHome service data, starting with the device information byte.
        :return: The device information found in the payload.
        """
        device_type_id = None
        firmware_version = None

        # Skip encrypted payloads and anything other than BTHome V2
        if len(payload) < 1 or payload[0] & 0x01 or payload[0] >> 5 != 2:
            return cls()

        index = 1
        while index < len(payload):
            meas_type = BTHOME_MEAS_TYPES.get(payload[index])
            index += 1

            # The length of an unknown object can't be determined
            if meas_type is None:
                break

            length = meas_type.data_length
            if meas_type.data_format in ("raw", "string"):
                # Variable length objects are prefixed with their length
                if index >= len(payload):
                    break
                length = payload[index]
                index += 1

            data = payload[index : index + length]
            index += length
            if len(data) < length:
                break

            if meas_type.data_format == "device_type_id" and device_type_id is None:
                device_type_id = int.from_bytes(data, "little")
            elif (
                meas_type.data_format in ("firmware_version_4", "firmware_version_3")
                and firmware_version is None
            ):
                # Version components are sent least significant first
                firmware_version = ".".join(
                    str(component) for component in reversed(data)
                )

        return cls(device_type_id=device_type_id, firmware_version=firmware_version)


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
    device_info: BTHomeDeviceInfo

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
            device_info=BTHomeDeviceInfo.from_payload(
                packet.service_data.get(UuidType.V2.value, b"")
            ),
        )

    def process_ble_data(self, data: BLEData):
        """
        Process BLE data.
        """
        # Log BLE activity
        if indigo.activePlugin.pluginPrefs.get("debug-ble-activity", False):
            relay_device_name = "<Unknown>"
            if relay_device := indigo.devices.get(data.packet.relay_device_id):
                relay_device_name = relay_device.name
            self.logger.info(
                f"{self.device.name} processing BLE data from {relay_device_name} ({data.packet.rssi} dBm): "
                f"sensors={data.sensors} "
                f"events={data.events} "
                f"device_info={ ({'device_type_id': data.device_info.device_type_id, 'firmware_version': data.device_info.firmware_version}) } "
            )

        # Update base states from sensor data shared across all BLU devices
        state_updates = []
        state_updates.append({"key": "pid", "value": data.sensors.get("packet_id", -1)})
        state_updates.append({"key": "rssi", "value": data.rssi})
        state_updates.append({"key": "address", "value": data.address})
        self.device.updateStatesOnServer(state_updates)

        # Update device properties, only when device information is sent and has changed
        props = self.device.pluginProps
        prop_updates = {}
        if firmware_version := data.device_info.firmware_version:
            prop_updates["version"] = firmware_version

        # TODO: Use data.device_info.device_type_id to identify BLU devices.
        #  Shelly's device ids are listed at https://shelly-api-docs.shelly.cloud/docs-ble/common
        #  (ex: 0x0003 is the BLU H&T). Options:
        #  - A class attribute on each ShellyBLU model class holding its device id
        #  - A mapping table from device ids to the internal model identifiers (ex: "shelly-blu-ht")
        #  - A generated device name to show when identifying an unknown/discovered device

        if prop_updates:
            props.update(prop_updates)
            self.device.replacePluginPropsOnServer(props)

        # Fire triggers matching common event data
        self.trigger_button_events(data.events)

    def handle_ble_relay_packet(self, packet: BLERelayPacket):
        ble_data = self.parse_packet(packet)
        self.process_ble_data(ble_data)
        self.update_state_image()

    def trigger_button_events(self, events: dict[str, dict[str, Any]]):
        for event_key, event in events.items():
            # Split on the last _ and pad with None to safely extract 2 items
            event_name, index = (event_key.rsplit("_", 1) + [None])[:2]

            # Skip non-button events
            if event_name != "button":
                continue

            # Build the button id from the event index
            try:
                button_id = int(index or 1)
            except ValueError:
                self.logger.error(
                    f"Unable to parse button_id from event key: {event_key}"
                )
                continue

            # Process each event
            for event_type in event:
                trigger_type = BUTTON_TRIGGER_TYPES.get(event_type)

                if trigger_type is None:
                    self.logger.error(
                        f"No trigger type found for button event: {event_type}"
                    )
                    continue

                # Execute all matching triggers
                for trigger in indigo.activePlugin.triggers.values():
                    # Filter out triggers not matching the trigger type for the event
                    if trigger.pluginTypeId != trigger_type:
                        continue

                    # Filter out triggers not configured for this device
                    if int(trigger.pluginProps.get("device-id", -1)) != self.device.id:
                        continue

                    # Filter out triggers not matching the event's button id
                    if int(trigger.pluginProps.get("button-id", 1)) != button_id:
                        continue

                    indigo.trigger.execute(trigger)
