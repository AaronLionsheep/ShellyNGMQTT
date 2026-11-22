# Reporting Bugs

Found something that isn't working? Thanks for taking the time to report it. This page explains where to report, what helps get a bug fixed quickly, and how to collect it. Don't worry about getting everything perfect: a report with partial information is far better than no report at all.

## Before You Report

- **Update.** Make sure you're on the latest plugin release, and ideally the latest Shelly firmware. The bug may already be fixed.
- **Check the docs.** The [Troubleshooting](user-guide.md#troubleshooting) section covers common setup problems, like devices that never update.
- **Search.** Look through [existing issues](https://github.com/AaronLionsheep/ShellyNGMQTT/issues?q=is%3Aissue) and the [Indigo forum](https://forums.indigodomo.com/viewforum.php?f=330). If you find your bug, add a comment with your details rather than opening a new issue.

## Where to Report

- **Bugs:** open a [bug report](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=bug-report.yml) on GitHub. The form asks for everything listed below.
- **Questions and setup help:** post on the [Indigo forum](https://forums.indigodomo.com/viewforum.php?f=330). If you're not sure whether something is a bug or a setup problem, start there.
- **Unsupported devices:** open a [new device request](#requesting-a-new-device) instead of a bug report.

## What to Include

The bug report form asks for each of these. Fill in what you can.

- **What happened, and what you expected.** "The switch turned on in Indigo, but the relay stayed off" is much more useful than "the switch doesn't work".
- **Steps to reproduce,** if you know them. A bug that can be reproduced can almost always be fixed.
- **Versions:** plugin, Indigo, macOS, and whether your Mac is Apple Silicon or Intel. Some dependencies behave differently on Intel Macs.
- **MQTT setup:** your MQTT Connector version, and which broker you use and where it runs.
- **Device:** the Shelly model and firmware version, if the bug involves a specific device.
- **Logs** covering the moment the bug happened. See [Collecting Logs](#collecting-logs).
- **MQTT messages** from the device, if the problem looks like a device reporting the wrong thing. See [Capturing MQTT Traffic](#capturing-mqtt-traffic).

## Collecting Logs

1. In Indigo, open **Plugins → ShellyNGMQTT → Configure...** and set the log level to **Debug**. For BLU devices, also turn on **Debug BLE Activity**.
2. Reproduce the bug.
3. Copy the related lines from the Indigo Event Log window, starting a little before the bug happened.
4. Set the log level back to its previous value. Debug logging is very chatty.

If the bug already happened and you didn't catch it live, Indigo saves the log to a file per day:

```
/Library/Application Support/Perceptive Automation/Indigo <version>/Logs/<YYYY-MM-DD> Events.txt
```

Paste logs as text, not screenshots, so they can be searched.

## Capturing MQTT Traffic

Seeing exactly what a device sends to the broker helps tell a device problem from a plugin problem. Each Shelly device publishes under the **Base MQTT Topic** set on its Indigo device, which is the topic prefix configured on the Shelly itself.

With the [Mosquitto](https://mosquitto.org) command line tools installed, run this and reproduce the bug:

```sh
mosquitto_sub -h <broker-ip> -v -t '<base-topic>/#'
```

Add `-u <username> -P <password>` if your broker requires a login. A graphical client like [MQTT Explorer](https://mqtt-explorer.com) works too.

## Removing Sensitive Information

Issues and forum posts are public. Before posting logs, device data, or screenshots, remove or replace:

- Wi-Fi passwords
- MQTT broker usernames and passwords
- BLU bind keys (encryption keys)
- Public IP addresses and hostnames

Local addresses like `192.168.x.x` and device MAC addresses are fine to leave in.

## Requesting a New Device

If your Shelly device isn't supported yet, open a [new device request](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=new-device.yml). The form walks you through collecting the data needed to add support.
