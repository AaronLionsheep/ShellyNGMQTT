import pytest
from shelly.devices.ShellyBLU import BLEData, BLERelayPacket


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
        )

    def test_address(self, data):
        assert data.address == "b0:c7:de:04:1c:ff"

    def test_rssi(self, data):
        assert data.rssi == -77

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
