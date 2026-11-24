from .shelly_blu_rc_button_4 import ShellyBLURCButton4


class ShellyBLUWallSwitch4ZB(ShellyBLURCButton4):
    """
    Creates a Shelly BLU Wall Switch 4 ZB device class.

    It sends the same BTHome data as the RC Button 4: battery and four buttons.
    """

    display_name = "Shelly BLU Wall Switch 4 ZB"
