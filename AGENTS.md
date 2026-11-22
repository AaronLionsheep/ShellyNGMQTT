# AGENTS.md

Guidance for AI coding agents working in this repository. Human contributors should read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md), which has the full details behind everything here.

## Project

An [Indigo](https://www.indigodomo.com) home automation plugin that integrates Shelly Gen2+ devices (and Shelly BLU Bluetooth sensors relayed through a Shelly gateway) over MQTT. Messages arrive through the MQTT Connector plugin; the plugin never talks to the broker directly.

All plugin code lives in `ShellyNGMQTT.indigoPlugin/Contents/Server Plugin/` (note the space in the path; quote it in shell commands).

- `plugin.py`: entry point, MQTT message routing, device lifecycle, UI callbacks, and the `shelly_model_classes` mapping of Indigo device type IDs to model classes
- `shelly/devices/shelly.py`: `Shelly` base class with logic shared by all models
- `shelly/devices/shelly_mqtt.py` / `shelly_blu.py`: base classes for Wi-Fi/Ethernet devices and BLU devices (BTHome parsing lives in `shelly_blu.py`)
- `shelly/devices/shelly_*.py`: one class per Shelly model
- `shelly/components/functional/`: components that become Indigo devices (switch, input, light, cover, temperature, humidity)
- `shelly/components/system/`: device-level components (system, Wi-Fi, Ethernet, BLE, MQTT, script, device power, H&T UI)
- `shelly/scripts/` and `Contents/Resources/indigo-blu-relay.js`: the BLU relay script the plugin installs and manages on Shelly devices
- `Devices.xml`, `Actions.xml`, `Events.xml`, `MenuItems.xml`, `PluginConfig.xml`, `ConfigTemplates/`: Indigo UI definitions
- `tests/`, `shelly/**/tests/`: unit tests, next to the code they cover

`Contents/Packages/` is installed by Indigo at runtime, is git-ignored, and must never be committed or edited.

### The `indigo` module

The `indigo` module is injected by the Indigo plugin host at runtime. It is not a real package: it can't be installed from PyPI or anywhere else, and it can never be imported outside Indigo. The `import indigo` lines in the plugin (marked with a `# pyright: ignore[reportMissingImports, ...]` comment) only resolve when Indigo runs the plugin.

- Don't try to install `indigo`, add it to `requirements.txt` or `environment.yml`, or run plugin modules directly with `python`.
- Don't add `try`/`except ImportError` fallbacks or stub `indigo` modules.
- For local offline testing, [pytest-indigo](https://github.com/AaronLionsheep/pytest-indigo) provides a mock `indigo` module and the `plugin` and `indigo` fixtures (see `conftest.py`). It is the only supported way to exercise code that uses `indigo` outside the host.
- Behavior that depends on real devices or the live Indigo server can only be verified by loading the plugin in Indigo (see [Testing in Indigo](docs/CONTRIBUTING.md#testing-in-indigo)).

## Commands

Run from the repo root. Tools live in the `shellyngmqtt-dev` conda environment (`conda env create -f environment.yml`); bare `pytest` and `ruff` are not on the PATH.

```sh
conda run -n shellyngmqtt-dev pytest                 # full suite with coverage
conda run -n shellyngmqtt-dev pytest -k blu_motion   # subset
conda run -n shellyngmqtt-dev ruff check
conda run -n shellyngmqtt-dev ruff format
```

CI runs `ruff check`, `ruff format --check`, and the test suite on Apple Silicon and Intel macOS with Python 3.11 and 3.13.

### Dependencies

- `ShellyNGMQTT.indigoPlugin/Contents/Server Plugin/requirements.in` lists the runtime packages the plugin imports directly, with only the version limits it needs. Indigo installs these on users' machines, so only add packages the plugin needs when it runs.
- `requirements.txt` next to it is a universal lockfile generated from `requirements.in` for both Apple Silicon and Intel Macs. Never edit it by hand. After changing `requirements.in`, regenerate it from the repo root with `conda run -n shellyngmqtt-dev scripts/compile-requirements.sh` (extra arguments go to `uv pip compile`). Keep the generated header; Renovate reads the command from it. CI fails if the lockfile is out of date.
- `environment.yml` defines the development environment: Python, ruff, pytest, pytest-cov, pytest-indigo, uv, plus everything from `requirements.txt`. Dev-only tools go here, never in `requirements.in`.
- After any of these files change, update the environment with `conda env update -f environment.yml --prune`.

## Rules

- **Python 3.11 compatible.** Don't use syntax or library features newer than 3.11.
- **Model-specific logic goes on the model class.** Add a default classmethod on `Shelly` in `shelly.py` and override it per model; call it from `plugin.py` via `shelly_model_classes`. Never add `if type_id == ...` branches in `plugin.py`. Shared helpers go on `Shelly`, not on a subclass like `ShellyBLU`.
- **Keep code minimal.** Read preferences and write simple checks inline. Don't add helper functions, dataclasses, or abstraction layers for simple logic. Propose the lean version first when scope is unclear.
- **Parsing code is the exception.** New parsing logic (BTHome bytes, RPC payloads) gets a dedicated dataclass and thorough tests (normal values, edge cases, malformed input) in the same change. Reuse `bthome_ble` definitions such as `MeasTypes` where they fit.
- **Intel Macs must keep working.** `bthome-ble` stays on 3.23.4 (3.23.5+ needs `cryptography>=49`, which has no Intel wheels). Backport newer `bthome-ble` features into `shelly_blu.py` instead of upgrading. New dependencies must install from pre-built wheels on both architectures.

## Testing

- Unit tests cover pure logic: parsing, state calculation, validation. Use the `plugin` and `indigo` fixtures from [pytest-indigo](https://github.com/AaronLionsheep/pytest-indigo) when a test needs them.
- Never use `MagicMock` or monkeypatching on the `indigo` module or Indigo devices; pytest-indigo's mock is the only one allowed. If logic is hard to test without a mock, move it into a classmethod or function that takes plain data, or leave it untested.
- Every test function has a one-line docstring saying what it checks and why, for example `"""Each call returns a separate dict so devices never share props"""`.
- New code should be covered; pytest prints missing lines.

## Adding a Device

Follow [Adding a New Device](docs/CONTRIBUTING.md#adding-a-new-device): create `shelly/devices/shelly_<model>.py` from the closest existing model, add it to `Devices.xml` (its `<Name>` must match `display_name`), register it in `shelly_model_classes`, add tests, and update the README and [docs/supported-devices.md](docs/supported-devices.md). Title the PR with the `device` scope, for example `feat(device): add Shelly 1 PM Gen 3`.

## Docs and Git

- Write Markdown with each paragraph and list item on a single line; don't hard-wrap prose.
- User-facing behavior changes should update the matching page in `docs/`.
- Branch from `master`, named after the issue (for example `issue-77`).
- **Pull request titles must use [Conventional Commits](https://www.conventionalcommits.org) style**, for example `feat: add Shelly Pro 3EM support` or `fix: handle missing BLU battery level`. The Lint PR workflow enforces this. Release-please reads the title to build the changelog and choose the next version (`feat` → minor, `fix` → patch, `!` → major). Scopes are optional, for example `feat(device): add Shelly 1 PM Gen 3` when adding a new device. See [Pull Requests](docs/CONTRIBUTING.md#pull-requests) for the common types.
- Conventional Commits style is encouraged but not required for individual commit messages. Keep them to one short line, for example `feat: add Shelly Pro 3EM support` or `Add Shelly Pro 3EM support`.
- **Never bump versions by hand.** Release-please handles version bumps (`.release-please-manifest.json` and `PluginVersion` in `Info.plist`, between the `x-release-please` markers) and the changelog through its automated release PR. Don't edit those values, the markers, or the changelog.
