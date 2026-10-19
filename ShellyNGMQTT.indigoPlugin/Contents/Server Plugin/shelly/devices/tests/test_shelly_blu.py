import pytest
from shelly.devices.ShellyBLU import (
    BTHOME_MEAS_TYPES,
    BLEData,
    BLERelayPacket,
    BTHomeDeviceInfo,
)

# Unencrypted BTHome V2 payload: packet id, battery, humidity, temperature
SENSOR_PAYLOAD = "44005001642e3545ef00"


def parse(payload: str) -> BTHomeDeviceInfo:
    return BTHomeDeviceInfo.from_payload(bytes.fromhex(payload))


class TestBTHomeMeasTypes:
    @pytest.mark.parametrize(
        ("object_id", "data_length", "data_format"),
        [
            pytest.param(0xF0, 2, "device_type_id", id="device-type-id"),
            pytest.param(0xF1, 4, "firmware_version_4", id="firmware-version-4"),
            pytest.param(0xF2, 3, "firmware_version_3", id="firmware-version-3"),
        ],
    )
    def test_device_info_meas_types(self, object_id, data_length, data_format):
        meas_type = BTHOME_MEAS_TYPES[object_id]
        assert meas_type.data_length == data_length
        assert meas_type.data_format == data_format

    def test_includes_bthome_ble_meas_types(self):
        """Object definitions from bthome-ble are used for all other objects"""
        assert BTHOME_MEAS_TYPES[0x45].data_length == 2
        assert BTHOME_MEAS_TYPES[0x53].data_format == "string"
        assert BTHOME_MEAS_TYPES[0x54].data_format == "raw"


