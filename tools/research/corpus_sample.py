"""Draw the seeded reading samples from a fetched corpus.

Each sample is a list of picks: a repository, or a file to read in a
repository. The same raw data, seed and earlier reads give the same picks.
`corpus_fetch.py --stage reads --picks FILE` fetches the picked files.

Samples:

- slices: 28 repositories in 4 slices, stratified by language and star tier
  and shuffled inside each stratum.
- new-names: files with unmatched names (no 2026-10-03 pattern). Up to 2
  repositories for each document-like name in 2 or more repositories, 30
  names seen in one repository, and the first file of selected `docs/` folders.
- small-groups: the first 3 files of each proposal and decision-record folder
  under the 2026-10-08 folder rule; every RELEASE, REVIEW and AI policy file;
  6 sub-folder READMEs.
- terms: 30 contexts for each of six words, spread over document kinds.
- precision: up to 10 positive files for each document flag and 7 release
  bodies for each release element, for checking keyword patterns by reading.
- confirm: three draws of 10 repositories: repositories with commit messages,
  with an agent file at the root, and with a human-written pull request body
  over 200 characters.
- folders: 3 files from each proposal or decision-record folder added by the
  later folder rule.
- subfolder-readmes: 20 repositories with a sub-folder README, one README each.
- architecture: 10 repositories with an architecture file name.

The last three samples skip repositories already read in the same group.
Pass the earlier picks or reads index with `--prior`.

Usage:

    python3 tools/research/corpus_sample.py --data DIR --seed 20261008 \\
        --sample slices new-names small-groups terms --out picks.json
    python3 tools/research/corpus_sample.py --data DIR --seed 20261009 \\
        --sample confirm folders subfolder-readmes architecture --prior reads.json \\
        --out picks-2.json
"""

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path

import corpus_counts

SAMPLES = (
    "slices",
    "new-names",
    "small-groups",
    "terms",
    "precision",
    "confirm",
    "folders",
    "subfolder-readmes",
    "architecture",
)
LANGUAGES = ("TypeScript", "Go", "Python", "Rust", "JavaScript", "Swift")
SLICE_RULE = (
    "stratum = (language in TypeScript/Go/Python/Rust/JavaScript/Swift else other, "
    "star tier 40k+/10-40k/3-10k)"
)
SLICE_METHOD = "random.Random(seed).shuffle per stratum, strata visited in sorted order, round robin"

# Folder rules as run on 2026-10-08 for the small-groups sample.
FIRST_PROPOSAL_FOLDERS = re.compile(
    r"^(proposals?/|docs/proposals?/|Documentation/proposals/|design/|docs/designs?/|rfcs/"
    r"|docs/enhancements/|geps/|engdocs/design/)",
    re.IGNORECASE,
)
FIRST_ADR_FOLDERS = re.compile(
    r"^(docs/adr/|docs/architecture-decisions/|docs/v5/architecture/adr/|engdocs/adr/)",
    re.IGNORECASE,
)
NEW_NAME_SKIP = re.compile(
    r"^(readme_\w+|index|requirements(-dev)?|cname|version|package|tsconfig|.*lock.*)$",
    re.IGNORECASE,
)
NEW_NAME_FOLDERS = (
    "superpowers",
    "plans",
    "internal",
    "codebase",
    "design",
    "designs",
    "proposal",
    "adr",
    "specs",
    "releases",
    "blog",
    "contributing",
)


def tier(stars):
    return "40k+" if stars >= 40000 else "10-40k" if stars >= 10000 else "3-10k"


