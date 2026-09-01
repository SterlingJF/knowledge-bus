"""Command line for the type checker.

    kbp [--validate] [<protocol.yaml>] [<document-or-directory>...]
    kbp --self-check [<protocol.yaml>]
    kbp --mint element|artifact|frame|factor [count] [<document-or-directory>...]

`--validate` checks documents against the protocol and is what a bare `kbp`
does. `--self-check` checks the protocol against itself and stops there.
`--mint` returns codes that collide with nothing the documents declare.

Paths are arguments. Given none, the protocol and the universes are found by
walking up from the working directory for a `spec/` directory — so a bare run
inside the repository does the obvious thing, and a run anywhere else says what
it could not find rather than checking nothing and reporting success.

A directory argument contributes every `*.kbp.yaml` beneath it. A file argument
contributes itself, whatever its name.
"""
import os
import sys
import glob

import yaml

from .checker import (
    CODE_PREFIX, CODED,
    check, check_guidance, mint, self_check,
)

SPEC_DIR = "spec"
PROTOCOL_NAME = "knowledge-bus-protocol.yaml"
UNIVERSE_DIR = "universes"


def find_root(start=None):
    """The nearest ancestor holding `spec/`, or None."""
    here = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(here, SPEC_DIR)):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def default_protocol(root):
    named = os.path.join(root, SPEC_DIR, PROTOCOL_NAME)
    if os.path.exists(named):
        return named
    found = sorted(glob.glob(os.path.join(root, SPEC_DIR, "*.yaml")))
    return found[0] if found else None


def expand(paths):
    """File arguments as themselves; directory arguments as the documents in them."""
    out = []
    for p in paths:
        if os.path.isdir(p):
            out.extend(glob.glob(os.path.join(p, "**", "*.kbp.yaml"), recursive=True))
        else:
            out.append(p)
    return sorted(set(out))


def resolve(args):
    """(protocol path, document paths, error message)."""
    args = list(args)
    protocol = None
    if args and args[0].endswith((".yaml", ".yml")) and os.path.isfile(args[0]):
        head = yaml.safe_load(open(args[0], encoding="utf-8")) or {}
        if "protocol" in head:
            protocol = args.pop(0)

    if protocol is None:
        root = find_root()
        if root is None:
            return None, [], (
                f"no protocol given and no `{SPEC_DIR}/` directory above "
                f"{os.getcwd()} — pass the protocol as the first argument"
            )
        protocol = default_protocol(root)
        if protocol is None:
            return None, [], f"no protocol document in {os.path.join(root, SPEC_DIR)}"
        if not args:
            args = [os.path.join(root, UNIVERSE_DIR)]

    return protocol, expand(args), None


MODES = ("--validate", "--self-check", "--mint")


def main(argv=()):
    argv = list(argv)
    mode = argv.pop(0) if argv and argv[0] in MODES else "--validate"

    unknown = next((a for a in argv if a.startswith("--")), None)
    if unknown:
        print(f"unknown option {unknown}\nusage: kbp [{' | '.join(MODES)}] ...")
        return 1

    if mode == "--mint":
        kind = argv[0] if argv else ""
        usage = f"usage: kbp --mint {'|'.join(CODED)} [count]"
        if kind not in CODE_PREFIX:
            print(usage)
            return 1
        try:
            count = int(argv[1]) if len(argv) > 1 else 1
        except ValueError:
            print(usage)
            return 1
        _, docs, err = resolve(argv[2:])
        if err:
            print(err)
            return 1
        for code in mint(kind, count, docs):
            print(code)
        return 0

    self_only = mode == "--self-check"

    protocol_path, doc_paths, err = resolve(argv)
    if err:
        print(err)
        return 1

    protocol = yaml.safe_load(open(protocol_path, encoding="utf-8"))

    # the protocol first, and fatally: a verdict computed against an unsound
    # protocol is not unreliable, it is misleading
    pname = os.path.basename(protocol_path)
    print(f"=== {pname} against itself ===")
    unsound = self_check(protocol)
    for f_ in unsound:
        print(f"  FAIL  {f_}")
    print()
    print(f"{pname}: {'UNSOUND' if unsound else 'SOUND'}")
    print()
    if unsound or self_only:
        return 1 if unsound else 0

    expected = f"{protocol['protocol']['id']}/{protocol['protocol']['version']}"
    types = protocol["declarations"]["document_types"]["kinds"]
    if not doc_paths:
        print("no documents to check")
        return 1

    docs = []
    for path in doc_paths:
        doc = yaml.safe_load(open(path, encoding="utf-8"))
        header = next((k for k in types if k in doc), None) if isinstance(doc, dict) else None
        docs.append((os.path.basename(path), header, doc))

    ok, universes = True, {}
    for name, header, doc in docs:
        if header != "universe":
            continue
        print(f"=== {name} against {expected} ===")
        declared = doc["universe"].get("conforms_to", "")
        if declared != expected:
            print(f"  FAIL  conforms_to '{declared}' does not match '{expected}'\n")
            ok = False
            continue
        universes[doc["universe"].get("id")] = doc
        ok = check(protocol, doc, name) and ok
        print()

    for name, header, doc in docs:
        if header == "universe":
            continue
        print(f"=== {name} against {expected} ===")
        if header is None:
            print(f"  FAIL  no top-level header key from {types}; document type unknown\n")
            ok = False
            continue
        declared = doc[header].get("conforms_to", "")
        if declared != expected:
            print(f"  FAIL  conforms_to '{declared}' does not match '{expected}'\n")
            ok = False
            continue
        ok = check_guidance(protocol, doc, universes, name) and ok
        print()

    return 0 if ok else 1


def run():
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
