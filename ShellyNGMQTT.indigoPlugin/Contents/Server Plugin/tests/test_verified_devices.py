import re
from pathlib import Path

from plugin import shelly_model_classes, verified_devices

ISSUE_FORM = (
    Path(__file__).resolve().parents[4]
    / ".github"
    / "ISSUE_TEMPLATE"
    / "device-verification.yml"
)


def test_every_model_in_registry():
    """New models must be added to verified_devices.json, even if nobody has verified them yet"""
    assert set(verified_devices) == set(shelly_model_classes)


def test_registry_names_match_display_names():
    """The verification workflow finds models by display name, so the names must match"""
    for type_id, model_class in shelly_model_classes.items():
        assert verified_devices[type_id]["name"] == model_class.display_name, type_id


def test_registry_entries_have_all_fields():
    """Every verification records the same fields, so the registry stays consistent"""
    for type_id, model in verified_devices.items():
        assert set(model) == {"name", "verified_by"}, type_id
        for entry in model["verified_by"]:
            assert set(entry) == {
                "github_username",
                "indigo_username",
                "anonymous",
                "firmware",
                "plugin_version",
                "issue",
            }, type_id


def test_issue_form_lists_every_model():
    """The device verification form's model menu offers exactly the plugin's models"""
    form = ISSUE_FORM.read_text()
    # The options of the "model" dropdown, up to its validations
    block = re.search(
        r"id: model\n.*?options:\n(.*?)\n\s+validations:", form, re.DOTALL
    )
    options = re.findall(r"^\s+- (.+)$", block.group(1), re.MULTILINE)

    assert len(options) == len(set(options))
    assert set(options) == {model["name"] for model in verified_devices.values()}
