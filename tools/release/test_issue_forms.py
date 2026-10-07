"""GitHub issue forms keep the keys GitHub needs to show them."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FORMS = ROOT / ".github/ISSUE_TEMPLATE"
INPUTS = {"input", "textarea", "dropdown", "checkboxes"}


def forms():
    return sorted(path for path in FORMS.glob("*.yml") if path.name != "config.yml")


def test_every_path_has_a_form():
    assert [path.stem for path in forms()] == [
        "bug",
        "eval-or-model",
        "proposal",
        "universe",
    ]


@pytest.mark.parametrize("path", forms(), ids=lambda path: path.name)
def test_form_has_required_keys_and_valid_elements(path):
    form = yaml.safe_load(path.read_text())
    assert isinstance(form["name"], str) and form["name"]
    assert isinstance(form["description"], str) and form["description"]
    assert isinstance(form["body"], list) and form["body"]
    ids = []
    for element in form["body"]:
        kind = element["type"]
        attributes = element["attributes"]
        if kind == "markdown":
            assert attributes["value"].strip()
            continue
        assert kind in INPUTS
        assert attributes["label"]
        ids.append(element["id"])
        if kind == "dropdown":
            assert attributes["options"]
            assert len(set(attributes["options"])) == len(attributes["options"])
        if kind == "checkboxes":
            assert all(option["label"] for option in attributes["options"])
    assert any(
        element.get("validations", {}).get("required") for element in form["body"]
    )
    assert len(ids) == len(set(ids))


def test_config_links_to_contributing():
    config = yaml.safe_load((FORMS / "config.yml").read_text())
    assert config["blank_issues_enabled"] is True
    (link,) = config["contact_links"]
    assert link["name"] and link["about"]
    assert link["url"].endswith("/CONTRIBUTING.md")
