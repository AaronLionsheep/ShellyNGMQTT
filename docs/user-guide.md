# :book: User Guide

ShellyNGMQTT connects Shelly Gen2+ devices to Indigo over MQTT, along with Shelly BLU Bluetooth devices relayed through them. Gen1 devices are supported by the [ShellyMQTT](https://www.indigodomo.com/pluginstore/236/) plugin instead.

## Installation

### Requirements

- Indigo 2023.2 or later, on an Apple Silicon or Intel Mac
- The [MQTT Connector](https://www.indigodomo.com/pluginstore/211/) plugin
- An MQTT broker, reachable from both Indigo and your Shelly devices. If you don't already run one, the [MQTT Broker](https://www.indigodomo.com/pluginstore/260/) plugin runs a broker inside Indigo, with nothing else to install. A standalone broker like [Mosquitto](https://mosquitto.org) works too.

### Installing

1. Download the plugin from its [Indigo Plugin Store page](https://www.indigodomo.com/pluginstore/290/), or download `ShellyNGMQTT.indigoPlugin.zip` from the [latest release](https://github.com/AaronLionsheep/ShellyNGMQTT/releases/latest) on GitHub and unzip it.
2. Double-click `ShellyNGMQTT.indigoPlugin`. Indigo installs and enables it.
3. On first launch, Indigo downloads the Python packages the plugin needs, so the Indigo server needs internet access. This can take a minute.

Then continue with [Setup](#setup).

### Upgrading

Install the new version the same way, by double-clicking it. Indigo replaces the old version and keeps your devices, triggers, and settings. Check the [release notes](https://github.com/AaronLionsheep/ShellyNGMQTT/releases) for changes that need action on your part.

If you use BLU devices, the plugin updates the relay script on each gateway automatically after an upgrade. See [Keeping the Script Up to Date](blu-relay.md#keeping-the-script-up-to-date).

## Setup

Messages flow from each Shelly device to your MQTT broker, then through MQTT Connector to ShellyNGMQTT:

```
Shelly device → MQTT broker → MQTT Connector → ShellyNGMQTT → Indigo devices
```

Set up each piece in order. You only need to do the MQTT Connector steps once; the Shelly steps are repeated for each device.

### MQTT Connector

ShellyNGMQTT doesn't connect to the broker itself. It relies on [MQTT Connector](https://www.indigodomo.com/pluginstore/211/) for the connection.

This guide puts every Shelly under a `shellies-ng/` topic prefix and uses `shellies-ng` as the message type. Both differ from what the [ShellyMQTT](https://www.indigodomo.com/pluginstore/236/) plugin for Gen1 devices uses (`shellies/`), so the two plugins can run side by side without receiving each other's messages.

1. **Create a broker device.** Install MQTT Connector, then create an MQTT Connector device with your broker's connection settings. If you already have one, for example for ShellyMQTT, you can reuse it.
2. **Subscribe to the Shelly topics.** On the broker device, add a subscription to `shellies-ng/#`.
3. **Create a trigger that passes Shelly messages to the plugin.** MQTT Connector only hands messages to other plugins when a trigger queues them. One trigger covers all your Shellies:
   1. Create a new Indigo trigger with the type **MQTT Connector Event** and the event **Topic Component Match**.
   2. Select your broker device.
   3. Add the first match part: choose **Match**, enter `shellies-ng` as the **Match String**, and click **Add Match**.
   4. Add the second match part: choose **Any (wildcard)** and click **Add Match**.
   5. Check **Queue Message**, and set the **Message Type** to `shellies-ng`.
   6. Optionally, check **Hide trigger executions in Event Log**. The trigger runs for every message, and a single device update can produce several messages.

If you change the message type, use the same value in every ShellyNGMQTT device's **Message Type** field.

### Shelly Device

In the Shelly's web UI (open its IP address in a browser), go to **Settings → MQTT** and:

1. Turn on **Enable**.
2. Enter your broker's address as the **Server**, plus a username and password if your broker requires them.
3. Add `shellies-ng/` to the start of the **topic prefix**. For example, a default prefix of `shellyplugusg4-acebe6f78ecc` becomes `shellies-ng/shellyplugusg4-acebe6f78ecc`. This full prefix is the device's address in Indigo, so note it down.
4. Turn on **Enable RPC over MQTT**. This is required: the plugin controls the device and receives its updates through it.
5. Turn on **MQTT Control**. It isn't required today, but future features like automatic device discovery may use it.
6. Save. The device may restart to apply the settings.

BLU devices don't connect to MQTT themselves; they reach Indigo through a gateway. See [BLU Relay](blu-relay.md) for setup.

### Plugin Configuration

Open **Plugins → ShellyNGMQTT → Configure...** to change these settings. The defaults work for most setups.

| Setting | Default | What it does |
| --- | --- | --- |
| Log level | Info | How much the plugin logs. **Debug** logs every MQTT message, which helps with troubleshooting but is very chatty. **Warning** logs only problems. |
| Log Device Activity | On | Logs device activity such as turning a device on or off or changing brightness. Turn it off to keep the log quieter. |
| Debug BLE Activity | Off | Logs every broadcast received from a BLU device, including its sensor values and events, at the Info level. Useful for setting up or troubleshooting BLU devices. |
| Max BLE Packet Age (s) | 60 | BLU broadcasts older than this when they reach the plugin are discarded, since their values are stale (for example, broadcasts queued while the plugin was stopped). Increase it to process longer backlogs. |
| Max BLE Event Age (s) | 3 | BLU button presses older than this update states but don't fire triggers, so a delayed press can't run an action late. Ignored presses are logged as warnings. Increase it if presses are being ignored because of relay delays. |

Leave the two age settings blank to use the defaults. See [BLU Relay](blu-relay.md#what-it-does-and-doesnt-do) for more on how they're used.

## Creating Devices

1. In Indigo, create a new device, choose **ShellyNGMQTT** as the type, and choose **Create/Modify Shelly Device...** as the model.
2. Choose the **Shelly Model**.
3. Fill in the connection settings:
   - **MQTT devices:** choose the **MQTT Broker** device, enter the Shelly's full topic prefix as the **Base MQTT Topic** (for example `shellies-ng/shellyplugusg4-acebe6f78ecc`), and enter the **Message Type** from your MQTT Connector trigger (`shellies-ng`).
   - **BLU devices:** choose the device from **Discovered MAC Addresses**, or type its **MAC Address**. Discovered addresses come from your BLU gateways; click **Refresh** if the device isn't listed yet, and press its button to make it broadcast. See [BLU Relay](blu-relay.md#setting-up-a-gateway).
4. Enter an **Initial Name**, like `Kitchen Light`. The plugin names the main device with it, and names each component device after it, like `Kitchen Light Switch` and `Kitchen Light Input`.
5. **Shelly Plus 2 PM only:** choose the **Device Profile**, **Switch** or **Cover (Roller/Shutter)**, matching the profile set on the Shelly.
6. Click **Submit**.

Some models are added from Shelly's API documentation before anyone has tried them on a real device. For these, the dialog shows an orange warning when you choose the model, and the plugin logs a warning each time the device starts. They usually work, but if one doesn't, please [report it](reporting-bugs.md). Models that someone has confirmed work show a green note saying they've been verified by the community instead.

Verifications are included in the plugin when it's released, so the warning reflects the version you have installed. Someone may have verified the model since, which will be noted in a future version of the plugin. Updating the plugin picks up any new verifications.

If it does work, please send a device verification report, which removes the warning in the next release. Choose **Plugins → ShellyNGMQTT → Report Device Verification...**, pick the device, and click **Get Link**. The plugin logs a link to a [device verification](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=device-verification.yml) form on GitHub with the model, firmware, and plugin version filled in. Check **Open in browser** to also open it, but note that the browser opens on the Indigo server Mac, so from a remote client copy the link from the event log instead. You can report devices that are already verified too.

A verification is a community note of support that the model worked for you, not a warranty. You aren't responsible or liable for how the device or the plugin works for anyone else. You can choose to be credited by your GitHub and Indigo forum usernames, or verify anonymously.

The plugin creates the main Shelly device and one Indigo device per component, grouped together. The main device holds device-level information like Wi-Fi signal strength and firmware versions; the component devices are what you control and trigger on. See [Supported Devices](supported-devices.md) for what each model creates.

To change the connection settings later, edit any device in the group and click **Edit Device Settings...**. Renaming the main device doesn't rename its components.

## Triggers

See [Trigger Events](events.md) for button and device events, and which devices support each one.

## Actions

See [Actions](actions.md) for device actions, cover positions, and firmware updates.

## Device States

States can be used in trigger conditions, control pages, and scripts. The **State ID** is the name to use in scripts and in Indigo's state pickers. States only have a value once the device has reported them.

### Main Shelly Device

Every MQTT device's main device has these states:

| State | State ID | Description |
| --- | --- | --- |
| Online | `online` | Whether the Shelly reports itself as connected to the broker |
| IP Address | `ip-address` | The Shelly's IP address |
| Connected SSID | `ssid` | The Wi-Fi network the Shelly is connected to |
| Wi-Fi Signal Strength | `rssi` | Wi-Fi signal strength in dBm. Closer to 0 is stronger; below about -80 is weak |
| MAC Address | `mac-address` | The Shelly's MAC address |
| Uptime | `uptime` | Seconds since the Shelly last restarted |
| Current Firmware Version | `current-firmware` | The installed firmware |
| Available Firmware Version | `available-firmware` | The newest stable firmware, when it's newer than the installed version |
| Available Beta Firmware Version | `available-beta-firmware` | The newest beta firmware, when it's newer than the installed version |

The battery-powered **Shelly Plus H&T** also has:

| State | State ID | Description |
| --- | --- | --- |
| Battery Level | `batteryLevel` | Battery charge in percent |
| Battery Voltage | `battery-voltage` | Battery voltage |
| External Power | `external-power` | Whether the device is powered over USB instead of its batteries |

### Components

| State | State ID | Components | Description |
| --- | --- | --- | --- |
| On/Off | `onOffState` | Switch, Light, Cover, Input | On or off. For covers, on means open at all; for inputs, pressed or closed |
| Brightness | `brightnessLevel` | Light, Cover | Brightness in percent. For covers, the position: 0 is closed, 100 is open |
| Cover State | `cover_state` | Cover | What the cover is doing, such as opening, closing, or stopped |
| Sensor Value | `sensorValue` | Temperature, Humidity | The reading shown in Indigo's device list |
| Temperature (°C / °F) | `temperature_c`, `temperature_f` | Switch, Light, Cover, Temperature | For Temperature components, the reading; for others, the Shelly's internal temperature |
| Power | `curEnergyLevel` | Switch, Light, Cover with power metering | Current power draw in watts |
| Energy | `accumEnergyTotal` | Switch, Light, Cover with power metering | Total energy used. Shown in kWh, but the state's value is in Wh, so divide by 1000 in scripts and conditions |
| Voltage | `voltage` | Switch, Light, Cover with power metering | Supply voltage |
| Current | `current` | Switch, Light with power metering | Current draw in amps |
| Power Factor | `power_factor` | Switch, Light with power metering | Power factor of the load |

See [Supported Devices](supported-devices.md#gen2) for which models have power metering.

### BLU Devices

Every BLU device has:

| State | State ID | Description |
| --- | --- | --- |
| Battery Level | `batteryLevel` | Battery charge in percent |
| Signal Strength | `rssi` | Signal strength in dBm, as heard by the gateway that relayed the latest broadcast |
| MAC Address | `address` | The device's MAC address |
| Last Packet ID | `pid` | A counter the device increases with each broadcast |

Model-specific states:

| Model | States (State ID) |
| --- | --- |
| Shelly BLU Door/Window | Open/closed (`onOffState`), illuminance (`illuminance`), rotation (`rotation`) |
| Shelly BLU Motion | Motion detected (`onOffState`), illuminance (`illuminance`) |
| Shelly BLU H&T | Temperature (`temperature`, also `sensorValue`), humidity (`humidity`) |
| Shelly BLU H&T Display ZB | Temperature (`temperature`, also `sensorValue`), humidity (`humidity`), light detected (`light`), light level: `dark`, `twilight`, or `bright` (`lightLevel`) |
| Shelly BLU Distance | Distance in mm (`distance`), vibration (`vibration`), distance or container level (`sensorValue`) |
| Shelly BLU Motion ZB | Motion detected (`onOffState`), light level: `dark`, `twilight`, or `bright` (`lightLevel`) |
| Shelly BLU Door/Window ZB | Open/closed (`onOffState`), light level: `dark`, `twilight`, or `bright` (`lightLevel`), rotation (`rotation`) |
| Shelly BLU H&T ZB | Temperature (`temperature`, also `sensorValue`), humidity (`humidity`) |

## Troubleshooting

Start by setting the log level to **Debug** in **Plugins → ShellyNGMQTT → Configure...**, then reproduce the problem and watch the Indigo Event Log. Set it back to **Info** when you're done, since Debug logs every MQTT message.

### Device doesn't update or respond

Work through the path a message takes, from the Shelly to Indigo:

1. **Is the Shelly connected to the broker?** The main Shelly device's **Online** state shows whether the Shelly reports itself as connected. If it's false or never changes, check the Shelly's power and Wi-Fi, and its **Settings → MQTT** server address and login.
2. **Is RPC over MQTT on?** Without **Enable RPC over MQTT** on the Shelly, the device can connect but won't send updates or accept commands.
3. **Are messages reaching the plugin?** With Debug logging on, every message the plugin receives is logged as `Processing: "<payload>" on topic "<topic>"`. Toggle the device by hand and look for these lines.
   - **No lines:** messages aren't getting through MQTT Connector. Check that MQTT Connector is enabled, the broker device is connected and subscribed to `shellies-ng/#`, and the trigger matches `shellies-ng`, has **Queue Message** checked, and uses the message type `shellies-ng`.
   - **Lines, but the device doesn't update:** the topic in the log doesn't match the device. Check that the device's **Base MQTT Topic** is exactly the Shelly's topic prefix (topics are case-sensitive) and its **Message Type** matches the trigger's.
4. **Is the Shelly publishing at all?** To check outside Indigo, watch the broker directly. See [Capturing MQTT Traffic](reporting-bugs.md#capturing-mqtt-traffic).

### Log messages

| Message | What to do |
| --- | --- |
| `MQTT Connector plugin is required!!` | Install [MQTT Connector](https://www.indigodomo.com/pluginstore/211/), then restart ShellyNGMQTT. |
| `MQTT Connector plugin not enabled, aborting.` | Enable MQTT Connector. The plugin checks again every minute. |
| `'<device>' is not properly setup! Address is unknown.` or `Check the broker and topic root.` | Edit the device and fill in the **MQTT Broker** and **Base MQTT Topic**. |
| `Error writing ... configuration: <message>` | The Shelly rejected a settings change. The message after the colon comes from the Shelly and explains why. |
| `'<device>' (<model>) wasn't tested against a real device when this plugin version was released ...` | Nobody had confirmed this model works with the plugin when your version was released. Someone may have since, which a newer version will include. If it works for you, send a device verification report with **Plugins → ShellyNGMQTT → Report Device Verification...** (see [Creating Devices](#creating-devices)). |
| `No trigger type found for button event: <event>` | A BLU device sent a kind of button press the plugin doesn't recognize. Please [report it](reporting-bugs.md), including the log lines. |
| Messages mentioning the BLU Relay, Bluetooth scanning, or NTP sync | See [BLU Relay troubleshooting](blu-relay.md#troubleshooting). |

### Button triggers don't fire

- **Inputs:** the input must be set to **Button** mode on the Shelly for push events. In Switch mode, trigger on the Input device's on/off state instead.
- **Check the device in the trigger.** Button events on MQTT devices are tied to the Input component device, not the main Shelly device.
- **BLU devices:** presses that arrive more than 3 seconds late are ignored and logged as warnings. See [Trigger Events](events.md#blu-devices).

### Shelly Plus H&T updates rarely

The Plus H&T is battery powered and sleeps between readings, so it only reports when it wakes up: on a schedule, or when temperature or humidity changes enough. Its **Online** state is false while it sleeps. This is normal.

### BLU devices

See [BLU Relay troubleshooting](blu-relay.md#troubleshooting) for BLU devices that aren't discovered, don't update, or whose presses are ignored.

### Still stuck?

Ask on the [Indigo forum](https://forums.indigodomo.com/viewforum.php?f=330), or see [Reporting Bugs](reporting-bugs.md) for what to include in a bug report.
