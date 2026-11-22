#!/usr/bin/env bash
# Regenerate the plugin's requirements.txt lockfile from requirements.in for Apple Silicon and Intel Macs.
# Extra arguments are passed to uv, for example --upgrade or --upgrade-package habluetooth.
# Run from the Server Plugin directory so uv writes a header without the space in the path; Renovate reads the
# command from that header, so it must stay a plain uv pip compile command. Renovate also requires options that take
# a value to use '=' (--python-version=3.11, not --python-version 3.11).
set -euo pipefail

cd "$(dirname "$0")/../ShellyNGMQTT.indigoPlugin/Contents/Server Plugin"
uv pip compile requirements.in --universal --python-version=3.11 --output-file=requirements.txt "$@"
