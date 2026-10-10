"""Fetch the code-repository corpus from GitHub.

The corpus is every public repository the account has starred with at least
`--min-stars` stars, or every repository in a list file such as
`fixtures/corpus-2026-10-08.jsonl`. The script calls `gh api` one request at a
time, reads public data only, and stops with exit code 3 on a rate limit. A
rerun skips files already on disk, so a stopped run picks up at the first
missing file.

Stages, in order:

- stars: the account's starred repositories, or the repositories in the list
  file (`stars-all.jsonl`, `run-info.json`). A listed repository keeps the
  stars, language, kind and first-pass flag from the list. The script makes
  one call per repository for the default branch, the archived and fork flags
  and the licence.
- repos: per repository, the listings of the root, `.github/` and `docs/`; the
  README; the latest 10 releases; the latest 30 commits; the latest 10 closed
  pull requests (`repos/`, `readmes/`).
- files: documents matched by the file patterns, saved in full or as a head,
  plus the second-level listing of `docs/` (`files/`, `manifest.json`).
- trees: the recursive file tree, reduced to document paths, workflow names and
  top-level folders (`trees/`).
- pr-titles: for the newest release with 3 or more list lines that cite a pull
  request, up to 5 cited pull requests and their titles (`of2-prtitles.json`).
- commits-100: the latest 100 commits for repositories with Conventional
  Commits subjects in half or more of the stored commits (`commits-100.json`).
- reads: the files listed in a picks file from `corpus_sample.py` (`reads/`,
  `reads-index.json`). Runs only with `--picks`.

Usage:

    python3 tools/research/corpus_fetch.py --account NAME --min-stars 3000 --out DIR
    python3 tools/research/corpus_fetch.py \\
        --repos tools/research/fixtures/corpus-2026-10-08.jsonl --out DIR
    python3 tools/research/corpus_fetch.py --out DIR --stage reads --picks PICKS
"""

import argparse
import base64
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

STAGES = ("stars", "repos", "files", "trees", "pr-titles", "commits-100", "reads")

# Names of files and folders that explain, govern or record a repository,
# matched at the root, in `.github/` and in `docs/`. Unchanged since 2026-10-03,
# so file counts stay comparable across runs.
PATTERNS = {
    "readme": r"^readme(\.|$)",
    "contributing": r"^contributing(\.|$)",
    "security": r"^security(\.|$)",
    "changelog": r"^(changelog|changes|history|news)(\.|$)",
    "code_of_conduct": r"^code[_-]of[_-]conduct(\.|$)",
    "governance": r"^governance(\.|$)",
    "support": r"^support(\.|$)",
    "maintainers": r"^(maintainers|owners)(\.|$)",
    "credits": r"^(authors|contributors|credits)(\.|$)",
    "codeowners": r"^codeowners$",
    "citation": r"^citation\.cff$",
    "funding": r"^funding\.ya?ml$",
    "roadmap": r"^roadmap(\.|$)",
    "architecture": r"^architecture(\.|$)",
    "design_doc": r"^design(\.|$)",
    "license": r"^(license|licence|copying)(\.|$)",
    "agents": r"^(agents|claude|copilot-instructions)\.md$",
    "upgrade_guide": r"^(upgrad|migrat)\w*\.(md|rst|adoc|txt)$",
    "threat_model": r"^threat[_-]?model",
    "stability_policy": r"^(stability|versioning|support[_-]policy|deprecation)\w*(\.|$)",
    "docs_dir": r"^(docs?|documentation|website|site)$",
    "decisions_dir": r"^(adr|adrs|decisions|rfcs?|proposals|design-docs|enhancements|keps)$",
    "examples_dir": r"^(examples?|samples|demos?|cookbook)$",
    "issue_templates": r"^issue_template(\.md|$)",
    "pr_template": r"^pull_request_template(\.md)?$",
    "workflows_dir": r"^workflows$",
    "dependency_bot": r"^(dependabot\.ya?ml|renovate\.json5?|\.renovaterc(\.json)?)$",
    "devcontainer": r"^\.devcontainer$",
}
CONVENTIONAL = re.compile(
    r"^(feat|fix|docs|chore|refactor|perf|test|build|ci|style|revert)(\([^)]*\))?!?: "
)
LOCATIONS = ("/", ".github/", "docs/")

