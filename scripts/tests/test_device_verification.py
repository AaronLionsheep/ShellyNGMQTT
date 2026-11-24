import json

import pytest

from scripts import device_verification
from scripts.device_verification import Verification, is_checked, parse_issue_form

CREDIT = "List my GitHub username, and my Indigo forum username if given, publicly as a verifier of this model"
ON_BEHALF = (
    "I'm submitting this for the Indigo forum user named above, who verified the device"
)


def issue_body(
    model="Shelly Pro 2",
    firmware="1.4.4",
    plugin_version="1.5.0",
    tested="Turned both relays on and off from Indigo.",
    indigo_username="_No response_",
    on_behalf=False,
    credit=True,
):
    """Build an issue body the way GitHub renders the device verification form."""
    return f"""### Device model

{model}

### Firmware version

{firmware}

### Plugin version

{plugin_version}

### What did you test?

{tested}

### Indigo forum username

{indigo_username}

### Submitting for someone else?

- [{"X" if on_behalf else " "}] {ON_BEHALF}

### Credit

- [{"X" if credit else " "}] {CREDIT}"""


def make_entry(github_username=None, indigo_username=None, anonymous=False, issue=None):
    """A registry entry for the given verifier."""
    return {
        "github_username": github_username,
        "indigo_username": indigo_username,
        "anonymous": anonymous,
        "firmware": "1.0.0",
        "plugin_version": "0.1.0",
        "issue": issue,
    }


def make_registry():
    """A small registry with one verified and one unverified model."""
    return {
        "shelly-pro-2": {"name": "Shelly Pro 2", "verified_by": []},
        "shelly-plus-1": {
            "name": "Shelly Plus 1",
            "verified_by": [make_entry(github_username="someone")],
        },
    }


def verification(author="tester", number=42, **fields):
    """Read a verification from an issue body built with the given fields."""
    return Verification.from_issue(issue_body(**fields), author, number)


class TestParseIssueForm:
    def test_fields_keyed_by_label(self):
        """Each "### label" heading starts a field holding the text below it"""
        fields = parse_issue_form(issue_body())

        assert fields["Device model"] == "Shelly Pro 2"
        assert fields["Firmware version"] == "1.4.4"
        assert (
            fields["What did you test?"] == "Turned both relays on and off from Indigo."
        )

    def test_no_response_is_empty(self):
        """GitHub's placeholder for an empty field is read as an empty value"""
        assert parse_issue_form(issue_body())["Indigo forum username"] == ""

    def test_multiline_value(self):
        """Textarea values keep every line up to the next heading"""
        fields = parse_issue_form(issue_body(tested="Relay 1 on/off\n\nRelay 2 on/off"))

        assert fields["What did you test?"] == "Relay 1 on/off\n\nRelay 2 on/off"

    def test_windows_line_endings(self):
        """Bodies edited in some browsers use CRLF line endings"""
        fields = parse_issue_form(issue_body().replace("\n", "\r\n"))

        assert fields["Device model"] == "Shelly Pro 2"
        assert fields["Firmware version"] == "1.4.4"

    def test_heading_lookalike_inside_value(self):
        """A "###" that isn't at the start of a line doesn't start a new field"""
        fields = parse_issue_form(issue_body(tested="Pressed button ### 1"))

        assert fields["What did you test?"] == "Pressed button ### 1"

    @pytest.mark.parametrize("body", ["", "Just some text", "## Device model\n\nX"])
    def test_not_an_issue_form(self, body):
        """Bodies that weren't made from the form have no fields"""
        assert parse_issue_form(body) == {}


class TestIsChecked:
    @pytest.mark.parametrize("value", ["- [X] Yes", "- [x] Yes", "- [ ] No\n- [X] Yes"])
    def test_checked(self, value):
        """A box checked in the form or edited by hand in the body counts"""
        assert is_checked(value)

    @pytest.mark.parametrize("value", ["", "- [ ] Yes", "[X] Yes", "Text - [X] Yes"])
    def test_not_checked(self, value):
        """Unchecked boxes and text that only looks like a box don't count"""
        assert not is_checked(value)


