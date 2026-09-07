import pytest
from shelly.devices.ShellyBLU import BLEData, BLERelayPacket


class TestBLERelayPacket:
    def test_from_mqtt_event(self):
        packet = BLERelayPacket.from_mqtt_event(
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
            address="b0:c7:de:04:1c:ff",
            rssi=-77,
            service_data={
                "0000fcd2-0000-1000-8000-00805f9b34fb": b"D\x00P\x01d.5E\xef\x00"
            },
            timestamp=0,
        )

    def test_from_mqtt_event_converts_bthome_uuid(self):
        packet = BLERelayPacket.from_mqtt_event(
            timestamp=0,
            event_data={
                "address": "b0:c7:de:04:1c:ff",
                "rssi": -77,
                "service_data": {"fcd2": "44005001642e3545ef00"},
            },
        )
        assert packet == BLERelayPacket(
            version=1,
            address="b0:c7:de:04:1c:ff",
            rssi=-77,
            service_data={
                "0000fcd2-0000-1000-8000-00805f9b34fb": b"D\x00P\x01d.5E\xef\x00"
            },
            timestamp=0,
        )


class TestBleData:
    @pytest.fixture()
    def data(self) -> BLEData:
        return BLEData(
            address="00:00:00:00:00:00", rssi=0, sensors={"battery": 94}, events={}
        )

    class TestSensorContextManager:
        def test_sensor_returns_value(self, data):
            """A sensor value should be returned"""
            with data.sensor("battery") as battery:
                assert battery == 94

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