def slices(repos, seed=20261008, size=28):
    """Pick `size` repositories, one stratum at a time, in four slices.

    `repos` holds dicts with `full_name`, `language` and `stars`. Each stratum
    is shuffled with `random.Random(seed)`; strata are visited in sorted order.
    """
    repos = sorted(repos, key=lambda r: r["full_name"])
    rng = random.Random(seed)
    buckets = {}
    for r in repos:
        language = r.get("language") or "none"
        key = (language if language in LANGUAGES else "other", tier(r["stars"]))
        buckets.setdefault(key, []).append(r["full_name"])
    for key in sorted(buckets):
        rng.shuffle(buckets[key])
    picked = []
    while len(picked) < size and any(buckets.values()):
        for key in sorted(buckets):
            if buckets[key] and len(picked) < size:
                picked.append(buckets[key].pop(0))
    return {
        "seed": seed,
        "python_random": SLICE_METHOD,
        "rule": SLICE_RULE,
        "input_repos": len(repos),
        "input_sha256": hashlib.sha256(
            "\n".join(r["full_name"] for r in repos).encode()
        ).hexdigest(),
        "slices": [picked[i::4] for i in range(4)],
    }


def new_names(data, seed):
    rows = [r for r in corpus_counts.name_inventory(data) if not r["matched"]]
    by_location = {
        r["full_name"]: {
            where: {n for n, _ in entries} for where, entries in r["listing"].items()
        }
        for r in data.repos
    }
    candidates = defaultdict(list)
    for row in rows:
        name = row["name"]
        if row["type"] != "file":
            continue
        if not (
            corpus_counts.DOC_LIKE.search(name) or corpus_counts.CAPS_NAME.match(name)
        ):
            continue
        stem = corpus_counts.DOC_LIKE.sub("", name).lower()
        for full in sorted(by_location):
            if name in by_location[full].get(row["location"], set()):
                candidates[stem].append((row["location"], name, full))
    multi = {
        s: v
        for s, v in candidates.items()
        if len({x[2] for x in v}) >= 2 and not NEW_NAME_SKIP.match(s)
    }
    single = sorted(
        (s, v)
        for s, v in candidates.items()
        if len({x[2] for x in v}) == 1 and not NEW_NAME_SKIP.match(s)
    )
    random.Random(seed).shuffle(single)
    picks = []
    for _, found in sorted(multi.items()):
        seen = []
        for where, name, full in found:
            if full not in seen and len(seen) < 2:
                seen.append(full)
                picks.append(
                    {
                        "group": "A",
                        "repo": full,
                        "path": ("" if where == "/" else where) + name,
                    }
                )
    for _, found in single[:30]:
        where, name, full = found[0]
        picks.append(
            {"group": "B", "repo": full, "path": ("" if where == "/" else where) + name}
        )
    for full, entries in sorted(data.manifest.items()):
        second = entries.get("docs/__second_level", {}).get("dirs", {})
        for folder in NEW_NAME_FOLDERS:
            if folder not in second:
                continue
            files = [
                n
                for n, t in second[folder]
                if t == "file" and corpus_counts.DOC_LIKE.search(n)
            ]
            subs = [n for n, t in second[folder] if t == "dir"]
            if files:
                picks.append(
                    {"group": "C", "repo": full, "path": f"docs/{folder}/{files[0]}"}
                )
            elif subs:
                picks.append(
                    {"group": "C", "repo": full, "folder": f"docs/{folder}/{subs[0]}/"}
                )
    return {
        "rule": "A: names in 2+ repos, up to 2 repos each; B: 30 seeded names seen once; C: docs/ folders",
        "picks": picks,
    }