# Pattern keys saved in full, up to FULL_CAP characters.
FULL = {
    "contributing",
    "security",
    "code_of_conduct",
    "pr_template",
    "support",
    "governance",
    "maintainers",
    "roadmap",
    "architecture",
    "design_doc",
    "citation",
    "funding",
    "threat_model",
    "stability_policy",
    "upgrade_guide",
    "codeowners",
    "issue_templates",
}
# Pattern keys saved as a head of the given length.
HEAD = {"license": 1500, "changelog": 6000}
FULL_CAP = 150_000
AGENT_NAMES = re.compile(
    r"^(agents?|claude|gemini|qwen|codex|copilot-instructions|conventions|\.?cursorrules"
    r"|\.windsurfrules|\.clinerules|\.cursor|\.claude|\.agents?|\.gemini|\.codex"
    r"|\.windsurf|\.aider.*|\.github-copilot|instructions|skills)(\.|$)",
    re.IGNORECASE,
)
TREE_DOCS = re.compile(r"\.(md|mdx|markdown|rst|adoc|txt)$", re.IGNORECASE)
TREE_SKIP = re.compile(
    r"(^|/)(node_modules|vendor|third_party|testdata|fixtures|__snapshots__|\.git)/",
    re.IGNORECASE,
)
LIST_LINE = re.compile(r"^\s*([-*+]|\d+\.)\s+(.*)$")
PR_REFERENCE = re.compile(r"(?:\(#(\d+)\)|(?:/pull/|(?<![\w/])#)(\d+))")
PR_TITLES = "of2-prtitles.json"
COMMITS_100 = "commits-100.json"


class RateLimited(SystemExit):
    """Raised on a rate-limit reply. The run exits with status 3 and keeps the saved files."""


class GitHub:
    """Runs `gh api` one call at a time and counts the calls."""

    def __init__(self):
        self.gh = shutil.which("gh")
        if not self.gh:
            sys.exit(
                "gh is not on PATH. Install the GitHub CLI and run `gh auth login`."
            )
        self.calls = 0

    def run(self, *args):
        self.calls += 1
        done = subprocess.run(
            [self.gh, "api", *args], capture_output=True, text=True, check=False
        )
        err = done.stderr.lower()
        if done.returncode and (
            "rate limit" in err or "secondary" in err or "http 429" in err
        ):
            sys.stderr.write(f"Rate limit on {args[-1]}; stopping.\n")
            raise RateLimited(3)
        return done

    def json(self, path):
        done = self.run(path)
        if done.returncode:
            return None
        try:
            return json.loads(done.stdout)
        except ValueError:
            return None

    def raw(self, full, path):
        done = self.run(
            "-H",
            "Accept: application/vnd.github.raw",
            f"repos/{full}/contents/{quote(path)}",
        )
        return None if done.returncode else done.stdout


def slug(full):
    return full.replace("/", "__")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def corpus(out, min_stars):
    """Corpus repositories from the star list, most stars first."""
    stars = [json.loads(line) for line in (out / "stars-all.jsonl").open()]
    return sorted(
        (r for r in stars if r["stars"] >= min_stars), key=lambda r: -r["stars"]
    )


def star_row(repo, starred_at=None):
    """One corpus row from a `repos/{name}` or star-list item."""
    return {
        "full_name": repo["full_name"],
        "name": repo["full_name"].split("/", 1)[1],
        "stars": repo.get("stargazers_count"),
        "description": repo.get("description"),
        "topics": repo.get("topics") or [],
        "language": repo.get("language"),
        "license": (repo.get("license") or {}).get("spdx_id"),
        "created_at": repo.get("created_at"),
        "pushed_at": repo.get("pushed_at"),
        "archived": repo.get("archived"),
        "fork": repo.get("fork"),
        "starred_at": starred_at,
        "default_branch": repo.get("default_branch"),
    }


def write_rows(target, rows):
    with target.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# Fields a list file sets for each repository, in place of the live values.
LISTED_FIELDS = ("stars", "language", "kind", "first_pass")


def stage_listed(gh, out, repos_file, min_stars):
    """Corpus rows from a list file, with the list's stars kept at freeze values."""
    target = out / "stars-all.jsonl"
    if target.exists():
        return
    fetched = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    lines = Path(repos_file).read_text().splitlines()
    rows = []
    for item in (json.loads(line) for line in lines if line.strip()):
        repo = gh.json(f"repos/{item['full_name']}")
        if not repo:
            sys.stderr.write(f"{item['full_name']}: not found; kept in the list.\n")
            repo = {}
        row = star_row({**repo, "full_name": item["full_name"]})
        row.update({k: item[k] for k in LISTED_FIELDS if k in item})
        rows.append(row)
    write_rows(target, rows)
    write_json(
        out / "run-info.json",
        {
            "fetch_date_utc": fetched.isoformat().replace("+00:00", "Z"),
            "repos_file": Path(repos_file).name,
            "min_stars": min_stars,
            "listed": len(rows),
            "corpus": sum(r["stars"] >= min_stars for r in rows),
        },
    )