class TestFromIssue:
    def test_complete_report(self):
        """All form fields are read, and the issue author gets credit"""
        result = verification(indigo_username="Forum Name")

        assert result == Verification(
            model="Shelly Pro 2",
            firmware="1.4.4",
            plugin_version="1.5.0",
            tested="Turned both relays on and off from Indigo.",
            github_username="tester",
            indigo_username="Forum Name",
            on_behalf=False,
            anonymous=False,
            issue=42,
        )

    def test_no_indigo_username(self):
        """The Indigo forum username is optional"""
        assert verification().indigo_username is None

    def test_on_behalf_of_forum_user(self):
        """Reports filed for a forum user credit only the forum user, not the author"""
        result = verification(indigo_username="Forum Name", on_behalf=True)

        assert result.github_username is None
        assert result.indigo_username == "Forum Name"

    def test_on_behalf_without_indigo_username(self):
        """Without a forum user to credit, the author keeps credit (and errors() flags it)"""
        result = verification(on_behalf=True)

        assert result.github_username == "tester"
        assert result.on_behalf

    def test_anonymous(self):
        """Without the credit box, the usernames are still recorded but flagged anonymous"""
        result = verification(indigo_username="Forum Name", credit=False)

        assert result.github_username == "tester"
        assert result.indigo_username == "Forum Name"
        assert result.anonymous

    def test_anonymous_on_behalf(self):
        """A forum user filed for anonymously is still recorded by forum username only"""
        result = verification(
            indigo_username="Forum Name", on_behalf=True, credit=False
        )

        assert result.github_username is None
        assert result.indigo_username == "Forum Name"
        assert result.anonymous

    def test_empty_body(self):
        """An empty body reads as an empty anonymous report instead of raising"""
        result = Verification.from_issue("", "tester", 1)

        assert result.model == ""
        assert result.firmware is None
        assert result.github_username == "tester"
        assert result.anonymous


class TestTypeId:
    def test_known_model(self):
        """Models are matched by their display name"""
        assert verification().type_id(make_registry()) == "shelly-pro-2"

    @pytest.mark.parametrize(
        "model", ["Shelly Pro 3", "shelly pro 2", "shelly-pro-2", ""]
    )
    def test_unknown_model(self, model):
        """Names must match exactly, and device type ids aren't names"""
        assert verification(model=model).type_id(make_registry()) is None


class TestErrors:
    def test_valid_report(self):
        """A complete report has no errors"""
        assert verification().errors(make_registry()) == []

    def test_valid_anonymous_report(self):
        """Credit is optional, so anonymous reports are valid"""
        assert verification(credit=False).errors(make_registry()) == []

    def test_missing_model(self):
        """A report must name a model"""
        assert verification(model="_No response_").errors(make_registry()) == [
            "No device model was chosen."
        ]

    def test_unknown_model(self):
        """A model the plugin doesn't have can't be verified"""
        assert verification(model="Shelly Pro 3").errors(make_registry()) == [
            "`Shelly Pro 3` isn't a model the plugin supports."
        ]

    @pytest.mark.parametrize(
        "firmware",
        ["1.4.4", "1.4.4-beta2", "20241011-114455/1.4.4-g6d2a586", "2.0"],
    )
    def test_valid_firmware(self, firmware):
        """Firmware versions and Shelly's full firmware ids are accepted"""
        assert verification(firmware=firmware).errors(make_registry()) == []

    @pytest.mark.parametrize(
        "firmware", ["1.4.4 (latest)", "`1.4.4`", "1.4.4\n2.0", "x" * 41]
    )
    def test_invalid_firmware(self, firmware):
        """Firmware must be a single version, so it renders safely in comments"""
        assert verification(firmware=firmware).errors(make_registry()) == [
            "The firmware version should look like `1.4.4`, without spaces or other text."
        ]

    def test_missing_firmware(self):
        """Firmware is optional, since a model can be verified without knowing it"""
        result = verification(firmware="_No response_")

        assert result.firmware is None
        assert result.errors(make_registry()) == []

    def test_missing_plugin_version(self):
        """The plugin version is required"""
        result = verification(plugin_version="_No response_")

        assert result.errors(make_registry()) == ["The plugin version is missing."]

    def test_missing_tested(self):
        """The report must say what was tested"""
        assert verification(tested="_No response_").errors(make_registry()) == [
            "Please describe what you tested."
        ]

    @pytest.mark.parametrize(
        "indigo_username", ["Forum Name", "a", "x" * 50, "Name (Ünïcode)"]
    )
    def test_valid_indigo_username(self, indigo_username):
        """Forum usernames may have spaces and other characters"""
        result = verification(indigo_username=indigo_username)

        assert result.errors(make_registry()) == []

    @pytest.mark.parametrize(
        "indigo_username", ["x" * 51, "`name`", "a|b", "<b>name</b>"]
    )
    def test_invalid_indigo_username(self, indigo_username):
        """Forum usernames can't break out of the summary's code spans or table"""
        result = verification(indigo_username=indigo_username)

        assert result.errors(make_registry()) == [
            "The Indigo forum username should be a single line of at most 50 characters."
        ]

    def test_invalid_indigo_username_checked_when_anonymous(self):
        """Anonymous reports still record the forum username, so it's still checked"""
        result = verification(indigo_username="`name`", credit=False)

        assert result.errors(make_registry()) == [
            "The Indigo forum username should be a single line of at most 50 characters."
        ]

    @pytest.mark.parametrize("credit", [True, False])
    def test_on_behalf_without_indigo_username(self, credit):
        """Filing for someone else needs the forum username of who verified the device"""
        result = verification(on_behalf=True, credit=credit)

        assert result.errors(make_registry()) == [
            "**Submitting for someone else** is checked, but there's no Indigo forum username for who verified the device."
        ]

    def test_all_errors_reported(self):
        """Every problem is listed at once, so one edit can fix them all"""
        result = Verification.from_issue("", "tester", 1)

        assert len(result.errors(make_registry())) == 3