def small_groups(data, seed):
    picks = []
    for full, tree in data.trees.items():
        paths = tree.get("doc_paths", [])
        proposals = sorted(
            p
            for p in paths
            if FIRST_PROPOSAL_FOLDERS.match(p)
            and not re.search(r"readme|template|index|_index", p, re.IGNORECASE)
        )
        picks += [{"group": "proposal", "repo": full, "path": p} for p in proposals[:3]]
        adrs = sorted(
            p
            for p in paths
            if FIRST_ADR_FOLDERS.match(p)
            and not re.search(r"readme|template|index", p, re.IGNORECASE)
        )
        picks += [{"group": "adr", "repo": full, "path": p} for p in adrs[:3]]
    for r in data.repos:
        for where, entries in r["listing"].items():
            prefix = "" if where == "/" else where
            for name, kind in entries:
                if kind == "dir":
                    continue
                if re.match(r"^releas(e|ing)(\.\w+)?$", name, re.IGNORECASE):
                    picks.append(
                        {
                            "group": "release",
                            "repo": r["full_name"],
                            "path": prefix + name,
                        }
                    )
                if re.match(r"^review(ing)?(\.\w+)?$", name, re.IGNORECASE):
                    picks.append(
                        {
                            "group": "review",
                            "repo": r["full_name"],
                            "path": prefix + name,
                        }
                    )
                if re.match(
                    r"^(ai[-_]?policy|agent[-_]?policy)(\.\w+)?$", name, re.IGNORECASE
                ):
                    picks.append(
                        {
                            "group": "aipolicy",
                            "repo": r["full_name"],
                            "path": prefix + name,
                        }
                    )
    readmes = [
        (full, p)
        for full, tree in data.trees.items()
        for p in tree.get("doc_paths", [])
        if re.search(r"(^|/)readme\.md$", p, re.IGNORECASE)
        and p.count("/") == 1
        and not re.match(
            r"(docs?|examples?|tests?|test|\.github|scripts|templates?)/",
            p,
            re.IGNORECASE,
        )
    ]
    random.Random(seed).shuffle(readmes)
    picks += [
        {"group": "package_readme", "repo": full, "path": p} for full, p in readmes[:6]
    ]
    return {
        "rule": "first 3 files per folder by path order; every matching file; 6 seeded sub-folder READMEs",
        "picks": picks,
    }


def terms(data, seed):
    rng = random.Random(seed)
    contexts = {w: [] for w in corpus_counts.TERMS}
    for kind, full, text in corpus_counts.term_documents(data):
        clean = corpus_counts.clean_text(text)
        for word, rx in corpus_counts.TERMS.items():
            for found in re.finditer(rx, clean, re.IGNORECASE):
                snippet = clean[max(0, found.start() - 90) : found.end() + 90].replace(
                    "\n", " "
                )
                contexts[word].append((kind, full, re.sub(r"\s+", " ", snippet)))
    picks = {}
    for word in corpus_counts.TERMS:
        by_kind = defaultdict(list)
        for c in sorted(contexts[word]):
            by_kind[c[0]].append(c)
        kinds = sorted(by_kind)
        for k in kinds:
            rng.shuffle(by_kind[k])
        picked = []
        i = 0
        while len(picked) < 30 and any(by_kind.values()):
            k = kinds[i % len(kinds)]
            if by_kind[k]:
                picked.append(by_kind[k].pop())
            i += 1
        picks[word] = [
            {"kind": k, "repo": full, "context": text} for k, full, text in picked
        ]
    return {
        "rule": "30 contexts per word, round robin over document kinds",
        "contexts": picks,
    }


def precision(data, seed):
    picks = []
    doc_flags = corpus_counts.document_flags(data)
    for kind, rows in doc_flags.items():
        for flag in corpus_counts.DOC_KINDS[kind]:
            positive = [key for key, row in rows.items() if row[flag]]
            random.Random(seed).shuffle(positive)
            for key in positive[:10]:
                full, path = key.split(":", 1)
                picks.append({"group": f"{kind}.{flag}", "repo": full, "path": path})
    rng = random.Random(seed)
    for element, rx in corpus_counts.RELEASE_ELEMENTS.items():
        hits = [
            (r["full_name"], b["tag"])
            for r in data.repos
            for b in r["releases"].get("bodies") or []
            if re.search(rx, b["body"] or "")
        ]
        for full, tag in rng.sample(hits, min(7, len(hits))):
            picks.append({"group": f"release.{element}", "repo": full, "tag": tag})
    return {
        "rule": "10 positive files per flag; 7 release bodies per element",
        "picks": picks,
    }


def confirm(data, seed):
    def ten(pool):
        return random.Random(seed).sample(sorted(pool), min(10, len(pool)))

    messages = [r["full_name"] for r in data.repos if r["commits"]["messages"]]
    names = {r["full_name"] for r in data.repos}
    agents = [
        full
        for full, entries in data.manifest.items()
        if full in names
        and any(
            p in ("AGENTS.md", "CLAUDE.md") and "saved" in e for p, e in entries.items()
        )
    ]
    bodies = [
        r["full_name"]
        for r in data.repos
        if any(
            i.get("author_type") == "User" and len(i.get("body") or "") > 200
            for i in r["pulls"].get("items") or []
        )
    ]
    return {
        "rule": "10 repositories per pool",
        "picks": [{"group": "commit-message", "repo": f} for f in ten(messages)]
        + [{"group": "agent-instructions", "repo": f} for f in ten(agents)]
        + [{"group": "change-description", "repo": f} for f in ten(bodies)],
    }


