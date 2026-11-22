from pathlib import Path

RELAY_SCRIPT = Path(__file__).parents[5] / "Resources" / "indigo-blu-relay.js"


def test_relay_script_fits_in_one_chunk():
    """The BLU relay script stays under 1024 bytes so it uploads in a single Script.PutCode call"""
    assert len(RELAY_SCRIPT.read_bytes()) < 1024
