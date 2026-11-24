"""Turn a device verification issue into an entry in the plugin's verified device registry.

Run by .github/workflows/device-verification.yml, which passes the issue in the
ISSUE_BODY, ISSUE_AUTHOR, and ISSUE_NUMBER environment variables:

    python3 scripts/device_verification.py > comment.md

It prints a Markdown comment for the issue. When the report is valid, it also adds
the verification to verified_devices.json and regenerates the Community
Verifications table in docs/supported-devices.md. It writes valid=true|false and
the model name to GITHUB_OUTPUT for the workflow's later steps.

The issue body is untrusted user input, so it's only ever read from the environment.

After editing verified_devices.json by hand, regenerate the docs table with:

    python3 scripts/device_verification.py --docs
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

REPO = Path(__file__).resolve().parent.parent
REGISTRY = (
    REPO
    / "ShellyNGMQTT.indigoPlugin"
    / "Contents"
    / "Resources"
    / "verified_devices.json"
)
DOCS = REPO / "docs" / "supported-devices.md"

# The generated table in DOCS sits between these markers
DOCS_START = "<!-- Generated from verified_devices.json by scripts/device_verification.py --docs. Don't edit by hand. -->"
DOCS_END = "<!-- End of generated table -->"

FORM_URL = "https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new"
FORUM_PROFILE_URL = "https://forums.indigodomo.com/memberlist.php"

# GitHub fills fields left empty in an issue form with this placeholder
NO_RESPONSE = "_No response_"


def parse_issue_form(body: str) -> dict[str, str]:
    """
    Split a GitHub issue form body into its fields.

    Each field is rendered as a "### <label>" heading followed by its value.

    :param body: The issue body.
    :return: The field values keyed by label, with empty fields as "".
    """
    body = body.replace("\r\n", "\n")
    fields = {}
    for match in re.finditer(
        r"^### ([^\n]+)\n(.*?)(?=^### |\Z)", body, re.MULTILINE | re.DOTALL
    ):
        value = match.group(2).strip()
        fields[match.group(1).strip()] = "" if value == NO_RESPONSE else value
    return fields


def is_checked(value: str) -> bool:
    """Whether an issue form checkboxes field has a checked box."""
    return re.search(r"^- \[[xX]\] ", value, re.MULTILINE) is not None


@dataclass
class Verification:
    """
    A device verification report from an issue.

    Anonymous verifications still record the usernames, so the verifier can be
    matched later, but they aren't credited by name.
    """

    model: str
    firmware: str
    plugin_version: str
    tested: str
    github_username: str | None
    indigo_username: str | None
    on_behalf: bool
    anonymous: bool
    issue: int

    @classmethod
    def from_issue(cls, body: str, author: str, number: int) -> "Verification":
        """
        Read a verification from a device verification issue.

        :param body: The issue body, as rendered from the issue form.
        :param author: The GitHub username of the issue author.
        :param number: The issue number.
        :return: The verification. It may be incomplete, see errors().
        """
        fields = parse_issue_form(body)
        github_username = author
        indigo_username = fields.get("Indigo forum username") or None
        on_behalf = is_checked(fields.get("Submitting for someone else?", ""))
        if on_behalf and indigo_username:
            # The author only filed the report for a forum user, so only the forum user is recorded
            github_username = None
        return cls(
            model=fields.get("Device model", ""),
            firmware=fields.get("Firmware version", ""),
            plugin_version=fields.get("Plugin version", ""),
            tested=fields.get("What did you test?", ""),
            github_username=github_username,
            indigo_username=indigo_username,
            on_behalf=on_behalf,
            anonymous=not is_checked(fields.get("Credit", "")),
            issue=number,
        )

    def type_id(self, registry: dict) -> str | None:
        """The device type id for the model, or None if the plugin doesn't have it."""
        for type_id, model in registry.items():
            if model["name"] == self.model:
                return type_id
        return None

    def errors(self, registry: dict) -> list[str]:
        """
        Find problems that keep the verification from being added.

        :param registry: The verified device registry.
        :return: A message for each problem, empty when the verification can be added.
        """
        errors = []
        if not self.model:
            errors.append("No device model was chosen.")
        elif self.type_id(registry) is None:
            errors.append(f"`{self.model}` isn't a model the plugin supports.")
        for label, value in [
            ("firmware version", self.firmware),
            ("plugin version", self.plugin_version),
        ]:
            if not value:
                errors.append(f"The {label} is missing.")
            elif not re.fullmatch(r"[\w./+-]{1,40}", value):
                errors.append(
                    f"The {label} should look like `1.4.4`, without spaces or other text."
                )
        if not self.tested:
            errors.append("Please describe what you tested.")
        if self.indigo_username is not None and not re.fullmatch(
            r"[^\n`|<>]{1,50}", self.indigo_username
        ):
            errors.append(
                "The Indigo forum username should be a single line of at most 50 characters."
            )
        if self.on_behalf and self.indigo_username is None:
            errors.append(
                "**Submitting for someone else** is checked, but there's no Indigo forum username for who verified the device."
            )
        return errors

    def entry(self) -> dict:
        """The entry for this verification in the registry's verified_by list."""
        return {
            "github_username": self.github_username,
            "indigo_username": self.indigo_username,
            "anonymous": self.anonymous,
            "firmware": self.firmware,
            "plugin_version": self.plugin_version,
            "issue": self.issue,
        }

    def add_to(self, registry: dict) -> None:
        """
        Add the verification to the registry.

        A verifier who already verified the model has their entry replaced, so
        re-testing on newer firmware doesn't list them twice.

        :param registry: The verified device registry, changed in place.
        """
        verified_by = registry[self.type_id(registry)]["verified_by"]
        if self.github_username:
            key, value = "github_username", self.github_username
        else:
            key, value = "indigo_username", self.indigo_username
        verified_by[:] = [entry for entry in verified_by if entry[key] != value]
        verified_by.append(self.entry())

    def summary(self, registry: dict) -> str:
        """
        A Markdown summary of the verification to comment on the issue.

        :param registry: The verified device registry, before the verification is added.
        :return: The comment body.
        """
        errors = self.errors(registry)
        if errors:
            return "\n".join(
                [
                    "This verification report can't be added yet:",
                    "",
                    *[f"- {error}" for error in errors],
                    "",
                    "Edit the issue to fix these, and this comment will update.",
                ]
            )

        verifier = [f"GitHub `{self.github_username}`"] if self.github_username else []
        verifier += (
            [f"Indigo forum `{self.indigo_username}`"] if self.indigo_username else []
        )
        verified_by = registry[self.type_id(registry)]["verified_by"]
        return "\n".join(
            [
                "Thanks for the report! Here's what will be added:",
                "",
                "| | |",
                "| --- | --- |",
                f"| Model | {self.model} (`{self.type_id(registry)}`) |",
                f"| Verifier | {', '.join(verifier)} |",
                f"| Credited by name | {'No (anonymous)' if self.anonymous else 'Yes'} |",
                f"| Firmware | `{self.firmware}` |",
                f"| Plugin version | `{self.plugin_version}` |",
                "",
                f"This model has already been verified {len(verified_by)} time(s)."
                if verified_by
                else "This will be the first verification of this model.",
            ]
        )


