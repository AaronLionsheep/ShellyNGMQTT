# Contributing

Thanks for your interest in improving ShellyNGMQTT! Bug reports, new device support, fixes, tests, and documentation are all welcome.

## Ways to Contribute

- **Report a bug:** follow [Reporting Bugs](reporting-bugs.md) so the issue has everything needed to reproduce it.
- **Request or add a device:** open an issue with the device details listed in [Requesting a New Device](reporting-bugs.md#requesting-a-new-device), or follow [Adding a New Device](#adding-a-new-device) below.
- **Fix something:** issues are a good starting point. Comment on the issue before starting larger changes so work isn't duplicated.
- **Improve the docs:** corrections and clarifications to the README and `docs/` are always appreciated.

## Development Environment

The project uses a conda environment defined in [environment.yml](../environment.yml). It installs Python 3.13, ruff, pytest, the plugin's runtime dependencies from `requirements.txt`, and [pytest-indigo](https://github.com/AaronLionsheep/pytest-indigo), which provides the Indigo test fixtures.

```sh
git clone https://github.com/AaronLionsheep/ShellyNGMQTT.git
cd ShellyNGMQTT
conda env create -f environment.yml
```

Run tools inside the environment with `conda run`:

```sh
conda run -n shellyngmqtt-dev pytest
conda run -n shellyngmqtt-dev ruff check
conda run -n shellyngmqtt-dev ruff format
```

If `requirements.txt` or `environment.yml` changes, update the environment with `conda env update -f environment.yml --prune`.

### Testing in Indigo

Unit tests can't cover everything, so changes that touch device behavior should also be tried against real hardware in Indigo:

1. Copy `ShellyNGMQTT.indigoPlugin` into Indigo's plugin folder (`/Library/Application Support/Perceptive Automation/Indigo <version>/Plugins`), or double-click the bundle to install it.
2. Reload the plugin from the Indigo Plugins menu after each change.
3. Turn on debug logging in the plugin preferences to see MQTT traffic and state updates.

Indigo installs the packages from `requirements.txt` into `Contents/Packages` on first launch. That folder is git-ignored and should never be committed.

## Project Layout

All plugin code lives in `ShellyNGMQTT.indigoPlugin/Contents/Server Plugin/`:

| Path | Purpose |
| --- | --- |
| `plugin.py` | Plugin entry point: MQTT Connector integration, message routing, device lifecycle, UI callbacks, and the `shelly_model_classes` mapping of Indigo device type IDs to model classes |
| `shelly/devices/shelly.py` | `Shelly` base class with logic shared by all models |
| `shelly/devices/shelly_mqtt.py` | Base class for Wi-Fi/Ethernet devices that talk to the broker directly |
| `shelly/devices/shelly_blu.py` | Base class for BLU devices, including BTHome parsing and features backported from newer `bthome-ble` versions |
| `shelly/devices/shelly_*.py` | One class per Shelly model |
| `shelly/components/functional/` | Components that become Indigo devices: switch, input, light, cover, temperature, humidity |
| `shelly/components/system/` | Device-level components: system, Wi-Fi, Ethernet, BLE, MQTT, script, device power, H&T UI |
| `shelly/scripts/` | Scripts the plugin installs and manages on the Shelly device (the BLU relay) |
| `Devices.xml`, `Actions.xml`, `Events.xml`, `MenuItems.xml`, `PluginConfig.xml` | Indigo UI definitions |
| `ConfigTemplates/` | Shared config UI fragments included by the XML files |
| `tests/`, `shelly/**/tests/` | Unit tests, next to the code they cover |

`Contents/Resources/` holds the plugin icon and `indigo-blu-relay.js`, the JavaScript that runs on the Shelly device to relay BLU advertisements over MQTT.

## Coding Guidelines

- **Formatting and linting:** code must pass `ruff format --check` and `ruff check`. CI runs both on every pull request.
- **Put model-specific logic on the model class.** Per-model behavior belongs in classmethods on that model's class, not in `if model == ...` branches in `plugin.py`. Logic shared by many models goes on the `Shelly` base class in `shelly.py`.
- **Keep it minimal.** Write simple checks and preference reads inline. Don't add helper functions, dataclasses, or abstractions for simple logic. The exception is parsing code, which should get a dedicated dataclass (see [Testing](#testing)).
- **Dependencies:** every new dependency must work on both Apple Silicon and Intel Macs, preferably from pre-built wheels. CI fails if a package unexpectedly builds from source.
- **`bthome-ble` stays below 3.24.** Version 3.24 requires `cryptography>=49`, which has no Intel Mac wheels. If you need a feature from a newer release, backport it into `shelly_blu.py` instead of upgrading.

## Testing

Run the full suite with coverage:

```sh
conda run -n shellyngmqtt-dev pytest
```

Pass a path or `-k` to run part of the suite, for example `conda run -n shellyngmqtt-dev pytest -k blu_motion`.

- **Test pure logic.** Unit tests cover parsing, state calculation, validation, and similar logic that doesn't need a live Indigo server. Use the `plugin` and `indigo` fixtures from pytest-indigo where a test needs them, and never use `MagicMock` or monkeypatching on the `indigo` module or Indigo devices. If logic is hard to test without a mock, move it into a classmethod or function that takes plain data.
- **Parsing code needs thorough tests.** New parsing logic (BTHome data, RPC payloads, and so on) should come with a dedicated dataclass and tests that cover normal values, edge cases, and malformed input.
- **Every test has a docstring** saying what it checks and why, for example `"""Each call returns a separate dict so devices never share props"""`.
- **Coverage:** pytest prints a coverage report with missing lines. New code should be covered.

CI runs the suite on Apple Silicon and Intel macOS with Python 3.11 and 3.13, so avoid syntax or library features newer than Python 3.11.

## Adding a New Device

1. **Collect the device's data.** Save the output of `Shelly.GetDeviceInfo`, `Shelly.GetConfig`, and `Shelly.GetStatus` (or sample BTHome advertisements for BLU devices). You'll need them to choose components and write tests.
2. **Create the model class** in `shelly/devices/shelly_<model>.py`. Start from the closest existing model: `ShellyMQTT` subclasses for Wi-Fi/Ethernet devices, `ShellyBLU` subclasses for BLU devices. Set `display_name`, register the system and functional components the device has, and add any model-specific classmethods.
3. **Add the device to `Devices.xml`.** The `id` is the Indigo device type ID (for example `shelly-plus-1`), and its `<Name>` must match `display_name`.
4. **Register the class** in the `shelly_model_classes` mapping in `plugin.py`.
5. **Add tests** in the matching `tests/` folder. At minimum, cover `display_name`, the plugin props, and any parsing or state logic. See `shelly/devices/tests/test_shelly_blu_motion.py` for an example.
6. **Update the docs.** Add the device to the list in the [README](../README.md) and to the right table in [Supported Devices](supported-devices.md).
7. **Test on real hardware** if you can, and say in the pull request which models and firmware versions you tested.

## Pull Requests

1. Branch from `master`. Name the branch after the issue it addresses, for example `issue-77`.
2. Keep each pull request focused on one change. Unrelated fixes should go in their own pull requests.
3. Write commit messages as one short line in the imperative mood, for example `Add Shelly Pro 3EM support`.
4. Before pushing, run `ruff format`, `ruff check`, and `pytest`.
5. Open the pull request against `master` and link the issue (`Closes #77`). Describe what changed and how you tested it, including hardware and firmware versions where relevant.

Every pull request runs:

- **Code Quality:** `ruff check` and `ruff format --check`
- **Test:** unit tests on macOS (Apple Silicon and Intel) with Python 3.11 and 3.13
- **Install Dependencies:** installs `requirements.txt` on the same matrix and fails if a package unexpectedly builds from source

Dependency updates are opened automatically by Renovate (see [renovate.json](../renovate.json)).

## Releasing

Maintainers only.

1. Bump `PluginVersion` in `ShellyNGMQTT.indigoPlugin/Contents/Info.plist`. If the release needs features from a newer Indigo, update `ServerApiVersion` too.
2. Merge to `master` and tag the release with the bare version number (for example `1.4.0`).
3. Zip `ShellyNGMQTT.indigoPlugin` (without `Contents/Packages`) and attach it to a GitHub release with release notes.
4. <!-- TODO: Indigo Plugin Store / forum announcement steps -->