def stage_stars(gh, out, account, min_stars):
    target = out / "stars-all.jsonl"
    if target.exists():
        return
    fetched = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    done = gh.run(
        "--paginate",
        "-H",
        "Accept: application/vnd.github.star+json",
        "--jq",
        ".[]",
        f"users/{account}/starred?per_page=100",
    )
    if done.returncode:
        sys.exit("gh api failed on the star list: " + done.stderr[:300])
    rows = []
    for line in done.stdout.splitlines():
        item = json.loads(line)
        rows.append(star_row(item["repo"], item.get("starred_at")))
    write_rows(target, rows)
    write_json(
        out / "run-info.json",
        {
            "freeze_date_utc": fetched.isoformat().replace("+00:00", "Z"),
            "min_stars": min_stars,
            "starred": len(rows),
            "corpus": sum(r["stars"] >= min_stars for r in rows),
        },
    )


def file_hits(where, names):
    hits = {}
    for key, pattern in PATTERNS.items():
        match = [n for n in names if re.search(pattern, n, re.IGNORECASE)]
        if match:
            hits[key] = [f"{'' if where == '/' else where}{n}" for n in match]
    return hits


def stage_repos(gh, out, repos):
    (out / "repos").mkdir(exist_ok=True)
    (out / "readmes").mkdir(exist_ok=True)
    for repo in repos:
        full = repo["full_name"]
        target = out / "repos" / f"{slug(full)}.json"
        if target.exists():
            continue
        record = {**repo, "files": {}, "listing": {}}
        for where in LOCATIONS:
            raw = gh.json(f"repos/{full}/contents/{'' if where == '/' else where}")
            entries = [
                [i["name"], i.get("type")] for i in raw or [] if isinstance(i, dict)
            ]
            record["listing"][where] = entries
            for key, paths in file_hits(where, [n for n, _ in entries]).items():
                record["files"].setdefault(key, []).extend(paths)
        readme = gh.json(f"repos/{full}/readme")
        if readme and readme.get("content"):
            text = base64.b64decode(readme["content"]).decode("utf-8", "replace")
            (out / "readmes" / f"{slug(full)}.md").write_text(text)
            record["readme"] = {
                "path": readme.get("path"),
                "bytes": len(text.encode()),
                "headings": [
                    h.strip() for h in re.findall(r"(?m)^#{1,3}\s+(.+?)\s*#*$", text)
                ],
            }
        releases = [
            r
            for r in gh.json(f"repos/{full}/releases?per_page=10") or []
            if isinstance(r, dict)
        ]
        record["releases"] = {
            "count_sampled": len(releases),
            "bodies_chars": [len(r.get("body") or "") for r in releases],
            "bodies": [
                {
                    "tag": r.get("tag_name"),
                    "name": r.get("name"),
                    "prerelease": r.get("prerelease"),
                    "body": (r.get("body") or "")[:6000],
                }
                for r in releases
            ],
        }
        commits = [
            c
            for c in gh.json(f"repos/{full}/commits?per_page=30") or []
            if isinstance(c, dict)
        ]
        messages = [
            ((c.get("commit") or {}).get("message") or "").strip() for c in commits
        ]
        subjects = [m.splitlines()[0] if m else "" for m in messages]
        record["commits"] = {
            "sampled": len(messages),
            "subject_lengths": [len(s) for s in subjects],
            "with_body": sum(
                "\n" in m and bool(m.split("\n", 1)[1].strip()) for m in messages
            ),
            "messages": [m[:6000] for m in messages],
        }
        pulls = [
            p
            for p in gh.json(
                f"repos/{full}/pulls?state=closed&per_page=10&sort=updated&direction=desc"
            )
            or []
            if isinstance(p, dict)
        ]
        record["pulls"] = {
            "sampled": len(pulls),
            "body_chars": [len(p.get("body") or "") for p in pulls],
            "items": [
                {
                    "number": p.get("number"),
                    "title": p.get("title"),
                    "merged_at": p.get("merged_at"),
                    "author_type": (p.get("user") or {}).get("type"),
                    "body": (p.get("body") or "")[:4000],
                }
                for p in pulls
            ],
        }
        write_json(target, record)


