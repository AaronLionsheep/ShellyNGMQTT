# :zap: Trigger Events

Besides Indigo's built-in triggers on device states (like a switch turning on), ShellyNGMQTT provides events for things that don't change a state, like a button being double-pressed or a firmware update finishing.

To use one, create a new trigger in Indigo, set **Type** to **ShellyNGMQTT Event**, choose the event, and select the device it should watch.

## Button Events

Button events fire when a button or input is pressed. Each one asks for a **Device** and a **Button**. Most devices have a single button; the Shelly BLU RC Button 4 and RC Button 4 ZB have buttons 1-4.

| Event | Fires when | Input components | BLU devices |
| --- | --- | :---: | --- |
| Button Down | A button is pressed down | :white_check_mark: | :heavy_minus_sign: |
| Button Up | A button is released | :white_check_mark: | :heavy_minus_sign: |
| Single Push | A button is pressed once | :white_check_mark: | All |
| Double Push | A button is pressed twice quickly | :white_check_mark: | Button1, RC Button 4, RC Button 4 ZB |
| Triple Push | A button is pressed three times quickly | :white_check_mark: | Button1, RC Button 4, RC Button 4 ZB |
| Long Push | A button is held, then released | :white_check_mark: | Button1, RC Button 4, RC Button 4 ZB |
| Hold Push | A button has been held long enough, while it's still held | :heavy_minus_sign: | Button1, RC Button 4, RC Button 4 ZB, Door/Window, Motion, H&T |
| Long Double Push | A button is pressed once, then pressed and held | :heavy_minus_sign: | RC Button 4 ZB |
| Long Triple Push | A button is pressed twice, then pressed and held | :heavy_minus_sign: | RC Button 4 ZB |

:white_check_mark: means supported, and :heavy_minus_sign: means the device doesn't send that event.

**Long Push vs. Hold Push:** Long Push fires *after* the button is released, if it was held long enough. Hold Push fires *while* the button is still held, as soon as it's been held long enough. Use Hold Push when the action should happen without waiting for the release.

Because Hold Push fires while the button is held, one press can fire two events: Hold Push while the button is held, then Long Push, Long Double Push, or Long Triple Push when it's released. If a button has triggers for both Hold Push and one of the Long events, both run on the same press, so use only one of them for each button.

### Input Components

Input components on MQTT devices (for example, the Shelly Plus I4 or the switch input on a Shelly Plus 1) fire button events only when the input is set to **Button** mode on the Shelly. In **Switch** mode, use a trigger on the Input device's on/off state instead.

Button Down and Button Up fire on every press and release, so a double press fires both of them twice, as well as Double Push.

### BLU Devices

- **Hold Push** requires BLU device firmware 1.0.22 or newer.
- **Delayed presses don't fire triggers.** A button press that reaches the plugin more than 3 seconds after it happened updates the device's states, but doesn't fire triggers, so an action never runs unexpectedly late. Ignored presses are logged as warnings. The limit is set by **Max BLE Event Age** in the plugin preferences.
- **Each press fires once,** even when several gateways relay it. See [BLU Relay](blu-relay.md#multiple-gateways).
- **Don't use unencrypted BLU devices for security-sensitive actions,** like unlocking doors, opening garage doors, or disarming an alarm. Someone nearby can fake or replay their button presses. See [Security Considerations](blu-relay.md#security-considerations).

## Device Events

Device events report what's happening to an MQTT device itself. Each one asks for the **Device** to watch: choose the main Shelly device, not one of its components.

| Event | Fires when |
| --- | --- |
| OTA Begin | A firmware update starts |
| OTA Success | A firmware update finishes successfully |
| OTA Error | A firmware update fails |
| WiFi Connection Failure | The device fails to connect to its Wi-Fi network |
| WiFi Disconnected | The device loses its Wi-Fi connection |
| Sleep | A battery-powered device, like the Shelly Plus H&T, goes to sleep |
| Scheduled Restart | The device restarts on a schedule set on the Shelly |

BLU devices don't report device events.

## Examples

- **Double-press for a scene:** a Double Push trigger on a Shelly Plus I4 input that runs an "All Off" action group.
- **One button, two actions:** on a BLU Button1, a Single Push trigger that toggles a lamp, and a Hold Push trigger that turns off every light in the room.
- **Firmware update alerts:** an OTA Error trigger on each device that sends you a notification.
