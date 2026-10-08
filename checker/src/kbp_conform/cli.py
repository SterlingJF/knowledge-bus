"""Command line for the type checker.

    kbp [--validate] [<protocol.yaml>] [<document-or-directory>...]
    kbp --self-check [<protocol.yaml>]
    kbp --version
    kbp --mint element|artifact|frame|factor [count] [<document-or-directory>...]
    kbp --card <kind> [<scope or files>] [--universe <id>] [--format json|markdown]
    kbp --kinds [<scope or files>] [--universe <id>] [--format json|markdown]
    kbp --cover <file> [--type <document type id> | --no-fit] [--hat <name>]

`--validate` checks documents against the protocol and is what a bare `kbp`
does. `--self-check` checks the protocol against itself and stops there.
`--mint` returns codes that collide with nothing the documents declare.
`--card` prints the card for one document type. `--kinds` lists every document type.
Both take the same targets as `--inspect` and skip marks files. They also see
the universe specs a nested folder's coverage.yaml names from its parent, and
use the preset when no .knowledge-bus/ is found. `--cover` says which universe
specs cover one file.

Without targets, use the nearest ancestor's .knowledge-bus/ directory.
Explicit targets take precedence. The implementation checkout retains its bundled
universes/ default when no .knowledge-bus/ directory exists. Protocol discovery is independent
of the working directory; installed packages carry their own protocol.
"""

import json
import os
import sys
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
PRESET = "product-development"
PRESET_FILES = ("universe.kbp.yaml", "type-guidance.kbp.yaml")
COVERAGE_FILE = "coverage.yaml"
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


def default_preset():
    """The preset's files: the installed copy, or the source in a checkout."""
    for folder in (
        PACKAGE_DIR / "presets" / PRESET,
        CHECKOUT_ROOT / "universes" / PRESET,
    ):
        if all((folder / name).is_file() for name in PRESET_FILES):
            return [str(folder / name) for name in PRESET_FILES]
    return []


def expand(paths):
    """Expand explicit targets without absorbing nested folders with their own .knowledge-bus/."""
    out = []
    for raw in paths:
        path = Path(raw).resolve()
        if not path.exists():
            raise ValueError(f"target does not exist: {path}")
        if path.is_file():
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
    """Return the protocol, selected documents, and an actionable discovery error."""
    return _resolve(args, documents_required=documents_required)[:3]


def _resolve(args, *, documents_required=True):
    """As resolve, plus each selected .knowledge-bus/ directory."""
    args = list(args)
    protocol = None
    if args and args[0].endswith((".yaml", ".yml")) and os.path.isfile(args[0]):
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
    scopes = []
    for raw in args:
        path = Path(raw).resolve()
        scope = path if path.name == KNOWLEDGE_BUS_DIR else path / KNOWLEDGE_BUS_DIR
        if scope.is_dir() and scope not in scopes:
            scopes.append(scope)
    return protocol, documents, None, scopes


