import time

import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from ..devices.shelly_blu import BLERelayPacket, ShellyBLU
from .managed_script import ManagedScript

# Relayed BLE packets older than this (in seconds) are discarded, since their sensor
# values are stale (ex: queued while the plugin was not running).
MAX_BLE_PACKET_AGE = 60.0


class BluRelayScript(ManagedScript):
    """
    The script that relays BTHome advertisements heard by a device over MQTT, so they
    can be dispatched to Shelly BLU devices.
    """

    display_name = "BLU Relay"
    script_name = "indigo-blu-relay.js"
    file_name = "indigo-blu-relay.js"

    @property
    def enabled(self):
        """
        Whether BLU Relay is turned on in the device's config.
        """
        return self.script.shelly.device.pluginProps.get("blu-relay", False)

    def handle_notify_event(self, event):
        if event.get("name") != "shelly-blu":
            return

        shelly = self.script.shelly
        event_data = event.get("data", {})

        # The script may still be running if the disable RPCs were missed
        if not self.enabled:
            self.logger.debug(
                f"Ignoring BLE activity from {shelly.device.name}, BLU Relay is disabled: {event_data}"
            )
            return

        self.logger.debug(
            f"BLE activity relayed via {shelly.device.name}: {event_data}"
        )

        # Parse the event data
        packet = BLERelayPacket.from_mqtt_event(
            relay_device_id=shelly.device_id,
            timestamp=event["ts"],
            event_data=event_data,
        )

        # This is purposefully not using .get() so it creates the entry in the defaultdict for address discovery
        target_device_ids = tuple(
            indigo.activePlugin.blu_address_devices[packet.address]
        )

        # Nothing to dispatch to, the address has only been recorded for discovery
        if not target_device_ids:
            return

        # Only process the packet if we trust the relay device's clock
        if not shelly.clock_trusted():
            self.logger.warning(
                f"{shelly.device.name} has no recent NTP sync, ignoring its BLE packets. "
                "Check that it can reach its SNTP server."
            )
            return

        # Discard old packets by comparing the relay's timestamp to the system time
        packet_age = time.time() - packet.timestamp
        max_packet_age = float(
            indigo.activePlugin.pluginPrefs.get(
                "ble-max-packet-age", MAX_BLE_PACKET_AGE
            )
        )
        if packet_age > max_packet_age:
            self.logger.debug(
                f"Discarding BLE packet for {packet.address} relayed via "
                f"{shelly.device.name}, {packet_age:.1f}s old: {event_data}"
            )
            return

        # Submit the packet to each target device for processing
        for device_id in target_device_ids:
            shelly_blu = indigo.activePlugin.shellies.get(device_id)
            if not shelly_blu or not isinstance(shelly_blu, ShellyBLU):
                continue

            shelly_blu.handle_ble_relay_packet(packet)
