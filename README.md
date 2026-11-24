# ShellyNGMQTT

An [Indigo](https://www.indigodomo.com) plugin that integrates Shelly Gen2+ ("Next Generation") devices over MQTT, including Shelly BLU Bluetooth sensors relayed through a Shelly gateway.

Everything stays on your local network: devices push status changes to your MQTT broker the moment they happen, and Indigo controls them without any Shelly cloud account or polling.

Using Gen1 Shelly devices? Use the [ShellyMQTT](https://www.indigodomo.com/pluginstore/236/) plugin instead.

## Features

- Control and monitor Shelly Plus and Pro relays, plugs, dimmers, and covers
- Each device component (switch, input, light, cover, temperature, humidity) appears as its own Indigo device
- Shelly BLU sensors and buttons relayed over MQTT by a script the plugin installs and manages on your Shelly devices
- Triggers for button presses (single, double, triple, long, and hold) and device events like firmware updates and Wi-Fi disconnects
- Configure Wi-Fi, Ethernet, Bluetooth, and system settings, and update firmware, from Indigo

## Supported Devices

- **Gen2:** Plus 1, Plus 1 PM, Plus 2 PM, Plus WallDimmer, Plus I4, Plus H&T, Plus Plug (US/IT), Plus Plug S, Plus Plug UK, Pro 1, Pro 1 PM, Pro 2, Pro 2 PM, Pro 4 PM
- **BLU:** Button1, RC Button 4, Door/Window, Motion, H&T
- **BLU+ZB:** Distance, Door/Window ZB, H&T Display ZB, Motion ZB

See [Supported Devices](docs/supported-devices.md) for what each device provides in Indigo and which can act as BLU gateways. Don't see your device? Open a [new device request](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=new-device.yml).

## Requirements

- Indigo 2023.2 or later
- [MQTT Connector](https://www.indigodomo.com/pluginstore/211/) plugin with a broker device set up
- An MQTT broker, such as the [MQTT Broker](https://www.indigodomo.com/pluginstore/260/) plugin, which runs one inside Indigo, or a standalone broker like [Mosquitto](https://mosquitto.org)
- Shelly devices with MQTT enabled and connected to the same broker
- For BLU devices: a supported Shelly Gen2+ device nearby to act as a Bluetooth gateway

## Quick Start

1. Install [MQTT Connector](https://www.indigodomo.com/pluginstore/211/), create a broker device for your MQTT broker subscribed to `shellies-ng/#`, and create a trigger that queues `shellies-ng` topics with the message type `shellies-ng`.
2. Install ShellyNGMQTT from the [Indigo Plugin Store](https://www.indigodomo.com/pluginstore/290/) or the [latest release](https://github.com/AaronLionsheep/ShellyNGMQTT/releases/latest).
3. In the Shelly web UI, go to **Settings → MQTT**, turn on **Enable**, enter your broker's address, and turn on **Enable RPC over MQTT** (required). Turning on **MQTT Control** is recommended, since future features like auto-discovery may use it. Add `shellies-ng/` to the start of the topic prefix.
4. In Indigo, create a new ShellyNGMQTT device, choose the model, select the broker, enter the full topic prefix as the Base MQTT Topic, and enter `shellies-ng` as the message type.

See the [User Guide](docs/user-guide.md) for detailed setup, BLU devices, and troubleshooting.

## Documentation

- [User Guide](docs/user-guide.md): installation, setup, devices, triggers, actions, and troubleshooting
- [Supported Devices](docs/supported-devices.md): what each Shelly model provides in Indigo
- [BLU Relay](docs/blu-relay.md): how BLU devices reach Indigo, and security considerations
- [Trigger Events](docs/events.md): button presses and device events you can trigger on
- [Actions](docs/actions.md): controlling devices and updating firmware
- [Reporting Bugs](docs/reporting-bugs.md): what to include when something isn't working
- [Contributing](docs/CONTRIBUTING.md): dev environment, tests, and pull request guidelines

## Support

- Questions and setup help: [Indigo forum](https://forums.indigodomo.com/viewforum.php?f=330)
- Bugs: [GitHub issues](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new/choose)

## License

See [LICENSE](LICENSE).
