# Actions

ShellyNGMQTT devices work with Indigo's standard device actions, so you control them the same way as any other relay or dimmer: from the device list, control pages, action groups, schedules, and triggers. The plugin also adds actions for managing firmware.

## Device Actions

These are Indigo's built-in actions, found under **Device Actions** when you add an action. Which ones apply depends on the component.

| Component | Turn On | Turn Off | Toggle | Set Brightness | Brighten By / Dim By |
| --- | :---: | :---: | :---: | :---: | :---: |
| Switch | ✓ | ✓ | ✓ | | |
| Light | ✓ | ✓ | ✓ | ✓ | |
| Cover | Open | Close | ✓ | Set position | Move by |

### Covers

Covers use Indigo's dimmer actions, with brightness standing in for position: 0% is fully closed and 100% is fully open.

- **Turn On** opens the cover fully, and **Turn Off** closes it fully.
- **Toggle** opens a fully closed cover. If the cover is open at all, it closes it.
- **Set Brightness** moves the cover to a position, for example 50% for half open.
- **Brighten By** and **Dim By** open or close the cover by that many percent from its current position.

The cover must be calibrated on the Shelly for positions to work.

### Request Status

**Request Status** asks the device for its current state and updates Indigo. Devices normally push changes as they happen, so this is rarely needed. BLU devices don't support it, since they only broadcast and can't be asked for anything.

## Plugin Actions

These actions are found under **ShellyNGMQTT Actions** when you add an action. They work with MQTT devices only, not BLU devices. Choose the main Shelly device, not one of its components.

| Action | What it does |
| --- | --- |
| Check for Device Updates | Asks the device whether newer firmware is available, and logs the newest stable and beta versions it finds, or that it's up to date |
| Update Device | Tells the device to install the newest firmware from the chosen stage: **Stable** or **Beta** |

Both are also available from the **Plugins → ShellyNGMQTT** menu, for running them once without creating an action.

### Updating Firmware

- **The device downloads the update itself** from Shelly's servers, so it needs internet access.
- **The device restarts** to install the update, and can't be controlled until it reconnects. What its outputs do after the restart depends on each output's power-on setting on the Shelly.
- **Beta firmware may be unstable.** Stick with Stable unless you need a fix that's only in Beta.
- **Track progress with triggers.** The [OTA Begin, OTA Success, and OTA Error](events.md#device-events) events fire as the update runs, so you can be notified when an update finishes or fails.

For example, a weekly schedule could run Check for Device Updates on each device, so new versions show up in the log.

## Not Supported

- **Brighten By and Dim By on lights.** These actions currently do nothing on Light components. Use Set Brightness instead. <!-- TODO: confirm, Light.handle_action has no BrightenBy/DimBy -->
- **Resetting energy totals.** Indigo's energy reset action doesn't reset the energy counter on the Shelly. <!-- TODO: confirm, no EnergyReset handling found -->
- **Updating BLU firmware.** BLU devices are updated with the Shelly app.