def stage_files(gh, out):
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for path in sorted((out / "repos").glob("*.json")):
        record = json.loads(path.read_text())
        full = record["full_name"]
        folder = out / "files" / slug(full)
        folder.mkdir(parents=True, exist_ok=True)
        saved = manifest.setdefault(full, {})
        types = {
            ("" if where == "/" else where) + name: kind
            for where, entries in record["listing"].items()
            for name, kind in entries
        }
        want = {}
        for key, paths in record.get("files", {}).items():
            for p in paths:
                if key in FULL:
                    want[p] = FULL_CAP
                elif key in HEAD:
                    want[p] = HEAD[key]
        for p in types:
            if AGENT_NAMES.match(p.split("/")[-1]):
                want[p] = FULL_CAP
        for p, cap in sorted(want.items()):
            if p in saved:
                continue
            if types.get(p, "file") == "dir":
                save_folder(gh, full, p, folder, saved)
                continue
            text = gh.raw(full, p)
            if text is None:
                saved[p] = {"type": types.get(p, "file"), "error": "fetch failed"}
                continue
            name = p.replace("/", "__")
            (folder / name).write_text(text[:cap])
            saved[p] = {
                "type": types.get(p, "file"),
                "bytes": len(text.encode()),
                "saved": name,
                "capped": len(text) > cap,
            }
        if "docs/__second_level" not in saved:
            dirs = {}
            for name, kind in record["listing"].get("docs/", []):
                if kind == "dir":
                    listing = gh.json(f"repos/{full}/contents/docs/{quote(name)}")
                    dirs[name] = [
                        [i["name"], i.get("type")]
                        for i in listing or []
                        if isinstance(i, dict)
                    ]
            saved["docs/__second_level"] = {"type": "docs-second-level", "dirs": dirs}
        write_json(manifest_path, manifest)


def save_folder(gh, full, path, folder, saved):
    """Save a folder's listing, its first 8 files, and the names one level down."""
    listing = gh.json(f"repos/{full}/contents/{quote(path)}")
    entries = [[i["name"], i.get("type")] for i in listing or [] if isinstance(i, dict)]
    saved[path] = {"type": "dir", "entries": entries}
    for name, _ in [e for e in entries if e[1] == "file"][:8]:
        sub = f"{path}/{name}"
        text = gh.raw(full, sub)
        if text is not None:
            (folder / sub.replace("/", "__")).write_text(text[:FULL_CAP])
            saved[sub] = {
                "type": "file",
                "bytes": len(text.encode()),
                "saved": sub.replace("/", "__"),
            }
    for name, kind in entries:
        if kind == "dir":
            sub = f"{path}/{name}"
            inner = gh.json(f"repos/{full}/contents/{quote(sub)}")
            saved[sub] = {
                "type": "dir",
                "entries": [
                    [i["name"], i.get("type")]
                    for i in inner or []
                    if isinstance(i, dict)
                ],
            }


def stage_trees(gh, out):
    (out / "trees").mkdir(exist_ok=True)
    for path in sorted((out / "repos").glob("*.json")):
        record = json.loads(path.read_text())
        target = out / "trees" / path.name
        if target.exists():
            continue
        branch = record.get("default_branch") or "HEAD"
        done = gh.run(f"repos/{record['full_name']}/git/trees/{branch}?recursive=1")
        if done.returncode:
            write_json(target, {"error": done.stderr[:200]})
            continue
        tree = json.loads(done.stdout)
        paths = [e["path"] for e in tree.get("tree", []) if e["type"] == "blob"]
        write_json(
            target,
            {
                "truncated": tree.get("truncated"),
                "total_paths": len(paths),
                "doc_paths": [
                    p for p in paths if TREE_DOCS.search(p) and not TREE_SKIP.search(p)
                ][:6000],
                "workflows": [p for p in paths if p.startswith(".github/workflows/")],
                "dirs": sorted({p.split("/")[0] for p in paths if "/" in p}),
            },
        )


def stage_pr_titles(gh, out):
    target = out / PR_TITLES
    done = json.loads(target.read_text()) if target.exists() else {}
    for path in sorted((out / "repos").glob("*.json")):
        record = json.loads(path.read_text())
        full = record["full_name"]
        if full in done:
            continue
        entry = {"release": None, "checked": []}
        for body in record["releases"].get("bodies") or []:
            lines = [
                line
                for line in (body["body"] or "").splitlines()
                if LIST_LINE.match(line) and PR_REFERENCE.search(line)
            ]
            if len(lines) < 3:
                continue
            entry["release"] = body["tag"]
            for line in lines[:5]:
                found = PR_REFERENCE.search(line)
                number = found.group(1) or found.group(2)
                pull = gh.json(f"repos/{full}/pulls/{number}")
                if pull is None:
                    entry["checked"].append(
                        {
                            "line": line.strip(),
                            "pr": number,
                            "error": "not a PR or not found",
                        }
                    )
                else:
                    entry["checked"].append(
                        {
                            "line": line.strip(),
                            "pr": number,
                            "title": pull.get("title") or "",
                        }
                    )
            break
        done[full] = entry
        write_json(target, done)


