# :handshake: Contributing

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

The two dependency files have separate jobs:

- `ShellyNGMQTT.indigoPlugin/Contents/Server Plugin/requirements.in` lists the runtime packages the plugin imports directly, with only the version limits it needs (such as the Intel Mac limits). Indigo installs these on users' machines, so only add packages the plugin needs when it runs.
- [environment.yml](../environment.yml) defines the development environment. Dev-only tools like ruff, pytest, pytest-indigo, and uv go here, never in `requirements.in`.

`requirements.txt` next to it is a lockfile generated from `requirements.in`, pinning every package (including indirect ones) for both Apple Silicon and Intel Macs. Indigo installs from it. Don't edit it by hand; after changing `requirements.in`, regenerate it from the repo root with [scripts/compile-requirements.sh](../scripts/compile-requirements.sh). Extra arguments are passed to `uv pip compile`, for example `--upgrade-package habluetooth`:

```sh
conda run -n shellyngmqtt-dev scripts/compile-requirements.sh
```

Keep the generated header: Renovate reads the `uv pip compile` command from it to regenerate the lockfile, so the script must keep calling uv directly. Renovate opens a PR for each new release of a package in `requirements.in` that only updates the lockfile, and a regular lockfile maintenance PR that updates the indirect packages.

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

`Contents/Resources/` holds the plugin icon, `indigo-blu-relay.js` (the JavaScript that runs on the Shelly device to relay BLU advertisements over MQTT), and `verified_devices.json` (see [Device Verification](#device-verification)).

## Coding Guidelines

- **Formatting and linting:** code must pass `ruff format --check` and `ruff check`. CI runs both on every pull request.
- **Put model-specific logic on the model class.** Per-model behavior belongs in classmethods on that model's class, not in `if model == ...` branches in `plugin.py`. Logic shared by many models goes on the `Shelly` base class in `shelly.py`.
- **Keep it minimal.** Write simple checks and preference reads inline. Don't add helper functions, dataclasses, or abstractions for simple logic. The exception is parsing code, which should get a dedicated dataclass (see [Testing](#testing)).
- **Dependencies:** every new dependency must work on both Apple Silicon and Intel Macs, preferably from pre-built wheels. CI fails if a package unexpectedly builds from source.
- **`bthome-ble` stays on 3.23.4.** Version 3.23.5 and newer require `cryptography>=49`, which has no Intel Mac wheels. If you need a feature from a newer release, backport it into `shelly_blu.py` instead of upgrading.

## Testing

Run the full suite with coverage:

```sh
conda run -n shellyngmqtt-dev pytest
```

Pass a path or `-k` to run part of the suite, for example `conda run -n shellyngmqtt-dev pytest -k blu_motion`.

- **Test pure logic.** Unit tests cover parsing, state calculation, validation, and similar logic that doesn't need a live Indigo server. Use the `plugin` and `indigo` fixtures from pytest-indigo where a test needs them, and never use `MagicMock` or monkeypatching on the `indigo` module or Indigo devices. If logic is hard to test without a mock, move it into a classmethod or function that takes plain data.
- **Parsing code needs thorough tests.** New parsing logic (BTHome data, RPC payloads, and so on) should come with a dedicated dataclass and tests that cover normal values, edge cases, and malformed input.
- **Every test has a docstring** saying what it checks and why, for example `"""Each call returns a separate dict so devices never share props"""`.
- **Coverage:** pytest prints a coverage report with missing lines. New code should be covered. On pull requests, CI combines coverage from every Python version, adds the total to the run summary, and comments on the pull request with the coverage of the changed lines. No minimum is enforced yet.

CI runs the suite on Linux with Python 3.11 and 3.13, so keep tests platform-independent and avoid syntax or library features newer than Python 3.11.

## Adding a New Device

1. **Collect the device's data.** Save the output of `Shelly.GetDeviceInfo`, `Shelly.GetConfig`, and `Shelly.GetStatus` (or sample BTHome advertisements for BLU devices). You'll need them to choose components and write tests.
2. **Create the model class** in `shelly/devices/shelly_<model>.py`. Start from the closest existing model: `ShellyMQTT` subclasses for Wi-Fi/Ethernet devices, `ShellyBLU` subclasses for BLU devices. Set `display_name`, register the system and functional components the device has, and add any model-specific classmethods.
3. **Add the device to `Devices.xml`.** The `id` is the Indigo device type ID (for example `shelly-plus-1`), and its `<Name>` must match `display_name`.
4. **Register the class** in the `shelly_model_classes` mapping in `plugin.py`.
5. **Add the model to the verification registry.** Add an entry to `Contents/Resources/verified_devices.json` with the model's `display_name` as `name`, and add the name to the model menu in [.github/ISSUE_TEMPLATE/device-verification.yml](../.github/ISSUE_TEMPLATE/device-verification.yml). Leave `verified_by` empty unless you've tested the model on a real device (see [Device Verification](#device-verification)). Then run `python3 scripts/device_verification.py --docs` to add the model to the Community Verifications table in [Supported Devices](supported-devices.md#community-verifications).
6. **Add tests** in the matching `tests/` folder. At minimum, cover `display_name`, the plugin props, and any parsing or state logic. See `shelly/devices/tests/test_shelly_blu_motion.py` for an example.
7. **Update the docs.** Add the device to the list in the [README](../README.md) and to the right table in [Supported Devices](supported-devices.md), linking the model name to its [Shelly Knowledge Base](https://kb.shelly.cloud) page.
8. **Test on real hardware** if you can, and say in the pull request which models and firmware versions you tested.

### Device Verification

`Contents/Resources/verified_devices.json` lists every model with the people who confirmed it works on a real device. Models with an empty `verified_by` list show a warning in the device creation dialog and log a warning when the device starts. Tests check that the registry and the issue form's model menu match `shelly_model_classes`.

The [Community Verifications](supported-devices.md#community-verifications) table in Supported Devices is generated from the registry. Each model links its verifiers' GitHub profiles, with their Indigo forum profile in parentheses, and anonymous verifications are only counted. Don't edit the table by hand: after changing `verified_devices.json`, run `python3 scripts/device_verification.py --docs`. A test fails if the table is out of date.

A verification is a community note of support that a model worked for someone, not a warranty. Verifiers aren't responsible or liable for how the device or the plugin works for anyone else.

Each `verified_by` entry has these fields:

| Field | Value |
| --- | --- |
| `github_username` | GitHub username of the issue author, or `null` when the issue was filed for a forum user |
| `indigo_username` | Indigo forum username, or `null` |
| `anonymous` | `true` if the verifier asked not to be credited by name |
| `firmware` | Shelly firmware version tested |
| `plugin_version` | Plugin version tested |
| `issue` | The device verification issue number |

Users report verifications with the [device verification](https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=device-verification.yml) issue form. In Indigo, **Plugins → ShellyNGMQTT → Report Device Verification...** logs a link to the form with the firmware and plugin version filled in and the model in the title (GitHub can't fill in dropdowns from a link, so the reporter picks the model). The firmware version is optional. The [Device verification](../.github/workflows/device-verification.yml) workflow handles the rest, using [scripts/device_verification.py](../scripts/device_verification.py):

1. When an issue with the `device verification` label is opened or edited, the workflow checks the report and comments on the issue with what will be added, or the problems to fix first.
2. For a valid report, it opens (or updates) a `chore(device): verify <model>` pull request that adds the entry, regenerates the Community Verifications table, and closes the issue. If an edit makes the report invalid, the pull request is closed until it's fixed.
3. The pull request requests a review from the repository owner and is assigned to them. Checks on pull requests opened by GitHub Actions wait for approval, so approve the workflows on the pull request to run them, then merge it to approve the verification. To reject a report, close the issue, which also closes the pull request.

Leaving the **Credit** box unchecked sets `anonymous` to `true`. The usernames are still recorded, so a later verification by the same person replaces it, but anything that credits verifiers by name should leave anonymous entries out. It still counts toward the model being verified.

To credit an Indigo forum user who doesn't have a GitHub account, open the issue yourself with their forum username and check **Submitting for someone else**.

## Pull Requests

1. Branch from `master`. Name the branch after the issue it addresses, for example `issue-77`.
2. Keep each pull request focused on one change. Unrelated fixes should go in their own pull requests.
3. Write commit messages as one short line in the imperative mood. [Conventional Commits](https://www.conventionalcommits.org) style is encouraged but not required, for example `feat: add Shelly Pro 3EM support` or `Add Shelly Pro 3EM support`.
4. Before pushing, run `ruff format`, `ruff check`, and `pytest`.
5. Open the pull request against `master` and link the issue (`Closes #77`). Describe what changed and how you tested it, including hardware and firmware versions where relevant.
6. **Give the pull request a [Conventional Commits](https://www.conventionalcommits.org) title**, for example `feat: add Shelly Pro 3EM support` or `fix: handle missing BLU battery level`. This is required: the title becomes the commit message on `master`, and release-please uses it to write the changelog and choose the next version (see [Releasing](#releasing)).

Common title types:

| Type | Use for | Version bump |
| --- | --- | --- |
| `feat` | New features and device support | Minor |
| `fix` | Bug fixes | Patch |
| `docs` | Documentation only | None |
| `build` | Dependencies and packaging | None |
| `chore` | Maintenance that doesn't fit elsewhere | None |
| `ci` | GitHub workflows | None |
| `test` | Tests only | None |
| `refactor` | Code changes that don't change behavior | None |

An optional scope in parentheses after the type narrows down what changed, for example `feat(device): add Shelly 1 PM Gen 3` when adding a new device.

Add `!` after the type (for example `feat!: drop support for Indigo 2023.1`) for a breaking change, which bumps the major version.

Every pull request runs:

- **Lint PR:** checks that the title follows Conventional Commits
- **Code Quality:** `ruff check` and `ruff format --check`
- **Test:** unit tests on Linux with Python 3.11 and 3.13
- **Lockfile Up to Date:** regenerates `requirements.txt` and fails if it doesn't match `requirements.in`

Pull requests that change `requirements.in` or `requirements.txt` also run **Install Dependencies**, which installs `requirements.txt` on Apple Silicon and Intel macOS with Python 3.11 and 3.13, fails if a package unexpectedly builds from source, and checks that the plugin's dependencies import. It also runs weekly to catch breakage that doesn't come from a lockfile change.

Dependency updates are opened automatically by Renovate (see [renovate.json](../renovate.json)).

## Releasing

Releases are automated with [release-please](https://github.com/googleapis/release-please). Don't bump versions or edit the changelog by hand.

1. Every merge to `master` updates an open release pull request. It collects the Conventional Commits titles merged since the last release, writes the changelog, and bumps the version in [.release-please-manifest.json](../.release-please-manifest.json) and `PluginVersion` in `ShellyNGMQTT.indigoPlugin/Contents/Info.plist`.
2. When it's time to release, a maintainer merges the release pull request. Release-please then tags the release and creates the GitHub release, and the workflow zips `ShellyNGMQTT.indigoPlugin` and attaches it.
3. <!-- TODO: Indigo Plugin Store / forum announcement steps -->

If a release needs features from a newer Indigo, update `ServerApiVersion` in `Info.plist` in a regular pull request before merging the release pull request.

Configuration lives in [release-please-config.json](../release-please-config.json) and [.github/workflows/release-please.yml](../.github/workflows/release-please.yml).