class TestBTHomeDeviceInfo:
    def test_defaults(self):
        info = BTHomeDeviceInfo()
        assert info.device_type_id is None
        assert info.firmware_version is None

    def test_frozen(self):
        info = BTHomeDeviceInfo()
        with pytest.raises(AttributeError):
            info.firmware_version = "1.0.0"  # pyright: ignore[reportAttributeAccessIssue]

    class TestFirmwareVersion:
        @pytest.mark.parametrize(
            ("payload", "expected"),
            [
                pytest.param(SENSOR_PAYLOAD + "f101020301", "1.3.2.1", id="4-byte"),
                pytest.param(SENSOR_PAYLOAD + "f2010203", "3.2.1", id="3-byte"),
                pytest.param("44f101020301", "1.3.2.1", id="4-byte-only-object"),
                pytest.param("44f2010203", "3.2.1", id="3-byte-only-object"),
                pytest.param("44f100000000", "0.0.0.0", id="4-byte-zeros"),
                pytest.param("44f2ff00ff", "255.0.255", id="3-byte-max-components"),
            ],
        )
        def test_firmware_version(self, payload, expected):
            """The firmware version components are read least significant first"""
            assert parse(payload) == BTHomeDeviceInfo(firmware_version=expected)

        def test_first_firmware_object_is_used(self):
            """The first firmware version object wins when more than one is sent"""
            assert parse("44f101020301f2040506").firmware_version == "1.3.2.1"

        def test_missing_firmware_version(self):
            assert parse(SENSOR_PAYLOAD).firmware_version is None

    class TestDeviceTypeId:
        @pytest.mark.parametrize(
            ("payload", "expected"),
            [
                pytest.param("44f00100", 1, id="low-byte"),
                pytest.param("44f00001", 256, id="high-byte"),
                pytest.param("44f03412", 0x1234, id="little-endian"),
                pytest.param("44f00000", 0, id="zero"),
                pytest.param("44f0ffff", 0xFFFF, id="max"),
                pytest.param(SENSOR_PAYLOAD + "f00200", 2, id="after-sensors"),
            ],
        )
        def test_device_type_id(self, payload, expected):
            """The device type id is a little-endian unsigned 16-bit integer"""
            assert parse(payload) == BTHomeDeviceInfo(device_type_id=expected)

        def test_first_device_type_id_is_used(self):
            assert parse("44f00100f00200").device_type_id == 1

        def test_missing_device_type_id(self):
            assert parse(SENSOR_PAYLOAD).device_type_id is None

    class TestCombined:
        def test_device_type_id_and_firmware_version(self):
            assert parse(SENSOR_PAYLOAD + "f00100" + "f101020301") == BTHomeDeviceInfo(
                device_type_id=1, firmware_version="1.3.2.1"
            )

        def test_all_device_information_objects(self):
            assert parse("44" + "f00900" + "f101020301" + "f2040506") == BTHomeDeviceInfo(
                device_type_id=9, firmware_version="1.3.2.1"
            )

        def test_out_of_order_objects(self):
            """Objects are still parsed when not sent in ascending object id order"""
            assert parse("44" + "f2040506" + "f00100" + "0164") == BTHomeDeviceInfo(
                device_type_id=1, firmware_version="6.5.4"
            )

    class TestDeviceInformationByte:
        def test_trigger_based_flag(self):
            """The trigger based flag (bit 2) does not prevent parsing"""
            assert parse("40f2010203").firmware_version == "3.2.1"

        def test_encrypted_payload(self):
            """Encrypted payloads (bit 0 of the device info byte) can't be parsed"""
            assert parse("45f00100f101020301") == BTHomeDeviceInfo()

        @pytest.mark.parametrize(
            "device_info",
            [
                pytest.param("04", id="version-0"),
                pytest.param("24", id="version-1"),
                pytest.param("64", id="version-3"),
                pytest.param("e4", id="version-7"),
            ],
        )
        def test_non_v2_payload(self, device_info):
            """Only BTHome V2 payloads (bits 5-7 of the device info byte) are parsed"""
            assert parse(device_info + "f00100f101020301") == BTHomeDeviceInfo()

        def test_empty_payload(self):
            assert parse("") == BTHomeDeviceInfo()

        def test_device_info_byte_only(self):
            assert parse("44") == BTHomeDeviceInfo()

    class TestObjectIdInData:
        """A device information object id within another object's data is not mistaken for an object"""

        def test_fixed_length_object_containing_firmware_version_id(self):
            # Temperature (0x45) with a value of f1 02
            assert parse("4445f102") == BTHomeDeviceInfo()

        def test_fixed_length_object_containing_device_type_id(self):
            # Temperature (0x45) with a value of f0 01
            assert parse("4445f001") == BTHomeDeviceInfo()

        def test_fixed_length_object_before_firmware(self):
            assert parse("4445f102" + "f2010203").firmware_version == "3.2.1"

        def test_multi_byte_object_hides_object_ids(self):
            # Packet id (0x00) of f1, then a temperature (0x45) of f2 f0
            assert parse("4400f145f2f0" + "f101020301") == BTHomeDeviceInfo(
                firmware_version="1.3.2.1"
            )

        def test_device_info_object_hides_object_ids(self):
            # A device type id with a value containing the f1 and f2 object ids
            assert parse("44f0f1f2" + "f2010203") == BTHomeDeviceInfo(
                device_type_id=0xF2F1, firmware_version="3.2.1"
            )

        def test_string_object(self):
            # Text (0x53) with a length of 4 containing an f1 object
            assert parse("4453" + "04" + "f1010203") == BTHomeDeviceInfo()

        def test_string_object_before_firmware(self):
            assert parse("4453" + "04" + "f1010203" + "f2040506").firmware_version == "6.5.4"

        def test_raw_object_before_device_info(self):
            # Raw (0x54) with a length of 3 containing an f0 object
            payload = "4454" + "03" + "f00100" + "f00200" + "f101020301"
            assert parse(payload) == BTHomeDeviceInfo(
                device_type_id=2, firmware_version="1.3.2.1"
            )

        def test_empty_string_object(self):
            assert parse("4453" + "00" + "f2010203").firmware_version == "3.2.1"

    class TestMalformedPayload:
        @pytest.mark.parametrize(
            "payload",
            [
                pytest.param("44f1", id="4-byte-no-data"),
                pytest.param("44f1010203", id="4-byte-short-data"),
                pytest.param("44f2", id="3-byte-no-data"),
                pytest.param("44f20102", id="3-byte-short-data"),
                pytest.param("44f0", id="device-type-id-no-data"),
                pytest.param("44f001", id="device-type-id-short-data"),
            ],
        )
        def test_truncated_device_information(self, payload):
            """A device information object with missing data is ignored"""
            assert parse(payload) == BTHomeDeviceInfo()

        def test_truncated_object_after_device_information(self):
            """Device information found before a truncated object is kept"""
            assert parse("44f00100" + "f10102") == BTHomeDeviceInfo(device_type_id=1)

        def test_truncated_object_before_device_information(self):
            # Temperature (0x45) expects 2 bytes, leaving only 1 byte of an f2 object
            assert parse("4445f2") == BTHomeDeviceInfo()

        def test_string_object_missing_length(self):
            assert parse("4453") == BTHomeDeviceInfo()

        def test_string_object_length_exceeds_payload(self):
            assert parse("4453" + "0a" + "f2010203") == BTHomeDeviceInfo()

        def test_unknown_object_before_device_information(self):
            """Parsing stops at an object id with an unknown length"""
            assert parse("44ee" + "f00100f2010203") == BTHomeDeviceInfo()

        def test_unknown_object_after_device_information(self):
            """Device information found before an unknown object id is kept"""
            assert parse("44f00100f2010203" + "ee") == BTHomeDeviceInfo(
                device_type_id=1, firmware_version="3.2.1"
            )