def prior_repos(prior, group):
    return {e["repo"] for e in prior if e.get("group") == group}


def folders(data, seed, prior):
    picks = []
    for group, folder_of in (
        ("proposal", corpus_counts.proposal_folder),
        ("adr", corpus_counts.adr_folder),
    ):
        done = prior_repos(prior, group)
        for full, tree in data.trees.items():
            if full in done:
                continue
            pool = sorted(
                p
                for p in tree.get("doc_paths", [])
                if (f := folder_of(p)) is not None and corpus_counts.folder_member(p, f)
            )
            if pool:
                for p in random.Random(seed).sample(pool, min(3, len(pool))):
                    picks.append({"group": group, "repo": full, "path": p})
    return {
        "rule": "3 seeded files per unread folder repository",
        "picks": picks,
    }


def subfolder_readmes(data, seed, prior):
    found = corpus_counts.subfolder_readmes(data, narrow=False)
    pool = sorted(set(found) - prior_repos(prior, "package_readme"))
    rng = random.Random(seed)
    picks = []
    for full in rng.sample(pool, min(20, len(pool))):
        paths = [p for p in found[full] if p.lower().endswith("readme.md")] or found[
            full
        ]
        picks.append(
            {"group": "package_readme", "repo": full, "path": rng.choice(paths)}
        )
    return {"rule": "20 seeded repositories, one README.md each", "picks": picks}


def architecture(data, seed, prior):
    found = corpus_counts.architecture_files(data)
    pool = sorted(set(found) - prior_repos(prior, "architecture"))
    picks = [
        {"group": "architecture", "repo": full, "path": found[full][0]}
        for full in random.Random(seed).sample(pool, min(10, len(pool)))
    ]
    return {
        "rule": "10 seeded repositories, the shallowest architecture file each",
        "picks": picks,
    }


def draw(data, names, seed, prior=()):
    prior = list(prior)
    out = {"seed": seed, "samples": {}}
    for name in names:
        if name == "slices":
            out["samples"][name] = slices(data.repos, seed)
        elif name == "new-names":
            out["samples"][name] = new_names(data, seed)
        elif name == "small-groups":
            out["samples"][name] = small_groups(data, seed)
        elif name == "terms":
            out["samples"][name] = terms(data, seed)
        elif name == "precision":
            out["samples"][name] = precision(data, seed)
        elif name == "confirm":
            out["samples"][name] = confirm(data, seed)
        elif name == "folders":
            out["samples"][name] = folders(data, seed, prior)
        elif name == "subfolder-readmes":
            out["samples"][name] = subfolder_readmes(data, seed, prior)
        elif name == "architecture":
            out["samples"][name] = architecture(data, seed, prior)
    return out


def load_prior(path):
    """Earlier reads as `{group, repo}` entries, from a picks file or a reads index."""
    if path is None:
        return []
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        return data
    if "samples" in data:
        return [
            p
            for s in data["samples"].values()
            for p in s.get("picks", [])
            if isinstance(p, dict)
        ]
    return data.get("picks", [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--data", required=True, type=Path, help="raw data folder from corpus_fetch.py"
    )
    parser.add_argument("--min-stars", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--sample", nargs="+", choices=SAMPLES, default=list(SAMPLES))
    parser.add_argument(
        "--prior", type=Path, help="earlier picks or reads index, with a group per read"
    )
    parser.add_argument("--out", type=Path, help="picks file (default: print)")
    args = parser.parse_args(argv)
    data = corpus_counts.load(args.data, args.min_stars)
    result = draw(data, args.sample, args.seed, load_prior(args.prior))
    text = json.dumps(result, indent=1, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
