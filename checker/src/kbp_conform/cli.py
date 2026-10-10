"""Command line for the type checker.

    kbp [--validate] [<protocol.yaml>] [<document-or-directory>...]
    kbp --self-check [<protocol.yaml>]
    kbp --version
    kbp --mint element|artifact|frame|factor [count] [<document-or-directory>...]
    kbp --card <kind> [<scope or files>] [--universe <id>] [--format json|markdown]
    kbp --kinds [<scope or files>] [--universe <id>] [--format json|markdown]

`--validate` checks documents against the protocol and is what a bare `kbp`
does. `--self-check` checks the protocol against itself and stops there.
`--mint` returns codes that collide with nothing the documents declare.
`--card` prints the card for one document type. `--kinds` lists every document type.
Both take the same targets as `--inspect` and skip marks files.

Without targets, use the nearest ancestor's .knowledge-bus/ directory.
Explicit targets take precedence. The implementation checkout retains its bundled
universes/ default when no .knowledge-bus/ directory exists. Protocol discovery is independent
of the working directory; installed packages carry their own protocol.

A folder's .knowledge-bus/workspace.yaml can name universe specs of the parent
folder under `from_parent`. Commands that read a whole .knowledge-bus/ add the
named universe specs beside the folder's own universe specs. For an explicit
workspace.yaml target, check and `--mint` apply the rules for a folder target;
the other commands skip the file.
"""

import json
import os
import sys
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

from ._vendor import yaml
from .checker import (
    CODE_PREFIX,
    CODED,
    accepted_versions,
    check,
    check_guidance,
    mint,
    self_check,
)

KNOWLEDGE_BUS_DIR = ".knowledge-bus"
PROTOCOL_NAME = "knowledge-bus-protocol.yaml"
PACKAGE_DIR = Path(__file__).resolve().parent
CHECKOUT_ROOT = PACKAGE_DIR.parent.parent.parent


def find_knowledge_bus_dir(start=None):
    """Find the nearest .knowledge-bus/ directory, including calls from inside it."""
    here = Path(start or os.getcwd()).resolve()
    for candidate in (here, *here.parents):
        if candidate.name == KNOWLEDGE_BUS_DIR and candidate.is_dir():
            return candidate
        knowledge_bus_dir = candidate / KNOWLEDGE_BUS_DIR
        if knowledge_bus_dir.is_dir():
            return knowledge_bus_dir
    return None


def default_protocol():
    """Use the installed resource, or the canonical file in a source checkout."""
    for path in (
        PACKAGE_DIR / PROTOCOL_NAME,
        CHECKOUT_ROOT / "protocol" / PROTOCOL_NAME,
    ):
        if path.is_file():
            return str(path)
    return None


def expand(paths):
    """Expand explicit targets without absorbing nested folders with their own .knowledge-bus/."""
    from . import workspace

    out = []
    for raw in paths:
        path = Path(raw).resolve()
        if not path.exists():
            raise ValueError(f"target does not exist: {path}")
        if path.is_file():
            if not workspace.is_target(path):
                out.append(str(path))
            continue
        knowledge_bus_dir = (
            path if path.name == KNOWLEDGE_BUS_DIR else path / KNOWLEDGE_BUS_DIR
        )
        if knowledge_bus_dir.is_dir():
            out.extend(
                str(p)
                for p in sorted(knowledge_bus_dir.glob("*.kbp.yaml"))
                if p.is_file()
            )
            continue
        for directory, children, files in os.walk(path):
            children[:] = [
                name
                for name in children
                if name != KNOWLEDGE_BUS_DIR
                and not (Path(directory) / name / KNOWLEDGE_BUS_DIR).is_dir()
                and not (Path(directory) / name).is_symlink()
            ]
            out.extend(
                str(Path(directory) / name)
                for name in files
                if name.endswith(".kbp.yaml")
            )
    return sorted(set(out))


def resolve(args, *, documents_required=True):
    """Return the protocol, selected documents, and an actionable discovery error.

    The documents include the parent folder's files listed in each workspace.yaml.
    """
    protocol, documents, error, workspaces = _resolve(
        args, documents_required=documents_required
    )
    refusal = next(
        (str(found) for _, found in workspaces if isinstance(found, Exception)), None
    )
    return protocol, documents, error or refusal


