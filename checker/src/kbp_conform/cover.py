"""Which universe specs cover one file, from already-loaded folders and presets.

The answer narrows by folder, then path, then document type, then hat. It takes
documents that are already loaded and opens no files.
docs/universe-spec-coverage.md describes the rule, and
checker/tests/cover/cases.json holds the cases any other code must also pass.
"""

COVER_SCHEMA = "knowledge-bus/cover/1"
ERROR_SCHEMA = "knowledge-bus/inspection-error/1"
COVERAGE_VERSION = 1
COVERAGE_KEYS = ("version", "from_parent", "paths")
KNOWLEDGE_BUS_DIR = ".knowledge-bus"
PLAIN_PATH = (
    "write a folder ending in / or an exact file, relative to the folder holding "
    ".knowledge-bus/, with no wildcards"
)


class CoverError(ValueError):
    """A refusal shaped like the other inspection errors."""

    def __init__(self, category, message, candidates=None):
        super().__init__(message)
        self.category = category
        self.candidates = sorted(candidates or [])

    def as_dict(self):
        result = {
            "schema": ERROR_SCHEMA,
            "status": "error",
            "category": self.category,
            "message": str(self),
        }
        if self.candidates:
            result["candidates"] = self.candidates
        return result


def words(text):
    """Lower-case words: letters and digits; every other character separates words."""
    return "".join(c if c.isalnum() else " " for c in str(text).lower()).split()


def _header(spec):
    return spec["universe"]


def spec_id(spec):
    return _header(spec)["id"]


def document_type_ids(spec):
    return [
        artifact["id"]
        for artifact in spec.get("artifacts") or []
        if isinstance(artifact, dict) and isinstance(artifact.get("id"), str)
    ]


def _hat_texts(spec):
    overview = _header(spec).get("overview")
    if isinstance(overview, dict) and overview.get("for") is not None:
        yield overview["for"]
    for artifact in spec.get("artifacts") or []:
        enablement = artifact.get("enablement") if isinstance(artifact, dict) else None
        if isinstance(enablement, dict) and enablement.get("actor") is not None:
            yield enablement["actor"]
    for frame in spec.get("frames") or []:
        for value in (frame.get("values") if isinstance(frame, dict) else None) or []:
            yield value.get("id", "") if isinstance(value, dict) else value


def names_hat(spec, hat):
    """True when the hat's words appear, in order and side by side, in one text."""
    wanted = words(hat)
    size = len(wanted)
    for text in _hat_texts(spec):
        found = words(text)
        if any(found[i : i + size] == wanted for i in range(len(found) - size + 1)):
            return True
    return False


def _summary(spec, reasons):
    header = _header(spec)
    overview = header.get("overview")
    covers = overview.get("covers") if isinstance(overview, dict) else None
    version = header.get("version")
    return {
        "id": header["id"],
        "label": header.get("label") or header["id"].replace("-", " ").capitalize(),
        "version": None if version is None else str(version),
        "covers": None if covers is None else str(covers).strip(),
        "reasons": reasons,
    }


def _ids(specs):
    ids = []
    for spec in specs:
        header = spec.get("universe") if isinstance(spec, dict) else None
        if not isinstance(header, dict) or not isinstance(header.get("id"), str):
            raise CoverError("conformance", "A universe spec has no id")
        ids.append(header["id"])
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise CoverError(
            "conformance", f"Duplicate universe id values: {', '.join(duplicates)}"
        )
    return ids


def _plain_path(path):
    if not isinstance(path, str) or not path or path.startswith("/"):
        return False
    if any(c in path for c in "*?\\"):
        return False
    parts = path.removesuffix("/").split("/")
    return all(part not in ("", ".", "..") for part in parts)


def coverage_problem(coverage, own_ids, parent_ids):
    """The first problem in a coverage.yaml, as (message, candidates), or None.

    `parent_ids` is None when no .knowledge-bus/ is above the folder.
    """
    if not isinstance(coverage, dict):
        return "coverage.yaml: must be a mapping", None
    if "version" not in coverage:
        return "coverage.yaml: version is required; write version: 1", None
    version = coverage["version"]
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        return (
            "coverage.yaml: version must be a whole number; this checker reads version 1",
            None,
        )
    if version > COVERAGE_VERSION:
        return (
            (
                f"coverage.yaml: version {version} needs a newer checker; "
                f"this checker reads version {COVERAGE_VERSION}"
            ),
            None,
        )
    unknown = sorted(str(key) for key in coverage if key not in COVERAGE_KEYS)
    if unknown:
        return (
            (
                f"coverage.yaml: unknown key {unknown[0]!r}; "
                "version 1 allows from_parent and paths"
            ),
            None,
        )
    named = coverage.get("from_parent", [])
    if (
        not isinstance(named, list)
        or not all(isinstance(name, str) and name for name in named)
        or len(set(named)) != len(named)
    ):
        return (
            "coverage.yaml: from_parent must be a list of universe spec ids, each named once",
            None,
        )
    if named and parent_ids is None:
        return (
            (
                "coverage.yaml: from_parent names universe specs, "
                "but no .knowledge-bus/ is above this folder"
            ),
            None,
        )
    for name in named:
        if name not in parent_ids:
            return (
                (
                    f"coverage.yaml: from_parent names {name!r}, "
                    "which the parent folder does not have"
                ),
                parent_ids,
            )
        if name in own_ids:
            return (
                f"coverage.yaml: from_parent names {name!r}, which this folder already has",
                None,
            )
    paths = coverage.get("paths", {})
    if not isinstance(paths, dict) or not all(
        isinstance(key, str) and isinstance(value, list) for key, value in paths.items()
    ):
        return (
            "coverage.yaml: paths must map universe spec ids to lists of paths",
            None,
        )
    available = sorted([*own_ids, *named])
    for key in sorted(paths):
        if key not in available:
            return (
                (
                    f"coverage.yaml: paths names {key!r}, "
                    "which is not a universe spec in this folder"
                ),
                available,
            )
        listed = paths[key]
        for path in listed:
            if not _plain_path(path):
                return (
                    f"coverage.yaml: {path!r} under {key} is not a plain path: {PLAIN_PATH}",
                    None,
                )
        if listed != sorted(set(listed)):
            return (
                f"coverage.yaml: paths for {key} must be sorted, each path once",
                None,
            )
    return None


