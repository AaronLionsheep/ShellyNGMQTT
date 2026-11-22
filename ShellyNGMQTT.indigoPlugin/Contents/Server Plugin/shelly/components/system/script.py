from typing import TYPE_CHECKING, TypedDict

from ..component import Component

if TYPE_CHECKING:
    from ...scripts.managed_script import ManagedScript


class ScriptConfig(TypedDict):
    id: int | None
    name: str | None
    enable: bool


class Script(Component):
    """
    The Script component manages individual scripts on a device.
    """

    component_type = "script"
    device_type_id = ""

    def __init__(self, shelly):
        """
        Create a Script component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        """
        super().__init__(shelly, comp_id=-1)
        self.managed_scripts: list[ManagedScript] = []

    def create(self, name: str, callback):
        """
        Create a new script on the device with the given name.

        Parameters
        ----------
        name: str
            The name of the script to create.
        """
        self.shelly.publish_rpc("Script.Create", {"name": name}, callback)

    def list(self, callback):
        """
        List out scripts already on the device.
        """
        self.shelly.publish_rpc("Script.List", {}, callback)

    def get_status(self, id: int = -1, callback=None):
        """
        Get the status for a script.

        Parameters
        ----------
        id: int | None
            The identifier of the script whose status should be fetched. No action is
            performed when a negative number is provided.
        """
        if id < 0:
            return

        self.shelly.publish_rpc("Script.GetStatus", {"id": id}, callback)

    def process_status(self, status):
        self.logger.debug(f"{self.shelly.device.name} script status: {status}")

    def get_config(self, id: int = -1, callback=None):
        """
        Get the config for a script.

        Parameters
        ----------
        id: int | None
            The identifier of the script whose config should be fetched. No action is
            performed when a negative number is provided.
        """
        if id < 0:
            return

        self.shelly.publish_rpc("Script.GetConfig", {"id": id}, callback)

    def set_config(self, id: int, name: str, enable: bool, callback):
        """
        Set the configuration for a script.

        :param config: A system config to upload to the device.
        :return: None
        """
        payload = {"id": id, "config": {"id": id, "name": name, "enable": enable}}
        self.shelly.publish_rpc("Script.SetConfig", payload, callback)

    def start(self, id: int, callback):
        """
        Start a script.
        """
        self.shelly.publish_rpc("Script.Start", {"id": id}, callback)

    def stop(self, id: int, callback):
        """
        Stop a script.
        """
        self.shelly.publish_rpc("Script.Stop", {"id": id}, callback)

    def put_code(self, id: int, code: str, append: bool, callback):
        """
        Put code into the script.

        Multiple chunks must be uploaded if the total code length is greater than 1024
        bytes. The script must also be stopped.
        """
        self.logger.debug(
            f"Uploading {len(code)} bytes to script:{id} on {self.shelly.device.name}..."
        )
        self.shelly.publish_rpc(
            "Script.PutCode", {"id": id, "code": code, "append": append}, callback
        )

    def handle_notify_event(self, event):
        super().handle_notify_event(event)

        # We expect the event to be a dict with well-known keys
        if not isinstance(event, dict):
            self.logger.error(
                f"{self.shelly.device.name} received a malformed event."
                f" Expected a dict, but got {type(event)}: {event}"
            )
            return

        for managed_script in self.managed_scripts:
            managed_script.handle_notify_event(event)