class TestEntry:
    def test_entry(self):
        """The registry entry holds who verified the model and on what versions"""
        assert verification(indigo_username="Forum Name").entry() == {
            "github_username": "tester",
            "indigo_username": "Forum Name",
            "anonymous": False,
            "firmware": "1.4.4",
            "plugin_version": "1.5.0",
            "issue": 42,
        }

    def test_anonymous_entry(self):
        """Anonymous entries keep the usernames, flagged so they aren't credited by name"""
        entry = verification(credit=False).entry()

        assert entry["github_username"] == "tester"
        assert entry["anonymous"] is True


class TestAddTo:
    def test_first_verification(self):
        """An unverified model gets its first verifier"""
        registry = make_registry()

        verification().add_to(registry)

        assert registry["shelly-pro-2"]["verified_by"] == [verification().entry()]

    def test_additional_verifier(self):
        """Other people's verifications are kept"""
        registry = make_registry()

        verification(model="Shelly Plus 1").add_to(registry)

        assert [
            e["github_username"] for e in registry["shelly-plus-1"]["verified_by"]
        ] == ["someone", "tester"]

    def test_same_github_user_replaced(self):
        """Re-verifying replaces the person's earlier entry instead of listing them twice"""
        registry = make_registry()
        report = verification(author="someone", model="Shelly Plus 1")

        report.add_to(registry)

        assert registry["shelly-plus-1"]["verified_by"] == [report.entry()]

    def test_same_forum_user_replaced(self):
        """Forum users filed for by someone else are matched by forum username"""
        registry = make_registry()

        verification(indigo_username="Forum Name", on_behalf=True).add_to(registry)
        verification(
            author="other", number=43, indigo_username="Forum Name", on_behalf=True
        ).add_to(registry)

        assert [e["issue"] for e in registry["shelly-pro-2"]["verified_by"]] == [43]

    def test_forum_entry_doesnt_replace_github_entry(self):
        """A forum-only report doesn't remove an entry with no forum username"""
        registry = make_registry()

        verification(
            model="Shelly Plus 1", indigo_username="Forum Name", on_behalf=True
        ).add_to(registry)

        assert len(registry["shelly-plus-1"]["verified_by"]) == 2

    def test_anonymous_entry_replaced_by_same_user(self):
        """Anonymous entries keep the username, so the same person re-verifying replaces it"""
        registry = make_registry()
        registry["shelly-pro-2"]["verified_by"].append(
            make_entry(github_username="tester", anonymous=True, issue=1)
        )

        verification().add_to(registry)

        assert registry["shelly-pro-2"]["verified_by"] == [verification().entry()]


