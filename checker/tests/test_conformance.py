"""The conformance corpus.

Every document under `conformance/pass/` must conform. Every document under
`conformance/fail/` must be refused, and refused for its own reason — asserting
on the exit status alone would pass a checker that rejects everything.

Each failing document carries exactly one defect, named by its filename, and
the expected message fragment is registered below. A new refusal the checker
learns to make earns a file here; a refusal nobody has written a file for is a
refusal nobody has tested.
"""

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol" / "knowledge-bus-protocol.yaml"
CORPUS = ROOT / "protocol" / "conformance"

# filename stem -> the fragment the refusal must contain
EXPECTED = {
    "conflicting-composition-strength": "conflicts with composition list",
    "shared-feeds-order": "ordered must be True under its shared contract",
    "shared-distinction-order": "ordered must be False under its shared contract",
    "faceted-predicate-without-facet": "faceted predicate must name facets",
    "duplicate-composition-member": "duplicate composition member",
    "invalid-composition-strength": "strength 'banana' not in",
    "unknown-predicate-value": "unknown predicate value 'banana'",
    "unknown-predicate-facet": "unknown facet 'banana'",
    "unresolved-element": "composition refs unknown elements",
    "universe-predicate-names-factor": "may not be referenced by a universe",
    "element-missing-required": "missing required",
    "duplicate-code": "already carried by",
    "wrong-conforms-to": "does not match",
    "ordered-self-loop-missing-legality": "relation the-question->the-question (informs) is on a cycle and declares no legality",
    "ordered-cycle-missing-legality": "relation the-record->another-question (informs) is on a cycle and declares no legality",
    "relation-missing-required": "missing required ['to']",
}


def run(*paths):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "kbp_conform.cli",
            "--validate",
            str(PROTOCOL),
            *map(str, paths),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def ids(directory):
    return sorted(p.name for p in (CORPUS / directory).glob("*.kbp.yaml"))


@pytest.mark.parametrize("name", ids("pass"))
def test_conforms(name):
    result = run(CORPUS / "pass" / name)
    assert result.returncode == 0, result.stdout
    assert "CONFORMS" in result.stdout


@pytest.mark.parametrize("name", ids("fail"))
def test_refused(name):
    stem = name.removesuffix(".kbp.yaml")
    assert stem in EXPECTED, f"{name} has no registered reason in EXPECTED"
    result = run(CORPUS / "fail" / name)
    assert result.returncode != 0, f"{name} was accepted\n{result.stdout}"
    assert EXPECTED[stem] in result.stdout, (
        f"{name} was refused for the wrong reason\n{result.stdout}"
    )


def test_shipped_documents_conform():
    result = run(ROOT / "universes")
    assert result.returncode == 0, result.stdout
    assert "NON-CONFORMING" not in result.stdout


def test_protocol_is_sound():
    result = subprocess.run(
        [sys.executable, "-m", "kbp_conform.cli", "--self-check", str(PROTOCOL)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "SOUND" in result.stdout
