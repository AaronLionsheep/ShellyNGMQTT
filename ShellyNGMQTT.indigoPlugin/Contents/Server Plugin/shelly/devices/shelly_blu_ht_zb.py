from .shelly_blu_ht import ShellyBLUHT


class ShellyBLUHTZB(ShellyBLUHT):
    """
    Creates a Shelly BLU H&T ZB device class.

    It broadcasts the same BTHome data as the BLU H&T.
    """

    display_name = "Shelly BLU H&T ZB"
