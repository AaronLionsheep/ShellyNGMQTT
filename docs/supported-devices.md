# Supported Devices

ShellyNGMQTT supports Shelly Gen2+ Wi-Fi devices over MQTT, and Shelly BLU Bluetooth devices relayed through them. Gen1 devices are supported by the [ShellyMQTT](https://www.indigodomo.com/pluginstore/236/) plugin instead.

Don't see your device? Open a [new device request](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=new-device.yml).

## How Devices Appear in Indigo

When you create a Wi-Fi Shelly device, the plugin creates one Indigo device for each part of it, called a component. For example, a Shelly Plus 1 becomes two Indigo devices: a **Switch** for the relay and an **Input** for the switch terminal. The devices are grouped together in Indigo, and editing any one of them opens the settings for the whole Shelly.

Each BLU device is a single Indigo device.

## MQTT Devices

In the tables below:

- **Power metering:** the device reports power, energy, voltage, and current to Indigo.
- **BLU gateway:** the device can relay Shelly BLU devices to Indigo. See [BLU Gateways](#blu-gateways).

### Gen2

| Model | Indigo devices created | Power metering | BLU gateway |
| --- | --- | :---: | :---: |
| Shelly Plus 1 | 1 Switch, 1 Input | | ✓ |
| Shelly Plus 1 PM | 1 Switch, 1 Input | ✓ | ✓ |
| Shelly Plus 2 PM | 2 Switches and 2 Inputs, or 1 Cover and 2 Inputs | ✓ | ✓ |
| Shelly Plus WallDimmer | 1 Light | ✓ | ✓ |
| Shelly Plus I4 | 4 Inputs | | ✓ |
| Shelly Plus H&T | 1 Temperature, 1 Humidity | | |
| Shelly Plus Plug (US/IT) | 1 Switch | ✓ | ✓ |
| Shelly Plus Plug S | 1 Switch | ✓ | ✓ |
| Shelly Plus Plug UK | 1 Switch | ✓ | ✓ |
| Shelly Pro 1 | 1 Switch, 2 Inputs | | ✓ |
| Shelly Pro 1 PM | 1 Switch, 2 Inputs | ✓ | ✓ |
| Shelly Pro 2 | 2 Switches, 2 Inputs | | ✓ |
| Shelly Pro 2 PM | 2 Switches, 2 Inputs | ✓ | ✓ |
| Shelly Pro 4 PM | 4 Switches, 4 Inputs | ✓ | ✓ |

- **Shelly Plus 2 PM:** choose the **Switch** or **Cover (Roller/Shutter)** profile in the device settings, matching the profile set on the Shelly. Use Cover for roller shutters, blinds, and garage doors.
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
| Input | Sensor | On/off (pressed or switch closed) | |
| Temperature | Sensor | Temperature | Temperature in °C and °F |
| Humidity | Sensor | Humidity (%) | |

Inputs set up as buttons on the Shelly can also fire [button events](events.md#button-events) for button down/up and single, double, triple, and long presses.

## BLU Gateways

Shelly BLU devices broadcast over Bluetooth, so they reach Indigo through a nearby MQTT device acting as a gateway: any device marked ✓ in the BLU gateway column above. When you turn on the BLU relay for a gateway in Indigo, the plugin installs and manages a small script on it that relays BLU broadcasts over MQTT, so no scripting is needed on your part.

- **Multiple gateways:** turn on the relay on several devices around your home to reach BLU devices out of range of a single gateway. A broadcast heard by more than one gateway is only processed once.
- **Signal strength:** each BLU device's RSSI state shows how well the gateway that relayed its latest broadcast heard it, which helps with placing gateways.

See [BLU Relay](blu-relay.md) for how the relay works, setup, and security considerations.

## BLU Devices

Encrypted BLU devices aren't supported yet, so leave encryption turned off on BLU devices you add to Indigo. Support for encrypted devices is planned. See [Security Considerations](blu-relay.md#security-considerations).

### BLU

| Model | Main state | Sensor value | Other states | Buttons | Settings |
| --- | --- | --- | --- | :---: | --- |
| Shelly BLU Button1 | | | | 1 | |
| Shelly BLU RC Button 4 | | | | 4 | |
| Shelly BLU Door/Window | Open/closed | | Illuminance, rotation (tilt angle) | 1 | |
| Shelly BLU Motion | Motion detected | | Illuminance | 1 | |
| Shelly BLU H&T | | Temperature | Temperature, humidity | 1 | Temperature unit (°F/°C), temperature offset |

- **Shelly BLU H&T:** the temperature offset is applied in the selected temperature unit.

### BLU+ZB

BLU+ZB devices support both Bluetooth and Zigbee. The plugin uses their Bluetooth broadcasts, relayed through a gateway like any other BLU device.

| Model | Main state | Sensor value | Other states | Buttons | Settings |
| --- | --- | --- | --- | :---: | --- |
| Shelly BLU Distance | | Distance (mm), or how full a container is (%) | Distance, vibration | 1 | Distance offset, container level measurement |

- **Shelly BLU Distance:** turn on **Measure Level** and enter the container height and the sensor's height above the bottom of the container. The sensor value then shows how full the container is as a percentage, instead of the distance to the contents.

### Common BLU States

All BLU devices also report:

- **Battery level**
- **Signal strength** (RSSI) as received by the gateway
- **MAC address**
- **Packet ID,** a counter the device increases with each broadcast

Every BLU device has at least one button, which can fire [button events](events.md#button-events).
