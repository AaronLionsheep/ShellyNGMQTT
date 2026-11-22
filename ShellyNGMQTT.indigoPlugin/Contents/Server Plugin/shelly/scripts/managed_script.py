import os
from typing import TYPE_CHECKING

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

if TYPE_CHECKING:
    from ..components.system.script import Script


class ManagedScript:
    """
    Keeps a named script on a device in sync with a script file bundled in the
    plugin's Resources folder, using the RPC primitives of a Script component.

    Subclasses set the names below, and can override `enabled` and
    `handle_notify_event`.
    """

    # Name used in log messages
    display_name: str
    # Name of the script on the device, used to find it in Script.List
    script_name: str
    # Name of the script file in the plugin's Resources folder
    file_name: str

    def __init__(self, script: "Script"):
        """
        Create a managed script and register it to receive the Script component's
        events.

        :param script: The Script component used to send RPCs to the device.
        """
        self.script = script
        self.logger = script.logger
        # Incremented by each enable or disable so older callback chains stop
        self.generation = 0
        script.managed_scripts.append(self)

    @property
    def path(self):
        """
        The local script file, which is only read when the script is enabled.
        """
        return os.path.join(
            indigo.activePlugin.pluginFolderPath,
            "Contents",
            "Resources",
            self.file_name,
        )

    @property
    def device_name(self):
        """
        The current name of the Indigo device, which may change while RPCs are pending.
        """
        return self.script.shelly.device.name

    @property
    def enabled(self):
        """
        Whether the script should be running on the device.
        """
        return True

    def sync(self):
        """
        Enable or disable the script on the device to match `enabled`.
        """
        if self.enabled:
            self.enable()
        else:
            self.disable()

    def handle_notify_event(self, event):
        """
        Handle an event from the device's Script component. Subclasses override this
        to process events emitted by their script.

        :param event: The event from the device.
        """

    def started(self):
        """
        Called after the script is synced and started. Subclasses override this to
        check that the script is working.
        """

    def _if_current_generation(self, callback):
        """
        Wrap an RPC callback so it only runs if no newer enable or disable has
        started since it was wrapped. Syncs can overlap (ex: device start and
        reconnect), and their RPCs would otherwise interleave and corrupt the
        uploaded code.

        :param callback: The RPC callback to wrap.
        """
        generation = self.generation

        def wrapped(*args):
            if generation == self.generation:
                callback(*args)

        return wrapped

    def enable(self):
        """
        Create the script if needed, upload the code, set it to run at device boot,
        and start it.
        """
        self.generation += 1

        with open(self.path, "r", encoding="utf-8") as script_file:
            code = script_file.read()

        if not code:
            self.logger.error(
                f"No script data to upload for {self.display_name} script!"
            )
            return

        # Only log at info when the script was missing, disabled, or stopped
        changed = True

        def upload(script, error=None):
            if error:
                self.logger.error(
                    f"Unable to create {self.display_name} script on {self.device_name}: {error['message']}"
                )
                return

            self.upload(script["id"], code, callback=configure)

        def configure(script):
            id = script["id"]
            self.logger.debug(
                f"Configuring {self.display_name} script on {self.device_name}..."
            )

            def start(response, error=None):
                if error:
                    self.logger.error(
                        f"Unable to set {self.display_name} script config on {self.device_name}: {error['message']}"
                    )
                    return

                self.script.start(id, callback=self._if_current_generation(complete))

            self.script.set_config(
                id,
                name=self.script_name,
                enable=True,
                callback=self._if_current_generation(start),
            )

        def complete(response, error=None):
            if error:
                self.logger.error(
                    f"Unable to start {self.display_name} script on {self.device_name}: {error['message']}"
                )
                return

            log = self.logger.info if changed else self.logger.debug
            log(
                f"{self.display_name} script is synced, running, and configured to run at device boot for {self.device_name}"
            )
            self.started()

        def found(script):
            nonlocal changed
            if script:
                self.logger.debug(
                    f"Found existing {self.display_name} script on {self.device_name}: {script}"
                )
                changed = not (script.get("enable") and script.get("running"))
                upload(script)
            else:
                self.logger.debug(
                    f"Creating {self.display_name} script on {self.device_name}..."
                )
                self.script.create(
                    self.script_name, self._if_current_generation(upload)
                )

        self.find(found)

    def disable(self):
        """
        Stop the script and prevent it from running at device boot. Nothing is sent
        if the script does not exist or is already stopped and disabled.
        """
        self.generation += 1

        def found(script):
            if not script or not (script.get("enable") or script.get("running")):
                return

            self.logger.debug(
                f"Disabling {self.display_name} script on {self.device_name}..."
            )
            id = script["id"]

            def disable(response, error=None):
                if error:
                    self.logger.error(
                        f"Unable to stop {self.display_name} script on {self.device_name}: {error['message']}"
                    )
                    return

                self.script.set_config(
                    id,
                    name=self.script_name,
                    enable=False,
                    callback=self._if_current_generation(complete),
                )

            self.script.stop(id, callback=self._if_current_generation(disable))

        def complete(response, error=None):
            if error:
                self.logger.error(
                    f"Unable to set {self.display_name} script config on {self.device_name}: {error['message']}"
                )
                return

            self.logger.info(
                f"{self.display_name} script is stopped and will not run at device boot for {self.device_name}"
            )

        self.find(found)

    def find(self, callback):
        """
        Look up this script on the device by name.

        :param callback: Called with the script's entry from Script.List, or None if
            the device has no script with this name. Not called if the list fails.
        """

        def inspect_scripts(list_response, error=None):
            if error:
                self.logger.error(
                    f"Unable to get current scripts for {self.device_name}: {error['message']}"
                )
                return

            for script in list_response.get("scripts", []):
                if script["name"] == self.script_name:
                    callback(script)
                    return

            callback(None)

        self.script.list(self._if_current_generation(inspect_scripts))

    def upload(self, id: int, code: str, callback):
        """
        Stop the script and upload the code in chunks, since Script.PutCode accepts
        at most 1024 bytes at a time.

        :param callback: Called with {"id": id} once every chunk is uploaded.
        """
        chunk_size = 1024
        chunks = [code[i : i + chunk_size] for i in range(0, len(code), chunk_size)]
        total_bytes = len(code)
        progress = {"uploaded_bytes": 0}

        def upload_chunks(response, error=None):
            if error:
                self.logger.error(
                    f"Unable to upload script data chunk: {error['message']}"
                )
                return

            if chunks:
                chunk = chunks.pop(0)
                append = progress["uploaded_bytes"] > 0
                self.script.put_code(
                    id,
                    code=chunk,
                    append=append,
                    callback=self._if_current_generation(upload_chunks),
                )

                progress["uploaded_bytes"] += len(chunk)
                progress_pct = progress["uploaded_bytes"] / total_bytes * 100
                self.logger.debug(
                    f"Syncing script:{id} on {self.device_name}... ({progress_pct:.0f}%)"
                )
            else:
                callback({"id": id})

        self.script.stop(id, callback=self._if_current_generation(upload_chunks))