def _under(path, folder):
    """True when the slash-separated `path` is `folder` or inside it ("" is the root)."""
    return not folder or path == folder or path.startswith(folder + "/")


def _folder_of(path):
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _depth(folder):
    return len(folder.split("/")) if folder else 0


def _listed(paths, relative):
    return any(
        relative.startswith(entry) if entry.endswith("/") else relative == entry
        for entry in paths
    )


def _from_folders(file, on_path):
    governing = on_path[-1]
    parent = on_path[-2] if len(on_path) > 1 else None
    own = list(governing.get("universe_specs") or [])
    own_ids = _ids(own)
    folder = _folder_of(file)
    knowledge_bus_dir = "../" * (_depth(folder) - _depth(governing["at"]))
    knowledge_bus_dir += KNOWLEDGE_BUS_DIR

    named, paths, parent_specs = [], {}, []
    if "coverage" in governing:
        coverage = governing["coverage"]
        # The parent is read only when from_parent names universe specs.
        wanted = coverage.get("from_parent") if isinstance(coverage, dict) else None
        if parent and isinstance(wanted, list) and wanted:
            parent_specs = list(parent.get("universe_specs") or [])
        parent_ids = None if parent is None else _ids(parent_specs)
        problem = coverage_problem(coverage, own_ids, parent_ids)
        if problem:
            raise CoverError("conformance", problem[0], problem[1])
        named, paths = coverage.get("from_parent", []), coverage.get("paths", {})
    candidates = [(spec, ["in-folder"]) for spec in own] + [
        (spec, ["named-by-nested-folder"])
        for spec in parent_specs
        if spec_id(spec) in named
    ]
    if not candidates:
        raise CoverError(
            "selection",
            f"No universe specs in {knowledge_bus_dir}, "
            "and none named from the parent folder",
        )

    relative = file[len(governing["at"]) + 1 :] if governing["at"] else file
    kept = [
        (spec, reasons + ["listed-path"])
        if spec_id(spec) in paths and _listed(paths[spec_id(spec)], relative)
        else (spec, reasons)
        for spec, reasons in candidates
        if spec_id(spec) not in paths or _listed(paths[spec_id(spec)], relative)
    ]
    return (kept or candidates), knowledge_bus_dir


def cover(
    file, folders, presets, *, top="", document_type=None, no_fit=False, hat=None
):
    """Return the answer for `file`, or raise CoverError.

    `file`, `top` and each folder's `at` are slash-separated paths from one root;
    `at` is the folder holding that .knowledge-bus/ ("" for the root). Each folder
    is {"at", "universe_specs": [loaded universe specs], "coverage": loaded
    coverage.yaml}; leave out "coverage" when the folder has no coverage.yaml. An
    empty coverage.yaml loads as None and is refused. `presets` are loaded
    universe specs.
    """
    if document_type == "":
        raise CoverError("selection", "--type needs a document type id")
    if document_type and no_fit:
        raise CoverError("selection", "--type and --no-fit cannot be given together")
    if hat is not None and not words(hat):
        raise CoverError("selection", "--hat needs at least one word")
    if not _under(file, top):
        raise CoverError("selection", "The file is outside the top folder")

    folder = _folder_of(file)
    on_path = sorted(
        (f for f in folders if _under(f["at"], top) and _under(folder, f["at"])),
        key=lambda f: _depth(f["at"]),
    )
    if on_path:
        source = "folder"
        candidates, knowledge_bus_dir = _from_folders(file, on_path)
    else:
        source, knowledge_bus_dir = "presets", None
        _ids(presets)
        candidates = [(spec, ["preset"]) for spec in presets]

    if document_type:
        declaring = [
            (spec, reasons + ["declares-document-type"])
            for spec, reasons in candidates
            if document_type in document_type_ids(spec)
        ]
        if not declaring:
            raise CoverError(
                "selection",
                f"No candidate universe spec declares document type {document_type!r}",
                sorted(
                    {kind for spec, _ in candidates for kind in document_type_ids(spec)}
                ),
            )
        candidates = declaring

    if hat is not None and len(candidates) > 1:
        naming = [
            (spec, reasons + ["names-hat"])
            for spec, reasons in candidates
            if names_hat(spec, hat)
        ]
        candidates = naming or candidates

    candidates = sorted(candidates, key=lambda item: spec_id(item[0]))
    return {
        "schema": COVER_SCHEMA,
        "settled": len(candidates) == 1 or bool(document_type) or bool(no_fit),
        "source": source,
        "knowledge_bus_dir": knowledge_bus_dir,
        "document_type": document_type,
        "no_fit": bool(no_fit),
        "hat": hat,
        "universe_specs": [_summary(spec, reasons) for spec, reasons in candidates],
    }
