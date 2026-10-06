"""Documentation claims about the evals that a test can settle."""

import inspect
import re
from pathlib import Path

import adapters
import spec

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_no_document_claims_a_trace_check():
    """The eval spec has no trace check, so no recipe or table may say it checks traces."""
    justfile = read("justfile")
    comment = justfile.split("evals-check:")[0].rstrip().splitlines()[-1]
    assert "trace" not in comment.lower()
    row = next(
        line
        for line in read("evals/README.md").splitlines()
        if "`just evals-check`" in line
    )
    assert "trace" not in row.lower()


def test_judge_docs_name_only_the_vendors_that_are_wired_in():
    """The default judges are all Claude models, and the docs say so."""
    defaults = list(inspect.signature(adapters.Judge).parameters["models"].default)
    assert defaults and all(model.startswith("claude-") for model in defaults)
    assert len(defaults) == 2
    for relative in ("README.md", "evals/README.md"):
        text = read(relative)
        assert "different families" not in text, relative
        assert "two Claude models" in text, relative


def test_skills_scenarios_are_not_described_as_real_sessions():
    """The scenarios are constructed, as evals/skills.yaml says."""
    assert "replays a real session" not in read("evals/README.md")
    assert "is modelled on a session" in read("evals/README.md")


def test_contributing_does_not_claim_evidence_lives_in_evals():
    assert (
        "evidence" not in read("CONTRIBUTING.md").split("`evals/`")[1].splitlines()[0]
    )


def test_validation_guide_counts_the_failing_conformance_cases():
    cases = list((ROOT / "protocol/conformance/fail").glob("*.kbp.yaml"))
    match = re.search(r"(\d+) deliberately invalid cases", read("docs/validation.md"))
    assert match, "docs/validation.md states how many invalid cases the corpus holds"
    assert int(match.group(1)) == len(cases)


def test_the_readme_says_which_evals_files_name_no_vendor():
    """Run records name sides and models by design; the spec, fixtures, situations and
    retired fails do not."""
    text = read("evals/README.md")
    assert "The data files name no tool or vendor." not in text
    assert "Run records name sides and models by design" in text
    for retired in sorted((ROOT / "evals/retired").glob("*.yaml")):
        assert not spec.VENDORS.search(retired.read_text()), retired.name


def test_the_runbook_says_a_run_on_the_wrong_side_is_refused():
    """report.py refuses a run whose models belong to the other side's company."""
    runbook = read("evals/README.md").split("## Running on another vendor")[1]
    runbook = runbook.split("\n## ")[0]
    assert "is not `codex:<model>`" in runbook
    assert "Jev serves both" in runbook


def test_the_runbook_gives_both_packet_commands_with_their_required_flags():
    text = read("evals/README.md")
    build = text[text.index("packet.py build") :].split("```", 1)[0]
    apply = text[text.index("packet.py apply") :].split("```", 1)[0]
    assert "--anthropic-run" in build and "--out" in build
    assert "--anthropic-run" in apply and "--replies" in apply and "--effort" in apply