def _resolve(args, *, documents_required=True):
    """As resolve, plus (scope, workspace.Named or the refusal) per workspace.yaml read."""
    from . import workspace

    args = list(args)
    protocol = None
    if (
        args
        and args[0].endswith((".yaml", ".yml"))
        and os.path.isfile(args[0])
        and not workspace.is_target(args[0])
    ):
        with open(args[0], encoding="utf-8") as stream:
            head = yaml.safe_load(stream) or {}
        if isinstance(head, dict) and "protocol" in head:
            protocol = args.pop(0)

    protocol = protocol or default_protocol()
    if protocol is None:
        return (
            None,
            [],
            "no bundled protocol found; pass the protocol file explicitly",
            [],
        )
    if not documents_required:
        return protocol, [], None, []

    if not args:
        knowledge_bus_dir = find_knowledge_bus_dir()
        if knowledge_bus_dir is not None:
            args = [str(knowledge_bus_dir)]
        elif (
            (CHECKOUT_ROOT / "protocol" / PROTOCOL_NAME).is_file()
            and Path.cwd().resolve().is_relative_to(CHECKOUT_ROOT)
            and (CHECKOUT_ROOT / "universes").is_dir()
        ):
            args = [str(CHECKOUT_ROOT / "universes")]
        else:
            return (
                protocol,
                [],
                (
                    f"no {KNOWLEDGE_BUS_DIR}/ found from {Path.cwd()} upward; "
                    "choose a folder with Knowledge Bus definitions or pass explicit files. "
                    "Checking does not initialize a folder."
                ),
                [],
            )
    try:
        documents = expand(args)
    except ValueError as error:
        return protocol, [], str(error), []
    workspaces = _workspaces(args)
    for _, found in workspaces:
        if not isinstance(found, Exception):
            documents += [
                str(path) for path in found.files if str(path) not in documents
            ]
    return protocol, documents, None, workspaces


def _workspaces(args):
    """Read workspace.yaml for each folder target and each .knowledge-bus/ target.

    Read each explicit workspace.yaml target after the folder targets, and add no
    files from the parent folder for that target.
    """
    from . import explorer, workspace

    found = []
    for raw in sorted(args, key=workspace.is_target):
        path = Path(raw).resolve()
        explicit = workspace.is_target(path)
        if explicit:
            scope = path.parent
        elif path.is_dir():
            scope = path if path.name == KNOWLEDGE_BUS_DIR else path / KNOWLEDGE_BUS_DIR
        else:
            continue
        if not scope.is_dir() or scope in (seen for seen, _ in found):
            continue
        try:
            named = workspace.read(scope)
        except explorer.InspectionError as error:
            found.append((scope, error))
            continue
        if named is not None:
            found.append((scope, replace(named, files=()) if explicit else named))
    return found


MODES = (
    "--validate",
    "--self-check",
    "--mint",
    "--inspect",
    "--explore",
    "--card",
    "--kinds",
)
FORMATS = ("json", "markdown")


def _option(arguments, name, *, required=False):
    found = [index for index, value in enumerate(arguments) if value == name]
    if len(found) > 1:
        raise ValueError(f"{name} may be supplied once")
    if not found:
        if required:
            raise ValueError(f"{name} is required")
        return None
    index = found[0]
    if index + 1 >= len(arguments) or arguments[index + 1].startswith("--"):
        raise ValueError(f"{name} requires a value")
    value = arguments[index + 1]
    del arguments[index : index + 2]
    return value


