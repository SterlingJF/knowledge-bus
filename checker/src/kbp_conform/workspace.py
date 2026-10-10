"""The settings file of a Knowledge Bus folder: `.knowledge-bus/workspace.yaml`.

`from_parent` names universe specs of the parent folder. Every command adds each
named universe spec, with its guidance from the parent folder, beside the
folder's own universe specs. docs/knowledge-bus-directory.md describes the rules
for nested folders.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from ._vendor import yaml
from .explorer import InspectionError, _nearest_scope, scope_documents

FILE = "workspace.yaml"
KEYS = ("from_parent",)
HEADERS = ("universe", "guidance", "marks")
LINKS = {"universe": "id", "guidance": "guides", "marks": "marks_for"}


@dataclass(frozen=True)
class Named:
    """The ids in `from_parent`, and the parent folder's files to read for those ids."""

    scope: Path
    parent: Path | None
    ids: tuple
    files: tuple

    @property
    def where(self):
        """The parent folder, relative to the folder holding `scope`."""
        return parent_label(self.scope, self.parent)


def is_target(path):
    """True for an existing workspace.yaml file inside a .knowledge-bus/ folder."""
    path = Path(path).resolve()
    return path.name == FILE and path.parent.name == ".knowledge-bus" and path.is_file()


def parent_scope(scope):
    """The nearest .knowledge-bus/ above the folder holding `scope`, or None."""
    holder = Path(scope).parent
    return None if holder.parent == holder else _nearest_scope(holder.parent)


def parent_label(scope, parent):
    return os.path.relpath(parent, Path(scope).parent) + "/"


def problem(document, own_ids, parent_ids):
    """The first problem in a workspace.yaml, as (message, candidates), or None.

    `parent_ids` is None when no .knowledge-bus/ is above the folder.
    """
    if not isinstance(document, dict):
        return f"{FILE}: must be a mapping", None
    unknown = sorted(str(key) for key in document if key not in KEYS)
    if unknown:
        return f"{FILE}: unknown key {unknown[0]!r}; the only key is from_parent", None
    named = document.get("from_parent", [])
    if not _id_list(named):
        return (
            f"{FILE}: from_parent must be a list of universe spec ids, each named once",
            None,
        )
    if named and parent_ids is None:
        return (
            (
                f"{FILE}: from_parent names universe specs, "
                "but no .knowledge-bus/ is above this folder"
            ),
            None,
        )
    for name in named:
        if name not in parent_ids:
            declared = sorted(parent_ids)
            return (
                (
                    f"{FILE}: from_parent names {name!r}, which the parent folder "
                    "does not declare; the parent folder declares "
                    f"{declared or 'no universe spec'}"
                ),
                declared,
            )
        if name in own_ids:
            return (
                f"{FILE}: from_parent names {name!r}, which this folder already declares",
                None,
            )
    return None


def misplaced(kind, document, named_ids):
    """The refusal for nested guidance or marks naming a universe spec from the parent folder, or None."""
    if kind not in ("guidance", "marks"):
        return None
    target = _linked(kind, document)
    if target is None or target not in named_ids:
        return None
    return (
        f"{LINKS[kind]} {target!r}, a universe spec from the parent folder; "
        f"move the {kind} to the parent folder"
    )


def _id_list(named):
    return (
        isinstance(named, list)
        and all(isinstance(name, str) and name for name in named)
        and len(set(named)) == len(named)
    )


def _linked(kind, document):
    header = document.get(kind)
    value = header.get(LINKS[kind]) if isinstance(header, dict) else None
    return value if isinstance(value, str) else None


def _own_ids(scope):
    """Universe spec ids declared in `scope`. Unreadable files fail in their own checks."""
    ids = []
    for path in scope_documents(scope):
        if not path.name.endswith(".kbp.yaml"):
            continue
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError, UnicodeDecodeError, yaml.YAMLError:
            continue
        if isinstance(document, dict) and "universe" in document:
            ids.append(_linked("universe", document))
    return [identity for identity in ids if identity]


def _parent_documents(parent, where, marks):
    """Every definition file in the parent folder, as (path, kind, document).

    Raises InspectionError for an unreadable file, naming the file and the parent folder.
    """
    loaded = []
    for path in scope_documents(parent):
        if not marks and not path.name.endswith(".kbp.yaml"):
            continue
        place = f"{path.name} in the parent folder {where}"
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
            raise InspectionError(
                "conformance", f"Cannot parse {place}: {error}"
            ) from error
        if not isinstance(document, dict):
            raise InspectionError("conformance", f"{place}: document must be a mapping")
        kinds = [kind for kind in HEADERS if kind in document]
        if len(kinds) != 1:
            raise InspectionError(
                "conformance",
                f"{place}: expected exactly one universe, guidance, or marks header",
            )
        loaded.append((path, kinds[0], document))
    return loaded


def read(scope, *, marks=False):
    """Check `scope`'s workspace.yaml; return a Named, or None when the file is absent.

    The parent folder is read only when `from_parent` names a universe spec.
    With marks=True, the parent folder's marks files are read too.
    Raises InspectionError with the first refusal.
    """
    scope = Path(scope)
    if not (scope / FILE).is_file():
        return None
    try:
        document = yaml.safe_load((scope / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise InspectionError(
            "conformance", f"{FILE}: must be a mapping; cannot parse the file: {error}"
        ) from error
    parent = parent_scope(scope)
    reads_parent = (
        parent is not None
        and isinstance(document, dict)
        and not set(document) - set(KEYS)
        and _id_list(document.get("from_parent"))
        and bool(document.get("from_parent"))
    )
    parent_files = (
        _parent_documents(parent, parent_label(scope, parent), marks)
        if reads_parent
        else []
    )
    parent_ids = (
        None
        if parent is None
        else [
            _linked(kind, loaded)
            for _, kind, loaded in parent_files
            if kind == "universe" and _linked(kind, loaded)
        ]
    )
    found = problem(document, _own_ids(scope), parent_ids)
    if found:
        raise InspectionError("conformance", found[0], candidates=found[1])
    ids = tuple(document.get("from_parent", []))
    files = tuple(
        sorted(
            path for path, kind, loaded in parent_files if _linked(kind, loaded) in ids
        )
    )
    return Named(scope, parent, ids, files)