def stage_commits_100(gh, out):
    target = out / COMMITS_100
    done = json.loads(target.read_text()) if target.exists() else {}
    for path in sorted((out / "repos").glob("*.json")):
        record = json.loads(path.read_text())
        full = record["full_name"]
        subjects = [
            m.splitlines()[0] if m else "" for m in record["commits"]["messages"]
        ]
        if full in done or not subjects:
            continue
        if sum(bool(CONVENTIONAL.match(s)) for s in subjects) / len(subjects) < 0.5:
            continue
        commits = gh.json(f"repos/{full}/commits?per_page=100") or []
        done[full] = [
            ((c.get("commit") or {}).get("message") or "")
            for c in commits
            if isinstance(c, dict)
        ]
        write_json(target, done)


def stage_reads(gh, out, picks_path):
    """Fetch every file listed in the picks. For a folder pick, fetch the first file in the folder."""
    picks = json.loads(Path(picks_path).read_text())
    folder = out / "reads"
    folder.mkdir(exist_ok=True)
    index_path = out / "reads-index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    have = {(e["sample"], e["repo"], e.get("pick", e["path"])) for e in index}
    for name, sample in picks["samples"].items():
        for pick in sample.get("picks", []):
            if not isinstance(pick, dict) or "repo" not in pick:
                continue
            if "path" not in pick and "folder" not in pick:
                continue
            key = (name, pick["repo"], pick.get("path") or pick["folder"])
            if key in have:
                continue
            path = pick.get("path")
            if path is None:
                listing = gh.json(
                    f"repos/{pick['repo']}/contents/{quote(pick['folder'].rstrip('/'))}"
                )
                files = [
                    i["name"]
                    for i in listing or []
                    if isinstance(i, dict) and i.get("type") == "file"
                ]
                if not files:
                    continue
                path = pick["folder"] + files[0]
            text = gh.raw(pick["repo"], path)
            if text is None:
                continue
            target = folder / f"{slug(pick['repo'])}___{path.replace('/', '__')}"
            target.write_text(text[:FULL_CAP])
            index.append(
                {
                    "sample": name,
                    "group": pick.get("group", name),
                    "repo": pick["repo"],
                    "pick": key[2],
                    "path": path,
                    "file": str(target.relative_to(out)),
                }
            )
            have.add(key)
            write_json(index_path, index)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--account", help="GitHub account whose public stars form the corpus"
    )
    source.add_argument(
        "--repos",
        type=Path,
        help="JSONL list of repositories with frozen star counts, such as "
        "fixtures/corpus-2026-10-08.jsonl",
    )
    parser.add_argument("--min-stars", type=int, default=3000)
    parser.add_argument("--out", required=True, type=Path, help="raw data folder")
    parser.add_argument(
        "--stage",
        nargs="+",
        choices=STAGES,
        help="stages to run (default: all but reads)",
    )
    parser.add_argument(
        "--picks",
        type=Path,
        help="picks file from corpus_sample.py, for the reads stage",
    )
    args = parser.parse_args(argv)
    stages = args.stage or [s for s in STAGES if s != "reads"]
    if "reads" in stages and not args.picks:
        parser.error("the reads stage takes --picks")
    if "stars" in stages and not (args.account or args.repos):
        parser.error("the stars stage takes --account or --repos")
    args.out.mkdir(parents=True, exist_ok=True)
    gh = GitHub()
    try:
        if "stars" in stages and args.repos:
            stage_listed(gh, args.out, args.repos, args.min_stars)
        elif "stars" in stages:
            stage_stars(gh, args.out, args.account, args.min_stars)
        if "repos" in stages:
            stage_repos(gh, args.out, corpus(args.out, args.min_stars))
        if "files" in stages:
            stage_files(gh, args.out)
        if "trees" in stages:
            stage_trees(gh, args.out)
        if "pr-titles" in stages:
            stage_pr_titles(gh, args.out)
        if "commits-100" in stages:
            stage_commits_100(gh, args.out)
        if "reads" in stages:
            stage_reads(gh, args.out, args.picks)
    finally:
        print(f"{gh.calls} gh api calls", file=sys.stderr)


if __name__ == "__main__":
    main()