def _explorer_mode(mode, argv):
    from . import artifact, explorer

    try:
        universe_id = _option(argv, "--universe")
        output = _option(argv, "--output", required=mode == "--explore")
        replace = "--replace" in argv
        if argv.count("--replace") > 1:
            raise ValueError("--replace may be supplied once")
        argv = [value for value in argv if value != "--replace"]
        unknown = next((value for value in argv if value.startswith("--")), None)
        if unknown:
            raise ValueError(f"unknown option {unknown}")
        paths, file_selection, named = explorer.resolve_selection(argv)
        if not paths:
            raise explorer.InspectionError(
                "selection", "No Knowledge Bus definitions in the selected scope"
            )
        if universe_id and file_selection and universe_id != file_selection:
            raise explorer.InspectionError(
                "selection", "The explicit universe id conflicts with the selected file"
            )
        protocol = default_protocol()
        if protocol is None:
            raise explorer.InspectionError("protocol", "No bundled protocol found")
        model = explorer.inspect_paths(
            protocol,
            paths,
            universe_id=universe_id or file_selection,
            release_version=version("knowledge-bus"),
            named=named,
        )
        if mode == "--inspect":
            print(json.dumps(model, ensure_ascii=False, sort_keys=True))
        else:
            receipt = artifact.generate(model, output, replace=replace)
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0
    except explorer.InspectionError as error:
        print(
            json.dumps(error.as_dict(), ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
    except (artifact.ArtifactError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema": "knowledge-bus/explorer-error/1",
                    "status": "error",
                    "category": "generation" if mode == "--explore" else "selection",
                    "message": str(error),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
    return 1


def _card_mode(mode, argv):
    from . import card, explorer

    try:
        try:
            universe_id = _option(argv, "--universe")
            output_format = _option(argv, "--format") or "json"
        except ValueError as error:
            raise explorer.InspectionError("selection", str(error)) from error
        if output_format not in FORMATS:
            raise explorer.InspectionError(
                "selection", f"--format is one of {', '.join(FORMATS)}"
            )
        unknown = next((value for value in argv if value.startswith("--")), None)
        if unknown:
            raise explorer.InspectionError("selection", f"unknown option {unknown}")
        kind = None
        if mode == "--card":
            if not argv:
                raise explorer.InspectionError(
                    "selection", "--card requires a document type id"
                )
            kind = argv.pop(0)
        paths, file_selection, named = explorer.resolve_selection(argv, marks=False)
        if not paths:
            raise explorer.InspectionError(
                "selection", "No Knowledge Bus definitions in the selected scope"
            )
        if universe_id and file_selection and universe_id != file_selection:
            raise explorer.InspectionError(
                "selection",
                "The explicit universe spec id conflicts with the selected file",
            )
        protocol = default_protocol()
        if protocol is None:
            raise explorer.InspectionError("protocol", "No bundled protocol found")
        chosen = universe_id or file_selection
        listed = _universe_ids(paths, named) if mode == "--kinds" and not chosen else []
        if len(listed) > 1:
            result = card.build_kinds_set(
                [
                    card.build_kinds(
                        *explorer.load_selection(
                            protocol, paths, universe_id=each, marks=False, named=named
                        )[1:3]
                    )
                    for each in listed
                ],
                named.ids if named else (),
            )
            render = card.render_kinds_set
        else:
            _, universe, guidance, _ = explorer.load_selection(
                protocol, paths, universe_id=chosen, marks=False, named=named
            )
            if mode == "--kinds":
                result = card.build_kinds(universe, guidance)
                render = card.render_kinds
            else:
                kinds = card.kind_ids(universe)
                if kind not in kinds:
                    raise explorer.InspectionError(
                        "selection",
                        f"No document type {kind!r} in universe spec {universe['universe']['id']!r}",
                        candidates=kinds,
                    )
                parents = named.ids if named else ()
                own_id = universe["universe"]["id"]
                others = [
                    (
                        *explorer.load_selection(
                            protocol, paths, universe_id=each, marks=False, named=named
                        )[1:3],
                        each in parents,
                    )
                    for each in _universe_ids(paths, named)
                    if each != own_id
                ]
                result = card.build_card(
                    universe, guidance, kind, others, from_parent=own_id in parents
                )
                render = card.render_card
        if output_format == "markdown":
            sys.stdout.write(render(result))
        else:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except OSError as error:
        failure = explorer.InspectionError("selection", str(error))
    except explorer.InspectionError as error:
        failure = error
    print(
        json.dumps(failure.as_dict(), ensure_ascii=False, sort_keys=True),
        file=sys.stderr,
    )
    return 1


def _universe_ids(paths, named):
    """Universe spec ids in the selection: the folder's own ids, sorted, then the ids from `from_parent`."""
    from . import explorer, workspace

    parent_files = set(named.files) if named else set()
    files = [
        path
        for path in paths
        if not str(path).endswith(".explorer.yaml") and not workspace.is_target(path)
    ]
    own = []
    for path, (_, kind, document) in zip(files, explorer._loaded_documents(files)):
        header = document[kind]
        if kind == "universe" and Path(path) not in parent_files:
            own.append(header.get("id") if isinstance(header, dict) else None)
    if not all(isinstance(identity, str) for identity in own):
        return []
    return [*sorted(own), *(named.ids if named else ())]


def main(argv=()):
    argv = list(argv)
    if argv == ["--version"]:
        protocol_path = default_protocol()
        if protocol_path is None:
            print("no bundled protocol found")
            return 1
        with open(protocol_path, encoding="utf-8") as stream:
            protocol = yaml.safe_load(stream)["protocol"]
        print(f"Knowledge Bus {version('knowledge-bus')}")
        print(f"Bundled protocol: {protocol['id']}/{protocol['version']}")
        return 0
    mode = argv.pop(0) if argv and argv[0] in MODES else "--validate"

    if mode in ("--inspect", "--explore"):
        return _explorer_mode(mode, argv)
    if mode in ("--card", "--kinds"):
        return _card_mode(mode, argv)

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

    protocol_path, doc_paths, err, workspaces = _resolve(
        argv, documents_required=not self_only
    )
    if err:
        print(err)
        return 1

    with open(protocol_path, encoding="utf-8") as stream:
        protocol = yaml.safe_load(stream)

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

    accepted = accepted_versions(protocol)
    expected = accepted[0]
    refusal = f"does not match '{expected}'" + (
        f" or an accepted earlier version {accepted[1:]}" if accepted[1:] else ""
    )
    from . import workspace

    types = protocol["declarations"]["document_types"]["kinds"]
    refused = any(isinstance(found, Exception) for _, found in workspaces)
    if not doc_paths and not refused and not any(map(workspace.is_target, argv)):
        print("no documents to check")
        return 1

    ok = True
    for _, found in workspaces:
        ok = _check_workspace(found) and ok
    named_by_scope = {
        scope: found.ids
        for scope, found in workspaces
        if not isinstance(found, Exception)
    }
    from_parent = {
        str(path)
        for _, found in workspaces
        if not isinstance(found, Exception)
        for path in found.files
    }
    docs = []
    for path in doc_paths:
        with open(path, encoding="utf-8") as stream:
            doc = yaml.safe_load(stream)
        header = (
            next((k for k in types if k in doc), None)
            if isinstance(doc, dict)
            else None
        )
        docs.append((path, os.path.basename(path), header, doc))

    def heading(path, name, declared):
        against = declared if declared in accepted else expected
        if path in from_parent:
            return f"=== {name} from the parent folder, against {against} ==="
        return f"=== {name} against {against} ==="

    universes, universe_names = {}, {}
    for path, name, header, doc in docs:
        if header != "universe":
            continue
        declared = doc["universe"].get("conforms_to", "")
        print(heading(path, name, declared))
        if declared not in accepted:
            print(f"  FAIL  conforms_to '{declared}' {refusal}\n")
            ok = False
            continue
        universe_id = doc["universe"].get("id")
        if universe_id in universes:
            print(
                f"  FAIL  duplicate universe id '{universe_id}' also declared by "
                f"{universe_names[universe_id]}\n"
            )
            ok = False
        else:
            universes[universe_id] = doc
            universe_names[universe_id] = name
        ok = check(protocol, doc, name) and ok
        print()

    for path, name, header, doc in docs:
        if header == "universe":
            continue
        declared = doc[header].get("conforms_to", "") if header else ""
        print(heading(path, name, declared))
        if header is None:
            print(
                f"  FAIL  no top-level header key from {types}; document type unknown\n"
            )
            ok = False
            continue
        if declared not in accepted:
            print(f"  FAIL  conforms_to '{declared}' {refusal}\n")
            ok = False
            continue
        misplaced = (
            None
            if path in from_parent
            else workspace.misplaced(
                header, doc, named_by_scope.get(Path(path).parent, ())
            )
        )
        if misplaced:
            print(f"\n{name}: NON-CONFORMING\n  FAIL  {misplaced}\n")
            ok = False
            continue
        ok = check_guidance(protocol, doc, universes, name) and ok
        print()

    return 0 if ok else 1


def _check_workspace(found):
    """Print the check block for one workspace.yaml, in the same format as the block for a definition file."""
    from . import workspace

    print(f"=== {workspace.FILE} ===")
    if isinstance(found, Exception):
        print(f"\n{workspace.FILE}: NON-CONFORMING\n  FAIL  {found}\n")
        return False
    if found.ids:
        print(f"  names {', '.join(found.ids)} from {found.where}")
    else:
        print("  names no universe spec from the parent folder")
    print(f"\n{workspace.FILE}: CONFORMS\n")
    return True


def run():
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
