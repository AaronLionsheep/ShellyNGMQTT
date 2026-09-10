from .ShellyPlus2PM import ShellyPlus2PM


class ShellyPlus2PMGen3(ShellyPlus2PM):
    """
    Shelly Plus 2 PM Gen3 — same API as Plus 2 PM, different hardware generation.
    Supports profile=switch and profile=cover (roller/shutter).
    """

    display_name = "Shelly Plus 2 PM Gen3"
