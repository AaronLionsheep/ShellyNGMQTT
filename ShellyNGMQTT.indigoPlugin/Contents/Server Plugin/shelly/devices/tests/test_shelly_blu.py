from pytest_indigo import IndigoMock
import pytest
from shelly.devices.ShellyBLU import BLERelayPacket, BLEData

class TestBLERelayPacket:
    pass


class TestBleData:
    @pytest.fixture()
    def data(self) -> BLEData:
        return BLEData(address="00:00:00:00:00:00", rssi=0, sensors={"battery": 94}, events={})

    class TestSensorContextManager:
        def test_sensor_returns_value(self, data):
            """A sensor value should be returned"""
            with data.sensor("battery") as battery:
                assert battery == 94

        def test_sensor_missing_required_raise_key_error(self, data):
            """A required sensor value that is missing should raise a KeyError"""
            with pytest.raises(KeyError, match="Sensor 'missing' not found in BLE Data"):
                with data.sensor("missing", required=True) as value:
                    pytest.fail(f"The context manager should not have been entered. Entered with value of '{value}'")

        def test_sensor_missing_optional_returns_default(self, data):
            """An optional missing sensor should return a default value"""
            with data.sensor("missing", default="MISSING") as value:
                assert value == "MISSING"

        def test_sensor_missing_optional_returns_default_none(self, data):
            """An optional missing sensor should return None by default"""
            with data.sensor("missing") as value:
                assert value is None