class TestSummary:
    def test_valid_first_verification(self):
        """A valid report shows what will be added"""
        summary = verification(indigo_username="Forum Name").summary(make_registry())

        assert "| Model | Shelly Pro 2 (`shelly-pro-2`) |" in summary
        assert "| Verifier | GitHub `tester`, Indigo forum `Forum Name` |" in summary
        assert "| Credited by name | Yes |" in summary
        assert "| Firmware | `1.4.4` |" in summary
        assert "| Plugin version | `1.5.0` |" in summary
        assert "This will be the first verification of this model." in summary

    def test_missing_firmware(self):
        """A report without firmware says so instead of showing an empty version"""
        summary = verification(firmware="_No response_").summary(make_registry())

        assert "| Firmware | Not given |" in summary

    def test_already_verified(self):
        """The maintainer can see a model already has verifications"""
        summary = verification(model="Shelly Plus 1").summary(make_registry())

        assert "This model has already been verified 1 time(s)." in summary

    def test_on_behalf_credits_forum_only(self):
        """Reports filed for a forum user only credit the forum user"""
        summary = verification(indigo_username="Forum Name", on_behalf=True).summary(
            make_registry()
        )

        assert "| Verifier | Indigo forum `Forum Name` |" in summary

    def test_anonymous(self):
        """Anonymous reports show who's recorded, and that they won't be credited by name"""
        summary = verification(credit=False).summary(make_registry())

        assert "| Verifier | GitHub `tester` |" in summary
        assert "| Credited by name | No (anonymous) |" in summary

    def test_errors_listed(self):
        """Invalid reports list the problems instead of a summary"""
        summary = verification(tested="_No response_").summary(make_registry())

        assert summary.startswith("This verification report can't be added yet:")
        assert "- Please describe what you tested." in summary
        assert "| Model |" not in summary


class TestMarkdownText:
    @pytest.mark.parametrize(
        ("text", "escaped"),
        [
            ("Forum Name", "Forum Name"),
            ("snake_case", r"snake\_case"),
            ("*bold*", r"\*bold\*"),
            ("[link]", r"\[link\]"),
            ("back\\slash", r"back\\slash"),
            ("`code`", r"\`code\`"),
        ],
    )
    def test_escapes(self, text, escaped):
        """Names can't turn into emphasis, links, or code in the docs table"""
        assert device_verification.markdown_text(text) == escaped


class TestVerifierCredit:
    def test_github_and_forum(self):
        """Both usernames link to their profiles, with the forum name in parentheses"""
        entry = make_entry(github_username="tester", indigo_username="Forum Name")

        assert device_verification.verifier_credit(entry) == (
            "[tester](https://github.com/tester) "
            "([Forum Name](https://forums.indigodomo.com/memberlist.php?mode=viewprofile&un=Forum+Name))"
        )

    def test_github_only(self):
        """Without a forum username, only the GitHub profile is linked"""
        entry = make_entry(github_username="tester")

        assert device_verification.verifier_credit(entry) == (
            "[tester](https://github.com/tester)"
        )

    def test_forum_only(self):
        """Forum users filed for by someone else are linked to their forum profile"""
        entry = make_entry(indigo_username="Forum Name")

        assert device_verification.verifier_credit(entry) == (
            "[Forum Name](https://forums.indigodomo.com/memberlist.php?mode=viewprofile&un=Forum+Name)"
        )

    def test_forum_name_escaped(self):
        """Forum names are escaped in the link text and encoded in the URL"""
        entry = make_entry(indigo_username="a_b & c")

        assert device_verification.verifier_credit(entry) == (
            r"[a\_b & c](https://forums.indigodomo.com/memberlist.php?mode=viewprofile&un=a_b+%26+c)"
        )


