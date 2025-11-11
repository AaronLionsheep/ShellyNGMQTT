import indigo
import os

from ..component import Component

from ...devices.ShellyBLU import ShellyBLU, BLEPacketAlreadyProcessed

from typing import TypedDict


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
        super(Script, self).__init__(shelly, comp_id=-1)

        if shelly.device.pluginProps.get("blu-relay", False):
            self.logger.info(f"Enabling relay for {shelly.device.name}...")
            script_name = "indigo-blu-relay.js"
            script_path = os.path.join(indigo.activePlugin.pluginFolderPath, "Contents", "Resources", script_name)
            script_data = None
            with open(script_path, "r", encoding="utf-8") as script_file:
                script_data = script_file.read()

            if not script_data:
                self.logger.error("Problem reading script data!")
                return
            else:
                self.logger.info(f"Read {len(script_data)} bytes of script data")

            def inspect_scripts(list_response, error=None):
                if error:
                    self.logger.error(f"Unable to get current device scripts: {error['message']}")
                    return

                scripts = list_response.get("scripts", [])
                for script in scripts:
                    if script["name"] == script_name:
                        self.logger.info(f"Found existing script {script}")
                        upload(script)
                        return
                
                self.logger.info("Creating new script...")
                self.create(script_name, upload)

            def upload(script, error=None):
                if error:
                    self.logger.error(f"Unable to get/create script: {error['message']}")
                    return
                
                id = script["id"]
                self.upload_script(id, code=script_data, callback=enable_and_start)

            def enable_and_start(script, error=None):
                if error:
                    self.logger.error(f"Unable to upload script: {error['message']}")
                    return
                
                id = script["id"]
                self.logger.info("Configuring script...")

                def start(response, error=None):
                    if error:
                        self.logger.error(f"Unable to set script config: {error['message']}")
                        return
                    
                    self.start(id, callback=complete)

                self.set_config(id, name=script_name, enable=True, callback=start)

            def complete(response, error=None):
                if error:
                    self.logger.error(f"Error occurred during script management: {error['message']}")
                    return
                
                self.logger.info("Script is synced, running, and configured to run at device boot")

            self.list(inspect_scripts)

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
        self.logger.info(f"{self.shelly.device.name} script status: {status}")

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
        payload = {
            "id": id,
            "config": {
                "id": id,
                "name": name,
                "enable": enable
            }
        }
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
        self.logger.info(f"Uploading {len(code)} bytes to script:{id}...")
        self.shelly.publish_rpc(
            "Script.PutCode",
            {
                "id": id,
                "code": code,
                "append": append
            },
            callback
        )

    def upload_script(self, id: int, code: str, callback=None):
        """
        A helper utility to upload an entire script as multiple chunks.
        """        
        chunk_size = 1024
        chunks: list[str] = []
        for i in range(0, len(code), chunk_size):
            chunks.append({
                "id": i / chunk_size,
                "code": code[i:i+chunk_size]
            })

        def upload_chunks(status, error=None):
            if error:
                self.logger.error(f"Unable to upload script data chunk: {error['message']}")
                return

            if len(chunks) > 0:
                chunk = chunks.pop(0)
                chunk_id = chunk["id"]
                append = chunk_id != 0
                code = chunk["code"]
                self.put_code(id, code=code, append=append, callback=upload_chunks)
            elif callback:
                callback({"id": id})

        self.stop(id, callback=upload_chunks)

    def handle_notify_event(self, event):
        super(Script, self).handle_notify_event(event)

        if event.get("name", "") == "shelly-blu":
            packet = event.get("data", {})
            self.logger.debug(f"{self.shelly.device.name}:{event['name']}: {packet}")
            address = packet.get("address", None)
            indigo.activePlugin.discovered_blu_addresses.add(address)

            shelly_blu_dev_id = indigo.activePlugin.blu_address_device.get(address, None)
            if not shelly_blu_dev_id:
                return
            
            shelly_blu = indigo.activePlugin.shellies.get(shelly_blu_dev_id, None)
            if not shelly_blu or not isinstance(shelly_blu, ShellyBLU):
                return

            try:
                shelly_blu.process_packet(packet)
            except BLEPacketAlreadyProcessed:
                return