def markdown_text(text: str) -> str:
    """Escape the characters that would change how text renders in a Markdown link."""
    return re.sub(r"([\\\[\]*_`])", r"\\\1", text)


def verifier_credit(entry: dict) -> str:
    """
    Credit a verifier by name, linked to their profiles.

    :param entry: A non-anonymous entry from a model's verified_by list.
    :return: The GitHub username linked to their profile, followed by their Indigo
        forum username in parentheses when both are known.
    """
    forum = None
    if entry["indigo_username"]:
        query = urlencode({"mode": "viewprofile", "un": entry["indigo_username"]})
        forum = (
            f"[{markdown_text(entry['indigo_username'])}]({FORUM_PROFILE_URL}?{query})"
        )
    if not entry["github_username"]:
        return forum
    github = (
        f"[{entry['github_username']}](https://github.com/{entry['github_username']})"
    )
    return f"{github} ({forum})" if forum else github


def verification_table(registry: dict) -> str:
    """
    A Markdown table of every model's verification status, sorted by model name.

    Anonymous verifications count toward a model being verified, but are only
    shown as a count.

    :param registry: The verified device registry.
    :return: The table.
    """
    lines = ["| Model | Status | Verified by |", "| --- | --- | --- |"]
    for model in sorted(registry.values(), key=lambda model: model["name"]):
        name = markdown_text(model["name"])
        verified_by = model["verified_by"]
        if not verified_by:
            query = urlencode(
                {
                    "template": "device-verification.yml",
                    "title": f"Verify {model['name']}",
                    "model": model["name"],
                }
            )
            lines.append(
                f"| {name} | :warning: Not yet verified | [Report it]({FORM_URL}?{query}) |"
            )
            continue

        credit = ", ".join(
            verifier_credit(entry) for entry in verified_by if not entry["anonymous"]
        )
        anonymous = sum(entry["anonymous"] for entry in verified_by)
        if anonymous:
            credit = (
                f"{credit} and {anonymous} anonymous"
                if credit
                else f"{anonymous} anonymous"
            )
        lines.append(f"| {name} | :white_check_mark: Verified | {credit} |")
    return "\n".join(lines)


def with_verification_table(docs: str, registry: dict) -> str:
    """
    Replace the generated table in the docs page.

    :param docs: The page's Markdown, with the DOCS_START and DOCS_END markers.
    :param registry: The verified device registry.
    :return: The page with a regenerated table.
    :raises ValueError: If a marker is missing.
    """
    start = docs.index(DOCS_START) + len(DOCS_START)
    end = docs.index(DOCS_END)
    return f"{docs[:start]}\n\n{verification_table(registry)}\n\n{docs[end:]}"


def main(argv: list[str]) -> int:
    if argv[1:] == ["--docs"]:
        registry = json.loads(REGISTRY.read_text())
        DOCS.write_text(with_verification_table(DOCS.read_text(), registry))
        return 0

    verification = Verification.from_issue(
        os.environ["ISSUE_BODY"],
        os.environ["ISSUE_AUTHOR"],
        int(os.environ["ISSUE_NUMBER"]),
    )
    registry = json.loads(REGISTRY.read_text())
    valid = not verification.errors(registry)

    print(verification.summary(registry))
    if valid:
        verification.add_to(registry)
        REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
        DOCS.write_text(with_verification_table(DOCS.read_text(), registry))

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"valid={str(valid).lower()}\n")
            # The model is one of the registry's names when valid, so it's safe to pass on
            if valid:
                f.write(f"model={verification.model}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