class TestBLERelayPacket:
    def test_from_mqtt_event(self):
        packet = BLERelayPacket.from_mqtt_event(
            relay_device_id=1,
            timestamp=0,
            event_data={
                "address": "b0:c7:de:04:1c:ff",
                "rssi": -77,
                "service_data": {
                    "0000fcd2-0000-1000-8000-00805f9b34fb": "44005001642e3545ef00"
                },
            },
        )
        assert packet == BLERelayPacket(
            version=1,
            relay_device_id=1,
            address="b0:c7:de:04:1c:ff",
            rssi=-77,
            service_data={
                "0000fcd2-0000-1000-8000-00805f9b34fb": b"D\x00P\x01d.5E\xef\x00"
            },
            timestamp=0,
        )

    def test_from_mqtt_event_converts_bthome_uuid(self):
        packet = BLERelayPacket.from_mqtt_event(
            relay_device_id=1,
            timestamp=0,
            event_data={
                "address": "b0:c7:de:04:1c:ff",
                "rssi": -77,
                "service_data": {"fcd2": "44005001642e3545ef00"},
            },
        )
        assert packet == BLERelayPacket(
            version=1,
            relay_device_id=1,
            address="b0:c7:de:04:1c:ff",
            rssi=-77,
            service_data={
                "0000fcd2-0000-1000-8000-00805f9b34fb": b"D\x00P\x01d.5E\xef\x00"
            },
            timestamp=0,
        )

    def test_str(self):
        packet = BLERelayPacket.from_mqtt_event(
            relay_device_id=1,
            timestamp=0,
            event_data={
                "address": "b0:c7:de:04:1c:ff",
                "rssi": -77,
                "service_data": {
                    "0000fcd2-0000-1000-8000-00805f9b34fb": "44005001642e3545ef00"
                },
            },
        )
        print(packet.service_data)
        assert (
            str(packet)
            == "BLERelayPacket(version=1, relay_device_id=1, address='b0:c7:de:04:1c:ff', rssi=-77, service_data={'0000fcd2-0000-1000-8000-00805f9b34fb': '44005001642e3545ef00'}, timestamp=0)"
        )


class TestBleData:
    @pytest.fixture()
    def packet(self) -> BLERelayPacket:
        return BLERelayPacket.from_mqtt_event(
            relay_device_id=1,
            timestamp=0,
            event_data={
                "version": 1,
                "address": "b0:c7:de:04:1c:ff",
                "rssi": -77,
                "service_data": {"fcd2": "44004b01642e3745f200"},
            },
        )

    @pytest.fixture()
    def data(self, packet) -> BLEData:
        return BLEData(
            packet=packet,
            sensors={
                "packet_id": 75,
                "battery": 100,
                "humidity": 55,
                "temperature": 24.2,
                "signal_strength": -77,
            },
            events={},
            device_info=BTHomeDeviceInfo(device_type_id=1, firmware_version="1.3.2.1"),
        )

    def test_address(self, data):
        assert data.address == "b0:c7:de:04:1c:ff"

    def test_rssi(self, data):
        assert data.rssi == -77

    def test_device_info(self, data):
        assert data.device_info == BTHomeDeviceInfo(
            device_type_id=1, firmware_version="1.3.2.1"
        )

    class TestSensorContextManager:
        def test_sensor_returns_value(self, data):
            """A sensor value should be returned"""
            with data.sensor("battery") as battery:
                assert battery == 100

        def test_sensor_missing_required_raise_key_error(self, data):
            """A required sensor value that is missing should raise a KeyError"""
            with (
                pytest.raises(KeyError, match="Sensor 'missing' not found in BLE Data"),
                data.sensor("missing", required=True) as value,
            ):
                pytest.fail(
                    f"The context manager should not have been entered. Entered with value of '{value}'"
                )

        def test_sensor_missing_optional_returns_default(self, data):
            """An optional missing sensor should return a default value"""
            with data.sensor("missing", default="MISSING") as value:
                assert value == "MISSING"

        def test_sensor_missing_optional_returns_default_none(self, data):
            """An optional missing sensor should return None by default"""
            with data.sensor("missing") as value:
                assert value is None