class TestVerificationTable:
    def rows(self, registry):
        """The table's rows, without the header and divider."""
        return device_verification.verification_table(registry).split("\n")[2:]

    def test_header(self):
        """The table has model, status, and verifier columns"""
        table = device_verification.verification_table({})

        assert table == "| Model | Status | Verified by |\n| --- | --- | --- |"

    def test_sorted_by_name(self):
        """Models are listed alphabetically, not in registry order"""
        rows = self.rows(make_registry())

        assert rows[0].startswith("| Shelly Plus 1 |")
        assert rows[1].startswith("| Shelly Pro 2 |")

    def test_unverified(self):
        """Unverified models link to the verification form titled with the model"""
        registry = {"shelly-blu-ht": {"name": "Shelly BLU H&T", "verified_by": []}}

        assert self.rows(registry) == [
            (
                "| Shelly BLU H&T | :warning: Not yet verified | [Report it]("
                "https://github.com/AaronLionsheep/ShellyNGMQTT/issues/new?template=device-verification.yml"
                "&title=Verify+Shelly+BLU+H%26T) |"
            )
        ]

    def test_verified(self):
        """Verified models credit each verifier, in the order they verified"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [
                    make_entry(github_username="first"),
                    make_entry(github_username="second"),
                ],
            }
        }

        assert self.rows(registry) == [
            (
                "| Shelly Pro 2 | :white_check_mark: Verified | [first](https://github.com/first), "
                "[second](https://github.com/second) |"
            )
        ]

    def test_anonymous_counted(self):
        """Anonymous verifiers are counted after the named ones, never named"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [
                    make_entry(github_username="named"),
                    make_entry(github_username="hidden", anonymous=True),
                    make_entry(github_username="also-hidden", anonymous=True),
                ],
            }
        }

        (row,) = self.rows(registry)

        assert row.endswith("[named](https://github.com/named) and 2 anonymous |")
        assert "hidden" not in row

    def test_only_anonymous(self):
        """A model verified only anonymously is still verified"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [make_entry(github_username="hidden", anonymous=True)],
            }
        }

        assert self.rows(registry) == [
            "| Shelly Pro 2 | :white_check_mark: Verified | 1 anonymous |"
        ]

    def test_three_verifiers_not_collapsed(self):
        """Up to three verifiers are listed inline, which keeps the row short"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [make_entry(github_username=f"u{i}") for i in range(3)],
            }
        }

        (row,) = self.rows(registry)

        assert "<details>" not in row
        assert row.count("https://github.com/") == 3

    def test_many_verifiers_collapsed(self):
        """Long lists collapse to a count that expands to one verifier per line"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [
                    make_entry(github_username="first"),
                    make_entry(github_username="second"),
                    make_entry(github_username="third"),
                    make_entry(github_username="fourth"),
                ],
            }
        }

        assert self.rows(registry) == [
            (
                "| Shelly Pro 2 | :white_check_mark: Verified | "
                "<details><summary>4 verifiers</summary>"
                "[first](https://github.com/first)<br>[second](https://github.com/second)<br>"
                "[third](https://github.com/third)<br>[fourth](https://github.com/fourth)"
                "</details> |"
            )
        ]

    def test_collapsed_count_includes_anonymous(self):
        """Anonymous verifiers count toward collapsing and are summed on the last line"""
        registry = {
            "shelly-pro-2": {
                "name": "Shelly Pro 2",
                "verified_by": [
                    make_entry(github_username="named"),
                    *[
                        make_entry(github_username=f"hidden{i}", anonymous=True)
                        for i in range(3)
                    ],
                ],
            }
        }

        (row,) = self.rows(registry)

        assert "<summary>4 verifiers</summary>" in row
        assert row.endswith(
            "[named](https://github.com/named)<br>3 anonymous</details> |"
        )
        assert "hidden" not in row


class TestWithVerificationTable:
    def page(self, table=""):
        """A docs page with the generated table between its markers."""
        return (
            f"# Title\n\n{device_verification.DOCS_START}{table}"
            f"{device_verification.DOCS_END}\nAfter\n"
        )

    def test_inserts_table(self):
        """The table goes between the markers, with blank lines so it renders as a table"""
        table = device_verification.verification_table(make_registry())

        assert device_verification.with_verification_table(
            self.page(), make_registry()
        ) == self.page(f"\n\n{table}\n\n")

    def test_replaces_table(self):
        """Regenerating replaces the old table instead of adding another"""
        once = device_verification.with_verification_table(self.page(), {})

        twice = device_verification.with_verification_table(once, make_registry())

        assert twice == device_verification.with_verification_table(
            self.page(), make_registry()
        )

    @pytest.mark.parametrize(
        "page", ["# No markers\n", f"{device_verification.DOCS_START}\n"]
    )
    def test_missing_markers(self, page):
        """A page without both markers raises instead of being overwritten"""
        with pytest.raises(ValueError):
            device_verification.with_verification_table(page, {})


def test_docs_up_to_date():
    """The docs table matches verified_devices.json, so hand edits to either are caught"""
    registry = json.loads(device_verification.REGISTRY.read_text())
    docs = device_verification.DOCS.read_text()

    assert device_verification.with_verification_table(docs, registry) == docs, (
        "Run: python3 scripts/device_verification.py --docs"
    )


class TestMain:
    @pytest.fixture
    def registry_file(self, tmp_path, monkeypatch):
        """A registry file the script reads and writes instead of the plugin's"""
        path = tmp_path / "verified_devices.json"
        path.write_text(json.dumps(make_registry()))
        monkeypatch.setattr(device_verification, "REGISTRY", path)
        return path

    @pytest.fixture(autouse=True)
    def docs_file(self, tmp_path, monkeypatch):
        """A docs page the script writes instead of the real one"""
        path = tmp_path / "supported-devices.md"
        path.write_text(
            f"# Page\n{device_verification.DOCS_START}\n"
            f"{device_verification.DOCS_END}\n"
        )
        monkeypatch.setattr(device_verification, "DOCS", path)
        return path

    @pytest.fixture
    def output(self, tmp_path, monkeypatch):
        """The GITHUB_OUTPUT file the workflow reads step outputs from"""
        path = tmp_path / "output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(path))
        return path

    @pytest.fixture
    def issue(self, monkeypatch):
        """Set the issue environment variables the workflow passes in"""

        def _issue(**fields):
            monkeypatch.setenv("ISSUE_BODY", issue_body(**fields))
            monkeypatch.setenv("ISSUE_AUTHOR", "tester")
            monkeypatch.setenv("ISSUE_NUMBER", "42")

        return _issue

    def test_valid(self, registry_file, docs_file, output, issue, capsys):
        """Valid reports print the summary, update the registry and docs, and output the model"""
        issue()

        assert device_verification.main(["script"]) == 0
        assert "| Model | Shelly Pro 2 (`shelly-pro-2`) |" in capsys.readouterr().out
        registry = json.loads(registry_file.read_text())
        assert registry["shelly-pro-2"]["verified_by"][0]["github_username"] == "tester"
        assert (
            "| Shelly Pro 2 | :white_check_mark: Verified | [tester]"
            in docs_file.read_text()
        )
        assert output.read_text() == "valid=true\nmodel=Shelly Pro 2\n"

    def test_summary_counts_earlier_verifications(
        self, registry_file, output, issue, capsys
    ):
        """The summary describes the registry before this report is added"""
        issue()

        device_verification.main(["script"])

        assert "first verification" in capsys.readouterr().out

    def test_invalid(self, registry_file, docs_file, output, issue, capsys):
        """Invalid reports print the problems and leave the registry and docs unchanged"""
        docs = docs_file.read_text()
        issue(tested="_No response_")

        assert device_verification.main(["script"]) == 0
        assert "Please describe what you tested." in capsys.readouterr().out
        assert json.loads(registry_file.read_text()) == make_registry()
        assert docs_file.read_text() == docs
        assert output.read_text() == "valid=false\n"

    def test_keeps_unicode_and_format(self, registry_file, issue, monkeypatch):
        """The registry stays readable, with a trailing newline and unescaped names"""
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        issue(indigo_username="Jürgen")

        assert device_verification.main(["script"]) == 0
        text = registry_file.read_text()
        assert '"indigo_username": "Jürgen"' in text
        assert text.endswith("}\n")
        assert text.startswith('{\n  "shelly-pro-2"')

    def test_docs_only(self, registry_file, docs_file, monkeypatch):
        """--docs regenerates the table from the registry without an issue"""
        monkeypatch.delenv("ISSUE_BODY", raising=False)

        assert device_verification.main(["script", "--docs"]) == 0
        assert (
            "| Shelly Plus 1 | :white_check_mark: Verified |" in docs_file.read_text()
        )
        assert json.loads(registry_file.read_text()) == make_registry()
