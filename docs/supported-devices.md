# Supported Devices

ShellyNGMQTT supports Shelly Gen2+ Wi-Fi devices over MQTT, and Shelly BLU Bluetooth devices relayed through them. Gen1 devices are supported by the [ShellyMQTT](https://www.indigodomo.com/pluginstore/236/) plugin instead.

Don't see your device? Open a [new device request](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=new-device.yml).

In the tables on this page, :white_check_mark: means the device has the feature and the plugin supports it, and :heavy_minus_sign: means the device itself doesn't have it. **Added in** is the first plugin version that supports the model.

## How Devices Appear in Indigo

When you create a Wi-Fi Shelly device, the plugin creates one Indigo device for each part of it, called a component. For example, a Shelly Plus 1 becomes two Indigo devices: a **Switch** for the relay and an **Input** for the switch terminal. The devices are grouped together in Indigo, and editing any one of them opens the settings for the whole Shelly.

Each BLU device is a single Indigo device.

## MQTT Devices

In the tables below:

- **Power metering:** the device reports power, energy, voltage, and current to Indigo.
- **BLU gateway:** the device can relay Shelly BLU devices to Indigo. See [BLU Gateways](#blu-gateways).

### Gen2

| Model | Added in | Indigo devices created | Power metering | BLU gateway |
| --- | :---: | --- | :---: | :---: |
| [Shelly Plus 1](https://kb.shelly.cloud/knowledge-base/shelly-plus-1) ([Mini](https://kb.shelly.cloud/knowledge-base/shelly-plus-1-mini)) | 0.1.0 | 1 Switch, 1 Input | :heavy_minus_sign: | :white_check_mark: |
| [Shelly Plus 1 PM](https://kb.shelly.cloud/knowledge-base/shelly-plus-1pm) | 0.3.0 | 1 Switch, 1 Input | :white_check_mark: | :white_check_mark: |
| [Shelly Plus 2 PM](https://kb.shelly.cloud/knowledge-base/shelly-plus-2pm) | 0.1.0 | 2 Switches and 2 Inputs, or 1 Cover and 2 Inputs | :white_check_mark: | :white_check_mark: |
| [Shelly Plus WallDimmer](https://kb.shelly.cloud/knowledge-base/shelly-plus-wall-dimmer) | 1.2.0 | 1 Light | :white_check_mark: | :white_check_mark: |
| [Shelly Plus I4](https://kb.shelly.cloud/knowledge-base/shelly-plus-i4) ([I4DC](https://kb.shelly.cloud/knowledge-base/shelly-plus-i4dc)) | 0.1.0 | 4 Inputs | :heavy_minus_sign: | :white_check_mark: |
| [Shelly Plus H&T](https://kb.shelly.cloud/knowledge-base/shelly-plus-h-t) | 0.4.0 | 1 Temperature, 1 Humidity | :heavy_minus_sign: | :heavy_minus_sign: |
| Shelly Plus Plug ([US](https://kb.shelly.cloud/knowledge-base/shelly-plus-plug-us)/[IT](https://kb.shelly.cloud/knowledge-base/shelly-plus-plug-it)) | 0.4.0 | 1 Switch | :white_check_mark: | :white_check_mark: |
| [Shelly Plus Plug S](https://kb.shelly.cloud/knowledge-base/shelly-plus-plug-s) | 1.1.0 | 1 Switch | :white_check_mark: | :white_check_mark: |
| [Shelly Plus Plug UK](https://kb.shelly.cloud/knowledge-base/shelly-plus-plug-uk) | 1.1.0 | 1 Switch | :white_check_mark: | :white_check_mark: |
| [Shelly Pro 1](https://kb.shelly.cloud/knowledge-base/shelly-pro-1) | 0.3.0 | 1 Switch, 2 Inputs | :heavy_minus_sign: | :white_check_mark: |
| [Shelly Pro 1 PM](https://kb.shelly.cloud/knowledge-base/shelly-pro-1pm) | 0.3.0 | 1 Switch, 2 Inputs | :white_check_mark: | :white_check_mark: |
| [Shelly Pro 2](https://kb.shelly.cloud/knowledge-base/shelly-pro-2) | 0.3.0 | 2 Switches, 2 Inputs | :heavy_minus_sign: | :white_check_mark: |
| [Shelly Pro 2 PM](https://kb.shelly.cloud/knowledge-base/shelly-pro-2pm) | 0.3.0 | 2 Switches, 2 Inputs | :white_check_mark: | :white_check_mark: |
| [Shelly Pro 4 PM](https://kb.shelly.cloud/knowledge-base/shelly-pro-4pm) | 1.1.0 | 4 Switches, 4 Inputs | :white_check_mark: | :white_check_mark: |

- **Shelly Plus 2 PM:** choose the **Switch** or **Cover (Roller/Shutter)** profile in the device settings, matching the profile set on the Shelly. Use Cover for roller shutters, blinds, and garage doors. The Cover profile requires plugin version 1.4.0 or later.
- **Shelly Plus H&T:** battery powered. It sleeps between readings, so it only reports when it wakes up, and it can't act as a BLU gateway.

### Gen3

No Gen3 devices are supported yet.

### Gen4

No Gen4 devices are supported yet.

### Components

Each component type is a standard Indigo device type, so it works with Indigo's built-in actions, control pages, and triggers.

| Component | Indigo device type | Main state | Other states |
| --- | --- | --- | --- |
| Switch | Relay | On/off | Device temperature (°C and °F); with power metering: power, energy, voltage, current, power factor |
| Light | Dimmer | On/off and brightness | Device temperature (°C and °F); with power metering: power, energy, voltage, current, power factor |
| Cover | Dimmer | Position (0-100%, 0 is closed) | Cover state (opening, closing, stopped, ...), device temperature (°C and °F); with power metering: power, energy, voltage |
| Input | Sensor | On/off (pressed or switch closed) | :heavy_minus_sign: |
| Temperature | Sensor | Temperature | Temperature in °C and °F |
| Humidity | Sensor | Humidity (%) | :heavy_minus_sign: |

Inputs set up as buttons on the Shelly can also fire [button events](events.md#button-events) for button down/up and single, double, triple, and long presses.

## BLU Gateways

Shelly BLU devices broadcast over Bluetooth, so they reach Indigo through a nearby MQTT device acting as a gateway: any device marked :white_check_mark: in the BLU gateway column above. When you turn on the BLU relay for a gateway in Indigo, the plugin installs and manages a small script on it that relays BLU broadcasts over MQTT, so no scripting is needed on your part.

- **Multiple gateways:** turn on the relay on several devices around your home to reach BLU devices out of range of a single gateway. A broadcast heard by more than one gateway is only processed once.
- **Signal strength:** each BLU device's RSSI state shows how well the gateway that relayed its latest broadcast heard it, which helps with placing gateways.

See [BLU Relay](blu-relay.md) for how the relay works, setup, and security considerations.

## BLU Devices

Encrypted BLU devices aren't supported yet, so leave encryption turned off on BLU devices you add to Indigo. Support for encrypted devices is planned. See [Security Considerations](blu-relay.md#security-considerations).

### BLU

| Model | Added in | Main state | Sensor value | Other states | Buttons | Settings |
| --- | :---: | --- | --- | --- | :---: | --- |
| [Shelly BLU Button1](https://kb.shelly.cloud/knowledge-base/shellyblu-button1) | 1.2.0 | :heavy_minus_sign: | :heavy_minus_sign: | :heavy_minus_sign: | 1 | :heavy_minus_sign: |
| [Shelly BLU RC Button 4](https://kb.shelly.cloud/knowledge-base/shelly-blu-rc-button-4-us) | 1.4.0 | :heavy_minus_sign: | :heavy_minus_sign: | :heavy_minus_sign: | 4 | :heavy_minus_sign: |
| [Shelly BLU Door/Window](https://kb.shelly.cloud/knowledge-base/shellyblu-door-window) | 1.2.0 | Open/closed | :heavy_minus_sign: | Illuminance, rotation (tilt angle) | 1 | :heavy_minus_sign: |
| [Shelly BLU Motion](https://kb.shelly.cloud/knowledge-base/shellyblu-motion) | 1.4.0 | Motion detected | :heavy_minus_sign: | Illuminance | 1 | :heavy_minus_sign: |
| [Shelly BLU H&T](https://kb.shelly.cloud/knowledge-base/shelly-blu-h-t) | 1.4.0 | :heavy_minus_sign: | Temperature | Temperature, humidity | 1 | Temperature unit (°F/°C), temperature offset |

- **Shelly BLU H&T:** the temperature offset is applied in the selected temperature unit.

### BLU+ZB

BLU+ZB devices support both Bluetooth and Zigbee. The plugin uses their Bluetooth broadcasts, relayed through a gateway like any other BLU device.

| Model | Added in | Main state | Sensor value | Other states | Buttons | Settings |
| --- | :---: | --- | --- | --- | :---: | --- |
| [Shelly BLU Distance](https://kb.shelly.cloud/knowledge-base/shelly-blu-distance) | 1.3.0 | :heavy_minus_sign: | Distance (mm), or how full a container is (%) | Distance, vibration | 1 | Distance offset, container level measurement |

- **Shelly BLU Distance:** turn on **Measure Level** and enter the container height and the sensor's height above the bottom of the container. The sensor value then shows how full the container is as a percentage, instead of the distance to the contents.

### Common BLU States

All BLU devices also report:

- **Battery level**
- **Signal strength** (RSSI) as received by the gateway
- **MAC address**
- **Packet ID,** a counter the device increases with each broadcast

Every BLU device has at least one button, which can fire [button events](events.md#button-events).