MODES = (
    "--validate",
    "--self-check",
    "--mint",
    "--inspect",
    "--explore",
    "--card",
    "--kinds",
    "--cover",
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
        paths, file_selection = explorer.resolve_inspection_targets(argv)
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
        paths, file_selection = explorer.resolve_card_targets(
            argv, preset=default_preset()
        )
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
        _, universe, guidance, _ = explorer.load_selection(
            protocol, paths, universe_id=universe_id or file_selection, marks=False
        )
        if mode == "--kinds":
            result = card.build_kinds(universe)
            render = card.render_kinds
        else:
            kinds = card.kind_ids(universe)
            if kind not in kinds:
                raise explorer.InspectionError(
                    "selection",
                    f"No document type {kind!r} in universe spec {universe['universe']['id']!r}",
                    candidates=kinds,
                )
            result = card.build_card(universe, guidance, kind)
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


def _cover_folder(scope, anchor, explorer, *, nearest):
    """One .knowledge-bus/ as the rule takes it; only the nearest one's coverage.yaml counts."""
    at = scope.parent.relative_to(anchor).as_posix()
    folder = {
        "at": "" if at == "." else at,
        "universe_specs": [
            document
            for _, kind, document in explorer._definitions(scope)
            if kind == "universe"
        ],
    }
    if nearest and (scope / COVERAGE_FILE).is_file():
        folder["coverage"] = explorer.read_coverage(scope)
    return folder


def _names_from_parent(coverage):
    named = coverage.get("from_parent") if isinstance(coverage, dict) else None
    return isinstance(named, list) and bool(named)


def _cover_mode(argv):
    from . import cover, explorer

    try:
        try:
            document_type = _option(argv, "--type")
            hat = _option(argv, "--hat")
        except ValueError as error:
            raise explorer.InspectionError("selection", str(error)) from error
        if argv.count("--no-fit") > 1:
            raise explorer.InspectionError("selection", "--no-fit may be supplied once")
        no_fit = "--no-fit" in argv
        argv = [value for value in argv if value != "--no-fit"]
        unknown = next((value for value in argv if value.startswith("--")), None)
        if unknown:
            raise explorer.InspectionError("selection", f"unknown option {unknown}")
        if len(argv) != 1:
            raise explorer.InspectionError("selection", "--cover requires one file")
        file = Path(argv[0]).resolve()
        if file.is_dir():
            raise explorer.InspectionError(
                "selection", "--cover needs a file; a folder was given"
            )
        if KNOWLEDGE_BUS_DIR in file.parts:
            raise explorer.InspectionError(
                "selection", "--cover does not take files inside .knowledge-bus/"
            )
        scopes = []
        for folder in file.parents:
            if (folder / KNOWLEDGE_BUS_DIR).is_dir():
                scopes.append(folder / KNOWLEDGE_BUS_DIR)
            if len(scopes) == 2:
                break
        anchor = Path(file.anchor)
        folders = []
        if scopes:
            folders.append(_cover_folder(scopes[0], anchor, explorer, nearest=True))
        # The parent is read only when the nearest coverage.yaml names universe specs from it.
        if len(scopes) == 2 and _names_from_parent(folders[0].get("coverage")):
            folders.insert(0, _cover_folder(scopes[1], anchor, explorer, nearest=False))
        presets = []
        if not scopes:
            preset = default_preset()
            if not preset:
                raise explorer.InspectionError("selection", "No bundled preset found")
            presets = [
                document
                for _, kind, document in explorer._loaded_documents(preset)
                if kind == "universe"
            ]
        answer = cover.cover(
            file.relative_to(anchor).as_posix(),
            folders,
            presets,
            document_type=document_type,
            no_fit=no_fit,
            hat=hat,
        )
        print(json.dumps(answer, ensure_ascii=False, sort_keys=True))
        return 0
    except OSError as error:
        failure = explorer.InspectionError(
            "selection", f"Cannot read a {KNOWLEDGE_BUS_DIR}/ folder: {error.strerror}"
        )
    except (cover.CoverError, explorer.InspectionError) as error:
        failure = error
    print(
        json.dumps(failure.as_dict(), ensure_ascii=False, sort_keys=True),
        file=sys.stderr,
    )
    return 1


def _check_coverage(scope):
    """Check one .knowledge-bus/coverage.yaml; print the result as the checker does."""
    from . import explorer

    print(f"=== {COVERAGE_FILE} ===")
    try:
        explorer.named_from_parent(scope)
    except (OSError, explorer.InspectionError) as error:
        print(f"  FAIL  {error}")
        candidates = getattr(error, "candidates", None)
        if candidates:
            print(f"        candidates: {', '.join(candidates)}")
        print(f"{COVERAGE_FILE}: NON-CONFORMING\n")
        return False
    print(f"{COVERAGE_FILE}: CONFORMS\n")
    return True


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
    if mode == "--cover":
        return _cover_mode(argv)

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

    protocol_path, doc_paths, err, scopes = _resolve(
        argv, documents_required=not self_only
    )
    scopes = [scope for scope in scopes if (scope / COVERAGE_FILE).is_file()]
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
    types = protocol["declarations"]["document_types"]["kinds"]
    if not doc_paths and not any(_counts_as_documents(scope) for scope in scopes):
        print("no documents to check")
        return 1

    docs = []
    for path in doc_paths:
        with open(path, encoding="utf-8") as stream:
            doc = yaml.safe_load(stream)
        header = (
            next((k for k in types if k in doc), None)
            if isinstance(doc, dict)
            else None
        )
        docs.append((os.path.basename(path), header, doc))

    ok, universes, universe_names = True, {}, {}
    for name, header, doc in docs:
        if header != "universe":
            continue
        declared = doc["universe"].get("conforms_to", "")
        print(
            f"=== {name} against {declared if declared in accepted else expected} ==="
        )
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

    for name, header, doc in docs:
        if header == "universe":
            continue
        declared = doc[header].get("conforms_to", "") if header else ""
        print(
            f"=== {name} against {declared if declared in accepted else expected} ==="
        )
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
        ok = check_guidance(protocol, doc, universes, name) and ok
        print()

    for scope in scopes:
        ok = _check_coverage(scope) and ok

    return 0 if ok else 1


def _counts_as_documents(scope):
    """False for a coverage.yaml that conforms and names nothing from the parent."""
    from . import explorer

    try:
        return bool(explorer.named_from_parent(scope))
    except OSError, explorer.InspectionError:
        return True


def run():
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
