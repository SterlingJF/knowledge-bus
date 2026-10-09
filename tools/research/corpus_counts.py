"""Count document prevalence and every open fact over a fetched corpus.

Reads the raw data folder from `corpus_fetch.py` and prints one JSON document
of counts. Counts come from file names, file trees, parsed files and keyword
patterns. Each keyword count is a first pass: cite the count with the share of
sampled files a reader confirmed, from a seeded sample drawn by
`corpus_sample.py --sample precision`.

Optional label files written by readers, read from `--labels` (default: the
raw data folder). `fixtures/` holds the 2026-10-08 labels:

- `of6_labels.tsv`: one repository kind per repository: D developer tool,
  library or framework; O operations software; E end-user application;
  R research model release; C collection or theme. Without the file, the
  script reads the `kind` field of the repository list.
- `of2-security-channel.json`: a reporting-channel class per SECURITY file.
- `of7-labels.json`: a sense label for each sampled context of the six studied words.

With `--repo-list FILE`, the script also writes the repository list table of
the research document.

Usage:

    python3 tools/research/corpus_counts.py --data DIR --min-stars 3000 --out counts.json
    python3 tools/research/corpus_counts.py --data DIR --labels tools/research/fixtures \\
        --earlier-run 2026-10-03T18:00:00Z --reads READS/reads-index.json \\
        --out counts.json --repo-list repo-list.md
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

import corpus_fetch

# README section kinds, matched on normalised heading text. First match wins.
SECTIONS = [
    (
        "install",
        r"install|getting started|quick ?start|setup|set up|download|get started",
    ),
    ("usage", r"usage|how to use|examples?|tutorial|guide|walkthrough|cli|commands"),
    (
        "features",
        r"features?|highlights|capabilities|what .* does|why\b|overview|about|introduction|what is",
    ),
    ("configuration", r"config|options|settings|environment"),
    ("docs_link", r"documentation|docs|learn more|resources"),
    (
        "contributing",
        r"contribut|development|building from source|build from source|hacking",
    ),
    (
        "community_support",
        r"community|support|help|discuss|chat|discord|slack|contact|faq",
    ),
    ("license", r"licen[sc]e"),
    ("acknowledgements", r"acknowledg|credits|thanks|sponsors?|backers|contributors"),
    ("roadmap_status", r"roadmap|status|project status|stability|changelog|release"),
    ("architecture", r"architecture|how it works|design|internals"),
    ("comparison", r"comparison|alternatives|vs\.?|benchmark|performance"),
    ("security", r"security"),
    ("api", r"\bapi\b|reference"),
    ("requirements", r"requirements|prerequisites|dependencies|compatib|supported"),
]
BADGE = re.compile(
    r"!\[[^\]]*\]\([^)]*(?:shields\.io|badge)[^)]*\)"
    r"|<img[^>]+src=[\"'][^\"']*(?:shields\.io|badge)[^\"']*"
)
README_MENTIONS = {
    "sbom": r"\bsbom\b|software bill of materials",
    "slsa": r"\bslsa\b",
    "scorecard_badge": r"api\.securityscorecards\.dev|api\.scorecard\.dev|securityscorecards\.dev/projects",
    "best_practices_badge": r"bestpractices\.(coreinfrastructure|dev)",
}
SEMVER = r"semantic versioning|semver"

# Element flags per document kind: (heading pattern, body pattern). A flag is
# "H" when a heading matches, "B" when only the body matches.
CONTRIBUTING = {
    "route": (
        r"how to contribute|ways to contribute|getting started|where to start|reporting (bugs|issues)|opening an issue|submitting|raising a pr|creating a pull request|steps to contribute|proposing|please ask first",
        r"(open|file|create|raise|submit|send)\s+(an?\s+)?(new\s+)?(issue|pull request|PR)\b|discuss[^.\n]{0,40}(first|before)|ask first|before (you )?(start|begin|open|submit|send)",
    ),
    # The `\\b` below matches a literal backslash and "b". The pattern stays as
    # run on 2026-10-08, so the issue-first count reproduces.
    "route_first": (
        r"ask first|discussion is required|issue requirement|before you (start|begin|contribute)|before contributing|deciding what to work on|approval for",
        r"(open|file|create|raise|start)[^.\n]{0,30}(issue|discussion)[^.\n]{0,50}(first|before)|ask first|discuss[^.\n]{0,40}(before|first)|(issue|discussion)s? (is |are )?(required|first)\\b(?<!good first)|before (you )?(open|submit|send|start)[^.\n]{0,40}(pr\b|pull request|work|coding|writing)|must (be )?(linked|associated)[^.\n]{0,30}issue|approved issue",
    ),
    "refusal": (
        r"won'?t accept|not accept|what this project is not|non-goals|unaccepted|will be closed",
        r"(won'?t|can'?t|cannot|will not|would not|do not|don'?t|not)( be)? (accept|merge)\b|not accepting|(will|may|might) be (closed|rejected|declined)|out of scope|we (do not|don'?t|won'?t) (accept|merge|take|consider)|no longer (accept|taking)|unsolicited|not (a )?goals?\b|what (this project|we) (is|are) not|doesn'?t accept|unlikely to be (accepted|merged)|not interested in",
    ),
    "evidence": (
        r"checklist|test(s|ing)? required|before (you )?(submit|open)",
        r"(tests?|unit tests?) (are |is )?(required|mandatory|needed|must)|must (include|have|add|come with|be accompanied)[^.\n]{0,60}(tests?|screenshots?|steps)|(include|add|write|provide)[^.\n]{0,30}(tests?|screenshots?|reproduc)|without (corresponding )?tests|checklist",
    ),
    "dev_setup": (
        r"set ?up|development|dev(elopment)? environment|building|build|prerequisites|getting started|install|hacking|running locally",
        r"git clone|npm install|pnpm install|pip install|uv sync|make (build|setup)|cargo build|go build|nix develop|docker compose",
    ),
    "test_cmd": (
        None,
        r"(npm|pnpm|yarn|bun) (run )?test|pytest|go test|cargo (nextest |t|test)|make (test|check)|tox\b|nox\b|swift test|mvn |gradle|ctest|bundle exec rspec|vitest|jest",
    ),
    "commit_fmt": (
        r"commit (message|style|convention|format)|conventional commits|sign.?off|pull request title",
        r"conventional commits?|semantic commit|sign.?off|signed-off-by|commit (style|format|conventions?)|commit messages? (should|must|follow|format|conventions?|guidelines?)|pull request title (format|conventions?)|imperative mood",
    ),
    "cla_dco": (
        r"\bCLA\b|\bDCO\b|license agreement|certificate",
        r"\bCLA\b|contributor license agreement|\bDCO\b|developer certificate of origin",
    ),
    "ai": (
        r"\bAI\b|\bLLMs?\b|copilot",
        r"\b(AI|LLM)s?[- ](generated|assisted|usage|use|policy|contributions?|tools|coding)|(disclose|disclosure)[^.\n]{0,60}\b(AI|LLM)|\b(AI|LLM)\b[^.\n]{0,60}(disclose|disclosure)|generated (by|with|using) (an? )?(AI|LLM|Copilot|ChatGPT|Claude)|use of (AI|LLM|Copilot|ChatGPT|Claude)|(Copilot|ChatGPT|Claude|Cursor)[^.\n]{0,40}(generated|assisted|used)",
    ),
    "conduct": (r"code of conduct", r"code of conduct|CODE_OF_CONDUCT"),
    "style": (
        r"style|lint|format|convention",
        r"\b(eslint|prettier|ruff|black|gofmt|rustfmt|clippy|style guide|lint)\b",
    ),
    "review": (
        r"review|merge|triage",
        r"(will|would|should) (be )?review|code review|reviewers?|maintainers? will",
    ),
    "release": (r"releas", None),
    "channel": (
        r"community|chat|contact|communication|help|support|questions",
        r"discord|slack|matrix|irc\b|gitter|mailing list|forum|discussions",
    ),
    "contrib_license": (
        r"licen[sc]e",
        r"by contributing|licensed under|contributions? (are|will be) (licensed|under)",
    ),
}
SECURITY = {
    "channel": (
        None,
        r"security/advisories|advisories/new|private vulnerability reporting|private security advisor|hackerone|bugcrowd|huntr\.|intigriti|[\w.+-]+@[\w-]+\.[\w.]+|security\.[\w-]+\.\w+/",
    ),
    "contents": (
        r"what to include|include|details|information",
        r"(should|please|must) (include|provide|contain)|following information|steps to reproduce|proof of concept|\bpoc\b",
    ),
    "supported_versions": (
        r"supported versions?|versions?|support",
        r"supported versions?|versions? (that are |which are )?supported|\|\s*version\s*\|\s*supported|security (fixes|updates|patches) (for|are)",
    ),
    "reply_time": (
        None,
        r"within \d+ ?(business |working |calendar )?(hours?|days?|weeks?)|\d+ ?(business |working )?(hours?|days?) (to|for|of) (respond|reply|acknowledg)|acknowledge[^.\n]{0,60}(\d+|hours|days)",
    ),
    "disclosure": (
        r"disclosure|coordinated|embargo|timeline",
        r"\d+ ?days|coordinated (vulnerability )?disclosure|embargo|public disclosure|responsible disclosure|cve\b",
    ),
    "scope": (
        r"scope|out of scope|not (a )?vulnerab",
        r"out of scope|in scope|are not (considered )?(security )?vulnerabilit|not (considered )?(a )?(security )?vulnerabilit(y|ies) (if|when|unless)",
    ),
    "bounty": (r"bounty", r"bounty|reward"),
}
CODE_OF_CONDUCT = {
    "covenant": (None, r"contributor covenant"),
    "unacceptable": (
        r"unacceptable|expected behavior|standards|our pledge|behaviou?r",
        r"unacceptable behaviou?r|harass",
    ),
    "report": (
        r"report|enforcement|contact",
        r"(report|contact)[^.\n]{0,80}(@|email|e-mail)|\b[\w.+-]+@[\w-]+\.[\w.]+",
    ),
    "consequences": (
        r"consequences|enforcement guidelines|correction|warning|ban",
        r"consequences|temporary ban|permanent ban|warning",
    ),
    "scope": (
        r"^scope",
        r"applies within all community spaces|this code of conduct applies",
    ),
    "enforcers": (
        r"enforcement|responsibilities",
        r"community leaders|project (team|maintainers)|moderators",
    ),
}
AGENT = {
    "build_cmd": (
        r"build|commands|setup|development",
        r"(npm|pnpm|yarn|bun) (run )?(build|install)|make (build|all)?|cargo build|go build|uv sync|pip install|swift build|xcodebuild|just \w+|mise |docker compose",
    ),
    "test_cmd": (
        r"test",
        r"(npm|pnpm|yarn|bun) (run )?test|pytest|go test|cargo (nextest|test)|make test|swift test|vitest|jest|uv run",
    ),
    "style": (
        r"style|convention|format|lint",
        r"\b(eslint|prettier|ruff|black|gofmt|rustfmt|clippy|style|naming|indent|lint)\b",
    ),
    "generated": (
        r"generated files?|generated code|codegen",
        r"(do not|never|don'?t) (edit|modify|change)[^.\n]{0,40}generated|generated (files?|code)\b|auto-?generated|\bcodegen\b|DO NOT EDIT|(make|npm run|pnpm|yarn) (run )?(generate|gen|codegen)",
    ),
    "pre_commit_checks": (
        r"before (you )?commit|checks|pre-commit|verification|validation",
        r"before (committing|you commit|submitting|pushing|opening)|pre-commit|must pass|should pass|run (the )?(lint|tests|checks)",
    ),
    "ask_first": (
        r"ask first|ask before|needs? approval|requires? approval",
        r"\b(ask|confirm with|check with|get approval from|wait for) (the )?(user|human|maintainers?|owner)\b|ask first|ask before|without (asking|approval|permission)|requires? (human |maintainer |explicit )?approval|human approval",
    ),
    "prohibitions": (
        r"never|do not|don't|must not|boundaries|critical safety",
        r"\b(never|do not|don'?t|must not) (commit|push|force|delete|run|modify|edit|use|add|change|include|create|remove)",
    ),
    "layout": (
        r"structure|layout|repository map|architecture|overview|directory|monorepo",
        r"├|└|directory structure|project structure|repository (layout|structure|map)|monorepo",
    ),
    "git_conv": (
        r"commit|pull request|\bpr\b|git|branch",
        r"commit message|conventional commits?|pull request|branch",
    ),
    "security": (r"security|secrets", r"secret|credential|api key|token"),
    "points_elsewhere": (
        None,
        r"@AGENTS\.md|see (\[?)AGENTS\.md|@CLAUDE\.md|symlink|read (\[?)AGENTS\.md|refer to (\[?)AGENTS",
    ),
}
PR_TEMPLATE = {
    "description": (
        r"description|summary|what|changes?|overview|purpose",
        r"describe|description|summary",
    ),
    "related_issue": (
        r"issue|related|linked|fixes|closes|reference",
        r"(fix(es)?|close[sd]?|resolve[sd]?)\s*(:|#)|related issue|linked issue|issue (number|#)",
    ),
    "verification": (
        r"test|verif|how (was|has|did)|validation|checks?",
        r"how (was|has|did|have) (this|it|you|the change)[^.\n]{0,30}(test|verif|check)|tested|test plan|testing|verified",
    ),
    "checklist": (None, r"(?m)^\s*[-*] \[[ xX]\]"),
    "breaking": (r"breaking", r"(?<!non-)(?<!non )\bbreaking"),
    "release_note": (
        r"release ?notes?|changelog|user-facing",
        r"release[- ]?notes?|changelog|```release-note",
    ),
    "screenshots": (
        r"screenshot|visual|before|demo|video",
        r"screenshot|screen recording|video|before and after",
    ),
    "change_type": (
        r"type of change|kind|category|type",
        r"\[[ xX]\] *(bug ?fix|feature|breaking|docs|refactor)|(bug ?fix|new feature)",
    ),
    "docs": (r"documentation|docs", r"documentation|docs"),
    "ai": (r"\bAI\b|\bLLM", r"\b(AI|LLM|Copilot|ChatGPT|Claude|generated by)\b"),
    "cla_dco": (
        r"\bCLA\b|\bDCO\b",
        r"\bCLA\b|\bDCO\b|contributor license|developer certificate|signed-off-by",
    ),
    "contributing_link": (None, r"contributing"),
    "alternatives": (
        r"alternatives?|trade-?offs?|why",
        r"alternatives? considered|trade-?offs?",
    ),
    "risk": (r"risk|impact|compat", r"\brisks?\b|backward|compatib"),
}
ISSUE_TEMPLATE = {
    "observed": (
        r"actual|observed|what happened|current (behaviou?r)?|describe the bug|bug description",
        r"what happened|actual (behaviou?r|result)|describe the (bug|issue|problem)",
    ),
    "expected": (
        r"expected",
        r"expected (behaviou?r|result|outcome)|what (did you )?expect",
    ),
    "repro": (
        r"reproduc|steps",
        r"steps to reproduce|reproduc|minimal (example|repro)|how to reproduce",
    ),
    "environment": (
        r"version|environment|platform|\bos\b|system|setup|config",
        r"\bos\b|operating system|environment|version|platform",
    ),
    "logs": (r"logs?|output|error", r"\blogs?\b|stack ?trace|error output"),
    "duplicates": (
        r"duplicate|search|existing|before",
        r"(search|checked|looked)[^.\n]{0,40}(existing|duplicate)|duplicate",
    ),
    "feature": (
        r"feature|proposal|motivation|use case|problem",
        r"feature request|use case|motivation|proposed solution",
    ),
}
DOC_KINDS = {
    "contributing": CONTRIBUTING,
    "security": SECURITY,
    "code_of_conduct": CODE_OF_CONDUCT,
    "agent": AGENT,
    "pr_template": PR_TEMPLATE,
    "issue_template": ISSUE_TEMPLATE,
}
AGENT_FILE = re.compile(
    r"^(agents?|claude|gemini|crush|ai|agent_instructions|agent-instructions|copilot-instructions"
    r"|\.cursorrules|\.clinerules|\.clauderules|CONVENTIONS)(\.md)?$",
    re.IGNORECASE,
)

# Release-body measures over the latest 10 releases per repository.
GENERATED_NOTES = re.compile(
    r"(?i)what'?s changed|\*\*full changelog\*\*|^\W*full changelog"
    r"|\bby @[\w-]+(\[bot\])? in (https://github\.com/\S+/pull/\d+|#\d+)",
    re.MULTILINE,
)
PR_REF = re.compile(r"(\(#\d+\)|#\d{1,6}\b|/pull/\d+)")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+")
RELEASE_ELEMENTS = {
    "breaking_change": r"(?im)^\W*(#+\s*)?(\W*)(breaking( changes?)?)\b(?!.{0,3}(none|n/a))|\bbreaking change[s]?\b(?! (policy))",
    "deprecations": r"(?i)\bdeprecat(ed|es|ion|ions|e)\b",
    "security_fixes": r"(?i)\bCVE-\d{4}-\d+|GHSA-[\w-]+|\bsecurity (fix|update|patch|advisory|vulnerabilit)|(fix|patch)(es|ed)? [^.\n]{0,40}vulnerab",
    "upgrade_steps": r"(?i)\b(upgrad(e|ing)|migrat(e|ion))\b[^.\n]{0,60}(run|must|need|should|set|replace|rename|update|use)|(run|must|need to|should)[^.\n]{0,40}\b(upgrad|migrat)",
}
DATED_HEADING = re.compile(
    r"(?m)^\W*#+.*?\d{4}-\d{2}-\d{2}|^\W*#+.*?\(\d{4}-\d{2}-\d{2}\)"
    r"|\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}"
    r"|^##? .*\b(20\d\d)\b"
)

# Commit measures.
FOOTER = re.compile(r"(?m)^BREAKING[ -]CHANGES?(\([^)]*\))?:\s*\S")
BANG = re.compile(r"^[a-z]+(\([^)]*\))?!: ", re.IGNORECASE)
AREA_PREFIX = re.compile(r"^[\w./-]+(, ?[\w./-]+)*: ")
TRAILERS = {
    "signed_off_by": re.compile(r"(?mi)^Signed-off-by:"),
    "co_authored_by": re.compile(r"(?mi)^Co-authored-by:"),
    "closes_or_fixes": re.compile(r"(?mi)^(closes|fixes|resolves)[: ]+(#|https?://)"),
    "pr_number_in_subject": re.compile(r"\(#\d+\)\s*$"),
}
SQUASH_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")

# Change-note instructions: an imperative verb up to 60 characters before a
# change-note noun, in CONTRIBUTING, an agent file or a PR template.
CHANGE_NOTE_ASK = re.compile(
    r"(add|write|include|create|update|provide|run)\b[^.\n]{0,60}\b"
    r"(changesets?|change ?log( entry| entries)?|release[- ]notes?|news ?fragments?|change ?notes?)",
    re.IGNORECASE,
)

# Name groups at the root, in `.github/` and in `docs/`: (pattern, entry type, locations).
EXT = r"(\.(md|mdx|markdown|rst|adoc|txt))?"
NAME_GROUPS = {
    "NOTICE": (r"^notice" + EXT + "$", "file", None),
    "AI_POLICY / AGENT_POLICY": (
        r"^(ai[-_]?policy|agent[-_]?policy)" + EXT + "$",
        "file",
        None,
    ),
    "ADOPTERS": (r"^adopters" + EXT + "$", "file", None),
    "RELEASE / RELEASING": (r"^releas(e|ing)" + EXT + "$", "file", None),
    ".github/release.yml": (r"^release\.ya?ml$", "file", [".github/"]),
    "docs/releases (folder or file)": (r"^releases?" + EXT + "$", None, ["docs/"]),
    "DEVELOPMENT / HACKING / DEVELOPING": (
        r"^(development|hacking|developing|developer[-_]?guide)" + EXT + "$",
        "file",
        None,
    ),
    "BUILD / BUILDING": (r"^build(ing)?" + EXT + "$", "file", None),
    "INSTALL / INSTALLATION": (r"^install(ation)?" + EXT + "$", "file", None),
    "GETTING_STARTED (page)": (r"^getting[-_]started" + EXT + "$", "file", None),
    "GETTING_STARTED (folder)": (r"^getting[-_]started$", "dir", None),
    "FAQ": (r"^faq" + EXT + "$", None, None),
    "TROUBLESHOOTING": (r"^troubleshoot(ing)?" + EXT + "$", None, None),
    "TESTING": (r"^testing" + EXT + "$", "file", None),
    "CLA": (r"^cla" + EXT + "$", "file", None),
    "DCO": (r"^dco" + EXT + "$", "file", None),
    "REVIEW / REVIEWING": (r"^review(ing)?" + EXT + "$", "file", None),
    "SECURITY_CONTACTS": (r"^security[-_]contacts" + EXT + "$", "file", None),
    "SECURITY-CREDITS": (r"^security[-_]credits" + EXT + "$", "file", None),
    "OWNERS_ALIASES": (r"^owners_aliases$", "file", None),
    "TRADEMARK": (r"^trademarks?" + EXT + "$", "file", None),
    "PRIVACY": (r"^privacy" + EXT + "$", "file", None),
    "LICENSING / THIRD_PARTY_*": (
        r"^(licensing|third[-_]party[-_]\w+)" + EXT + "$",
        "file",
        None,
    ),
    "LICENSING / THIRD_PARTY_* (with JSON)": (
        r"^(licensing|third[-_]party[-_]\w+)(\.(md|mdx|markdown|rst|adoc|txt|json))?$",
        "file",
        None,
    ),
    "TRANSLATIONS": (r"^translat\w+" + EXT + "$", "file", None),
    "README in other languages": (
        r"^readme[-_.](zh|ja|ko|fr|de|es|pt|ru)\w*" + EXT + "$",
        "file",
        None,
    ),
    "TODO / PROGRESS / MAINTENANCE": (
        r"^(todo|progress|maintenance|project[_-]status)" + EXT + "$",
        "file",
        None,
    ),
    "PROPOSAL-*": (r"^proposal[-_]", "file", None),
    "llms.txt / llms-full.txt": (r"^llms(-full)?\.(txt|md)$", "file", None),
    "GEMINI.md / other agent-tool names": (r"^(gemini|crush|qwen)\.md$", "file", None),
    "docs/superpowers": (r"^superpowers$", "dir", ["docs/"]),
    "docs/plans": (r"^plans$", "dir", ["docs/"]),
    "docs/specs or spec": (r"^specs?$", "dir", ["docs/", "/"]),
    "design / designs dir (root or docs/)": (r"^designs?$", "dir", ["docs/", "/"]),
    "proposal(s) dir (root or docs/)": (r"^proposals?$", "dir", ["docs/", "/"]),
    "docs/adr or adrs": (r"^adrs?$", "dir", ["docs/"]),
    "docs/internal": (r"^internal$", "dir", ["docs/"]),
    "docs/codebase": (r"^codebase$", "dir", ["docs/"]),
    "docs/blog": (r"^blog$", "dir", ["docs/"]),
    "docs/guides or guide": (r"^guides?$", "dir", ["docs/"]),
    "docs/tutorials or tutorial": (r"^tutorials?$", "dir", ["docs/"]),
    "docs/reference(s)": (r"^references?$", "dir", ["docs/"]),
    "docs/how-to": (r"^how-?to" + EXT + "$", None, ["docs/"]),
    "docs/explanation or concepts": (r"^(explanation|concepts)$", "dir", ["docs/"]),
    "docs/api (dir or file)": (r"^api" + EXT + "$", None, ["docs/"]),
    "docs/architecture (dir or file)": (r"^architecture" + EXT + "$", None, ["docs/"]),
    "docs/security (dir or file)": (r"^security" + EXT + "$", None, ["docs/"]),
    "docs translations (language dirs)": (
        r"^(zh|zh-cn|zh-tw|ja|ko|fr|de|es|pt-br|ru)$",
        "dir",
        ["docs/"],
    ),
    ".github/DISCUSSION_TEMPLATE": (r"^discussion_template$", "dir", [".github/"]),
    ".github/instructions": (r"^instructions$", "dir", [".github/"]),
    ".github/workflows": (r"^workflows$", "dir", [".github/"]),
    ".github/actions": (r"^actions$", "dir", [".github/"]),
    ".changeset": (r"^\.changeset$", "dir", ["/"]),
    "CONDUCT": (r"^conduct" + EXT + "$", "file", None),
    "GRAMMAR": (r"^grammar" + EXT + "$", "file", None),
    "BENCHMARKS": (r"^benchmarks?" + EXT + "$", "file", None),
    "TOB / TSC": (r"^(tob|tsc)" + EXT + "$", "file", None),
    "VERSION": (r"^version$", "file", None),
    "REQUIREMENTS (txt)": (r"^requirements[-\w]*\.txt$", "file", None),
}
DOC_LIKE = re.compile(r"\.(md|mdx|markdown|rst|adoc|txt|org)$", re.IGNORECASE)
CAPS_NAME = re.compile(r"^[A-Z][A-Z0-9_.-]{2,}$")

# File-tree rules.
PROPOSAL_FOLDERS = re.compile(
    r"^(proposals?/|docs/proposals?/|Documentation/proposals/|design/|docs/designs?/|rfcs/"
    r"|docs/enhancements/|geps/|engdocs/design/|beps/)",
    re.IGNORECASE,
)
ADR_FOLDERS = re.compile(r"(^|/)(adrs?|architecture[- ]decisions)/", re.IGNORECASE)
FOLDER_INDEX = re.compile(r"^(readme|_?index|template|overview)\b", re.IGNORECASE)
SUBFOLDER_README = re.compile(
    r"^readme(\.(md|mdx|rst|txt|markdown|adoc|org))?$", re.IGNORECASE
)
SUBFOLDER_SKIP = re.compile(r"(^|/)(docs?|examples?|tests?|templates?)/", re.IGNORECASE)
VENDORED = re.compile(
    r"(^|/)(vendor|vendored|third[_-]?party|thirdparty|node_modules|pods|carthage|bower_components)/",
    re.IGNORECASE,
)
LOCALE_COPY = re.compile(
    r"(^|/)(locales?|i18n|l10n|translations?)/[a-z]{2}([-_][a-z]{2,4})?/", re.IGNORECASE
)
ARCHITECTURE_SKIP = re.compile(
    r"(^|/)(\.agents|\.claude|\.cursor|skills|optional-skills|agents|tests?|\.changeset|i18n)(/|$)"
    r"|(^|/)(ar|cs|de|es|fr|it|ja|ko|pt|ru|tr|zh|zh-Hans|zh-CN)(/|$)",
    re.IGNORECASE,
)
TREE_NAMES = {
    "runbook": r"(^|/)runbooks?[/.]",
    "postmortem_or_incident": r"(^|/)(post-?mortems?|incidents?)[/.-]",
    "glossary": r"(^|/)glossary[/.]",
    "faq": r"(^|/)faqs?[/.]",
    "troubleshooting": r"(^|/)troubleshooting[/.]",
    "getting_started_or_onboarding": r"(^|/)(getting[-_]started|onboarding)",
    "tutorials": r"(^|/)tutorials?[/.]",
    "api_reference": r"api[-_ ]?ref",
    "settings_reference": r"(^|/)(configuration|config|settings|options|reference)[/.]",
    "versioned_docs": r"(^|/)(versioned_docs|versions)/"
    r"|(^|/)(docs?|documentation|website|site|content|public)/(.*/)?(v\d+(\.\d+)*(\.x)?|\d+\.\d+(\.x)?)/",
}

# Term occurrences in README, CONTRIBUTING, SECURITY, PR template, agent file
# and release-note text, with code blocks, HTML and links removed.
TERMS = {
    "change": r"\bchang(e|es|ed|ing)\b",
    "release": r"\breleas(e|es|ed|ing)\b",
    "version": r"\bversions?\b",
    "user": r"\busers?\b",
    "maintainer": r"\bmaintainers?\b",
    "contributor": r"\bcontributors?\b",
}

# The 2026-10-03 reading sample: per stratum, richest documentation first.
RICHNESS_KEYS = (
    "contributing",
    "security",
    "changelog",
    "agents",
    "code_of_conduct",
    "decisions_dir",
    "architecture",
    "governance",
    "pr_template",
    "docs_dir",
)
LANGUAGES = ("TypeScript", "Go", "Python", "Rust", "JavaScript", "Swift")


@dataclass
class Corpus:
    """The raw data folder, loaded."""

    root: Path
    min_stars: int
    stars: list = field(default_factory=list)
    repos: list = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    trees: dict = field(default_factory=dict)
    labels: Path | None = None

    def readme(self, full):
        path = self.root / "readmes" / f"{corpus_fetch.slug(full)}.md"
        return path.read_text(errors="replace") if path.exists() else ""

    def saved(self, full, path, symlinks=False):
        """Text of a saved file, or None.

        Symbolic links count only with `symlinks=True`, as in the 2026-10-08 run.
        """
        entry = self.manifest.get(full, {}).get(path)
        kinds = ("file", "symlink") if symlinks else ("file",)
        if not entry or entry.get("type") not in kinds or "saved" not in entry:
            return None
        target = self.root / "files" / corpus_fetch.slug(full) / entry["saved"]
        return target.read_text(errors="replace") if target.exists() else None

    def optional(self, name):
        """A label file from the labels folder, else from the raw data folder."""
        for folder in (self.labels, self.root):
            if folder is not None and (folder / name).exists():
                return folder / name
        return None


def load(root, min_stars=3000, labels=None):
    root = Path(root)
    data = Corpus(root=root, min_stars=min_stars, labels=labels and Path(labels))
    stars_file = root / "stars-all.jsonl"
    if stars_file.exists():
        data.stars = [json.loads(line) for line in stars_file.open()]
    repos = [json.loads(p.read_text()) for p in sorted((root / "repos").glob("*.json"))]
    data.repos = [r for r in repos if r["stars"] >= min_stars]
    if (root / "manifest.json").exists():
        data.manifest = json.loads((root / "manifest.json").read_text())
    for r in data.repos:
        path = root / "trees" / f"{corpus_fetch.slug(r['full_name'])}.json"
        if path.exists():
            data.trees[r["full_name"]] = json.loads(path.read_text())
    return data


def ranked(counter):
    """Counts, most first; ties in key order, so output stays the same across runs."""
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def subjects(record):
    return [m.splitlines()[0] if m else "" for m in record["commits"]["messages"]]


def mostly_conventional(record):
    subs = subjects(record)
    return (
        bool(subs)
        and sum(bool(corpus_fetch.CONVENTIONAL.match(s)) for s in subs) / len(subs)
        >= 0.5
    )


def listing(record, where):
    return record["listing"].get(where, [])


# Corpus and prevalence


def before_run(row, earlier_run):
    """True for a repository starred before the earlier run.

    A repository list sets `first_pass`; a star list gives `starred_at`.
    """
    if "first_pass" in row:
        return bool(row["first_pass"])
    return (row.get("starred_at") or "") <= earlier_run


def corpus_counts(data, earlier_run=None):
    big = [r for r in data.stars if r["stars"] >= data.min_stars]
    languages = Counter(r.get("language") or "none" for r in data.repos)
    top3 = sum(n for _, n in languages.most_common(3))
    out = {
        "starred": len(data.stars),
        "corpus": len(data.repos),
        "corpus_in_star_list": len(big),
        "median_stars": median(r["stars"] for r in data.repos),
        "min_stars": min(r["stars"] for r in data.repos),
        "max_stars": max(r["stars"] for r in data.repos),
        "archived": sum(bool(r.get("archived")) for r in data.repos),
        "forks": sum(bool(r.get("fork")) for r in data.repos),
        "languages": ranked(languages),
        "top_three_language_share": round(top3 / len(data.repos), 2),
        "licenses": ranked(Counter(r.get("license") for r in data.repos)),
    }
    if earlier_run:
        out["starred_after_earlier_run"] = sorted(
            r["full_name"] for r in big if not before_run(r, earlier_run)
        )
    return out


def section_kind(heading):
    text = re.sub(
        r"[`*_\[\]()!:]|<[^>]+>|https?://\S+|[^\w\s.-]", " ", heading.lower()
    ).strip()
    for name, pattern in SECTIONS:
        if re.search(pattern, text):
            return name
    return None


def prevalence(data):
    files = Counter(k for r in data.repos for k in r.get("files", {}))
    sections = Counter()
    for r in data.repos:
        kinds = {section_kind(h) for h in (r.get("readme") or {}).get("headings", [])}
        sections.update(kinds - {None})
    badges = {
        r["full_name"]: len(BADGE.findall(data.readme(r["full_name"])))
        for r in data.repos
    }
    contents = sum(
        any(
            re.search(
                r"^(table of )?contents$", re.sub(r"[^\w\s]", "", h).strip().lower()
            )
            for h in (r.get("readme") or {}).get("headings", [])
        )
        for r in data.repos
    )
    mentions = {
        key: sorted(
            r["full_name"]
            for r in data.repos
            if re.search(rx, data.readme(r["full_name"]), re.IGNORECASE)
        )
        for key, rx in README_MENTIONS.items()
    }
    semver = sorted(
        r["full_name"]
        for r in data.repos
        if re.search(
            SEMVER,
            data.readme(r["full_name"])
            + "\n".join(b["body"] or "" for b in r["releases"].get("bodies") or []),
            re.IGNORECASE,
        )
    )
    return {
        "files": ranked(files),
        "readme_sections": ranked(sections),
        "readme_bytes_median": median(
            (r.get("readme") or {}).get("bytes", 0) for r in data.repos
        ),
        "repos_with_badges": sum(v > 0 for v in badges.values()),
        "badge_images": sum(badges.values()),
        "badges_median": median(badges.values()),
        "readme_contents_heading": contents,
        "readme_mentions": {
            k: {"repos": len(v), "names": v} for k, v in mentions.items()
        },
        "semantic_versioning_in_readme_or_release_notes": len(semver),
        "codeowners_and_maintainers": sum(
            "codeowners" in r["files"] and "maintainers" in r["files"]
            for r in data.repos
        ),
        "codeowners_or_maintainers": sum(
            "codeowners" in r["files"] or "maintainers" in r["files"]
            for r in data.repos
        ),
        "roadmap_files_saved": sum(
            data.saved(r["full_name"], p) is not None
            for r in data.repos
            for p in r["files"].get("roadmap", [])
        ),
    }


# Releases and change notes


def releases(data):
    substantive = {
        r["full_name"]
        for r in data.repos
        if any(b > 200 for b in r["releases"]["bodies_chars"])
    }
    changelog = {r["full_name"] for r in data.repos if "changelog" in r["files"]}
    per_repo = {}
    for r in data.repos:
        c = Counter()
        for body in r["releases"].get("bodies") or []:
            text = body["body"] or ""
            c["releases"] += 1
            if len(text.strip()) < 20:
                c["empty"] += 1
                continue
            if GENERATED_NOTES.search(text):
                c["generated"] += 1
            items = [line for line in text.splitlines() if LIST_ITEM.match(line)]
            if sum(bool(PR_REF.search(line)) for line in items) >= 3:
                c["pr_refs"] += 1
        per_repo[r["full_name"]] = c

    def repos_where(test):
        return sorted(k for k, c in per_repo.items() if test(c))

    def nonempty(c):
        return c["releases"] - c["empty"]

    elements = {}
    for key, rx in RELEASE_ELEMENTS.items():
        elements[key] = sum(
            any(
                re.search(rx, b["body"] or "")
                for b in r["releases"].get("bodies") or []
            )
            for r in data.repos
        )
    dated = 0
    read = 0
    for r in data.repos:
        texts = [data.saved(r["full_name"], p) for p in r["files"].get("changelog", [])]
        texts = [t for t in texts if t is not None]
        read += len(texts)
        dated += any(DATED_HEADING.search(t) for t in texts)
    return {
        "notes_over_200_characters": len(substantive),
        "changelog_file": len(changelog),
        "both": len(substantive & changelog),
        "notes_only": len(substantive - changelog),
        "file_only": len(changelog - substantive),
        "either": len(substantive | changelog),
        "repos_with_any_release": len(repos_where(lambda c: c["releases"] > 0)),
        "repos_with_a_nonempty_release": len(repos_where(lambda c: nonempty(c) > 0)),
        "repos_any_generated": len(repos_where(lambda c: c["generated"] > 0)),
        "repos_mostly_generated": len(
            repos_where(lambda c: nonempty(c) > 0 and c["generated"] * 2 > nonempty(c))
        ),
        "repos_any_pr_refs": len(repos_where(lambda c: c["pr_refs"] > 0)),
        "repos_mostly_pr_refs": len(
            repos_where(lambda c: nonempty(c) > 0 and c["pr_refs"] * 2 > nonempty(c))
        ),
        "releases": sum(c["releases"] for c in per_repo.values()),
        "releases_empty": sum(c["empty"] for c in per_repo.values()),
        "releases_generated": sum(c["generated"] for c in per_repo.values()),
        "releases_pr_refs": sum(c["pr_refs"] for c in per_repo.values()),
        "elements_repos": elements,
        "changelog_files_read": read,
        "changelog_repos_with_dated_heading": dated,
        "_mostly_pr_refs": repos_where(
            lambda c: nonempty(c) > 0 and c["pr_refs"] * 2 > nonempty(c)
        ),
    }


def note_text(line):
    """Normalise a release line or a PR title for comparison."""
    s = re.sub(r"\bby @[\w\[\]-]+ in (https://github\.com/\S+|#\d+)", "", line)
    s = re.sub(r"\[#?\d+\]\([^)]*\)|\(#\d+\)|https?://\S+|#\d+", "", s)
    s = re.sub(r"[*_`\[\]]|^\W+", "", s)
    s = re.sub(
        r"^(feat|fix|docs|chore|refactor|perf|test|build|ci|style|revert)(\([^)]*\))?!?:\s*",
        "",
        s,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", s).strip().lower().rstrip(".")


def line_matches_title(check):
    """True when the line equals the PR title, the line contains the title, or the title contains the line.

    The 2026-10-08 gather stored the match result in each record. The gather
    compared the full line, then stored only the first 200 characters of the line.
    """
    if "equal" in check:
        return (
            check["equal"]
            or check["line_contains_title"]
            or check["title_contains_line"]
        )
    item = corpus_fetch.LIST_LINE.match(check["line"])
    line = note_text(item.group(2) if item else check["line"])
    title = note_text(check["title"])
    return (
        line == title
        or (bool(title) and title in line)
        or (bool(line) and line in title)
    )


def pr_titles(data):
    path = data.optional(corpus_fetch.PR_TITLES)
    if not path:
        return None
    stored = json.loads(path.read_text())
    lines = resolved = matched = repos = majority = 0
    for entry in stored.values():
        checks = entry["checked"]
        lines += len(checks)
        ok = [c for c in checks if "error" not in c]
        if not ok:
            continue
        hits = sum(line_matches_title(c) for c in ok)
        resolved += len(ok)
        matched += hits
        repos += 1
        majority += hits * 2 > len(ok)
    return {
        "lines_checked": lines,
        "lines_resolved_to_a_pr": resolved,
        "lines_equal_or_containing_title": matched,
        "repos_checked": repos,
        "repos_mostly_title_lines": majority,
    }


def change_note_tools(data, mostly_pr_refs):
    hits = defaultdict(set)
    for r in data.repos:
        full = r["full_name"]
        root = {n.lower(): t for n, t in listing(r, "/")}
        docs = {n.lower(): t for n, t in listing(r, "docs/")}
        github = {n.lower() for n, _ in listing(r, ".github/")}
        workflows = [w.lower() for w in data.trees.get(full, {}).get("workflows", [])]
        if ".changeset" in root:
            hits["changeset"].add(full)
        if any(
            root.get(n) == "dir" or docs.get(n) == "dir"
            for n in ("changelog.d", "newsfragments", "news", "changes")
        ):
            hits["towncrier_style_folder"].add(full)
        if "releasenotes" in root:
            hits["reno"].add(full)
        if github & {"release.yml", "release.yaml"}:
            hits["release_yml"].add(full)
        if any("release-drafter" in x for x in github) or any(
            "release-drafter" in w for w in workflows
        ):
            hits["release_drafter"].add(full)
        if any(
            x.startswith("release-please") or x == ".release-please-manifest.json"
            for x in root
        ) or any("release-please" in w for w in workflows):
            hits["release_please"].add(full)
        if "cliff.toml" in root or any("cliff" in w for w in workflows):
            hits["git_cliff"].add(full)
        if any(x.startswith((".releaserc", "release.config.")) for x in root) or any(
            "semantic-release" in w for w in workflows
        ):
            hits["semantic_release"].add(full)
    note_files = hits["changeset"] | hits["towncrier_style_folder"] | hits["reno"]
    every_tool = set().union(*hits.values())
    return {
        "tools": {
            k: {"repos": len(v), "names": sorted(v)} for k, v in sorted(hits.items())
        },
        "note_file_tools": len(note_files),
        "mostly_pr_refs_or_note_file_tool": len(note_files | set(mostly_pr_refs)),
        "mostly_pr_refs_or_any_named_tool": len(every_tool | set(mostly_pr_refs)),
    }


# Commits and pull requests


def commits(data):
    total = Counter()
    repos = defaultdict(set)
    for r in data.repos:
        for message in r["commits"]["messages"]:
            subject = message.splitlines()[0] if message else ""
            total["commits"] += 1
            total["with_body"] += "\n" in message and bool(
                message.split("\n", 1)[1].strip()
            )
            if FOOTER.search(message):
                total["footer"] += 1
                repos["footer"].add(r["full_name"])
            if BANG.match(subject):
                total["bang"] += 1
                repos["bang"].add(r["full_name"])
            if re.search(r"(?i)\bbreaking\b", message):
                total["breaking_word"] += 1
                repos["breaking_word"].add(r["full_name"])
            for key, rx in TRAILERS.items():
                if rx.search(message):
                    total[key] += 1
                    repos[key].add(r["full_name"])
    conventional = [r for r in data.repos if mostly_conventional(r)]
    area = [
        r
        for r in data.repos
        if not mostly_conventional(r)
        and subjects(r)
        and sum(
            bool(AREA_PREFIX.match(s)) and not corpus_fetch.CONVENTIONAL.match(s)
            for s in subjects(r)
        )
        / len(subjects(r))
        >= 0.5
    ]
    medians = [
        median(r["commits"]["subject_lengths"])
        for r in data.repos
        if r["commits"]["subject_lengths"]
    ]
    return {
        "commits": total["commits"],
        "share_with_body": round(total["with_body"] / max(1, total["commits"]), 2),
        "subject_length_median_of_medians": median(medians) if medians else None,
        "repos_mostly_conventional": len(conventional),
        "repos_mostly_area_prefix": len(area),
        "repos_neither": len(data.repos) - len(conventional) - len(area),
        "breaking_change_footers": {
            "commits": total["footer"],
            "repos": sorted(repos["footer"]),
        },
        "bang_markers": {"commits": total["bang"], "repos": sorted(repos["bang"])},
        "word_breaking": {
            "commits": total["breaking_word"],
            "repos": len(repos["breaking_word"]),
        },
        "trailers": {
            k: {"commits": total[k], "repos": len(repos[k])} for k in TRAILERS
        },
        "latest_100": commits_100(data),
    }


def commits_100(data):
    path = data.optional(corpus_fetch.COMMITS_100)
    if path:
        stored = json.loads(path.read_text())
        footers, bangs = Counter(), Counter()
        for full, messages in stored.items():
            for m in messages:
                footers[full] += bool(FOOTER.search(m))
                bangs[full] += bool(BANG.match(m.splitlines()[0] if m else ""))
        return {
            "repos": len(stored),
            "commits": sum(len(v) for v in stored.values()),
            "breaking_change_footers": sum(footers.values()),
            "footer_repos": sorted(k for k, v in footers.items() if v),
            "bang_markers": sum(bangs.values()),
            "bang_repos": sorted(k for k, v in bangs.items() if v),
        }
    # The 2026-10-08 gather stored only totals, in `of2-commits100.json`.
    path = data.optional("of2-commits100.json")
    if not path:
        return None
    stored = json.loads(path.read_text())
    return {
        "repos": stored["repos"],
        "commits": stored["commits"],
        "breaking_change_footers": stored["BREAKING_CHANGE_footers"],
        "footer_repos": stored["footer_repos"],
        "bang_markers": stored["bang_marker_commits"],
        "bang_repos": stored["bang_marker_repos"],
    }


def pulls(data):
    sampled = [r for r in data.repos if r["pulls"]["sampled"]]
    described = sum(
        median(r["pulls"]["body_chars"]) > 200
        for r in sampled
        if r["pulls"]["body_chars"]
    )
    human = 0
    for r in sampled:
        bodies = [
            len(i.get("body") or "")
            for i in r["pulls"].get("items") or []
            if i.get("author_type") == "User"
        ]
        human += bool(bodies) and median(bodies) > 200
    squash = copies = 0
    for r in data.repos:
        prs = {
            i["number"]: i
            for i in r["pulls"].get("items") or []
            if i.get("author_type") == "User"
        }
        matched = copied = False
        for message in r["commits"]["messages"]:
            found = SQUASH_SUBJECT.search(message.splitlines()[0] if message else "")
            if not found or int(found.group(1)) not in prs:
                continue
            matched = True
            body = re.sub(
                r"\s+", " ", message.split("\n", 1)[1] if "\n" in message else ""
            )
            pr_lines = [
                re.sub(r"\s+", " ", x).strip()
                for x in (prs[int(found.group(1))]["body"] or "").splitlines()
            ]
            copied = copied or any(len(x) >= 20 and x in body for x in pr_lines)
        squash += matched
        copies += copied
    return {
        "repos_sampled": len(sampled),
        "repos_median_body_over_200": described,
        "repos_median_human_body_over_200": human,
        "repos_squash_merging_human_prs": squash,
        "repos_where_a_squash_commit_copies_the_pr_body": copies,
        "repos_with_pr_template": sum("pr_template" in r["files"] for r in data.repos),
    }


# Saved documents


def headings(text):
    atx = [h.strip(" #*_`") for h in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text)]
    setext = [m.group(1).strip() for m in re.finditer(r"(?m)^(.+)\n[=-]{3,}\s*$", text)]
    return atx + setext


def is_pointer(text):
    body = re.sub(r"(?m)^\s*#.*$", "", text)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    words = len(
        re.findall(r"\w+", re.sub(r"https?://\S+|\[[^\]]*\]\([^)]*\)", " ", body))
    )
    return (
        len(text.encode()) < 700
        and bool(re.search(r"https?://|\]\(", text))
        and words < 60
    )


def flags(text, rules):
    hs = headings(text)
    out = {}
    for name, (heading_rx, body_rx) in rules.items():
        in_heading = bool(heading_rx) and any(
            re.search(heading_rx, h, re.IGNORECASE) for h in hs
        )
        in_body = bool(body_rx) and bool(
            re.search(body_rx, text, re.IGNORECASE | re.MULTILINE)
        )
        out[name] = "H" if in_heading else ("B" if in_body else "")
    return out


def covenant_version(text):
    found = re.search(r"(?i)version[ \w]*?(\d\.\d)", text) or re.search(
        r"(?i)version/(\d)/(\d)", text
    )
    if not found:
        return None
    return (
        found.group(1) if found.lastindex == 1 else f"{found.group(1)}.{found.group(2)}"
    )


def document_flags(data):
    """Per-file element flags for the six document kinds, keyed `repo:path`."""
    out = defaultdict(dict)
    by_name = {r["full_name"]: r for r in data.repos}
    for full, entries in data.manifest.items():
        record = by_name.get(full)
        if record is None:
            continue
        for kind, key in (
            ("contributing", "contributing"),
            ("security", "security"),
            ("code_of_conduct", "code_of_conduct"),
        ):
            for path in record["files"].get(key, []):
                text = data.saved(full, path)
                if text is None:
                    continue
                row = {
                    "bytes": len(text.encode()),
                    "pointer": is_pointer(text),
                    "headings": headings(text)[:40],
                }
                row.update(flags(text, DOC_KINDS[kind]))
                if kind == "code_of_conduct":
                    row["version"] = covenant_version(text)
                out[kind][f"{full}:{path}"] = row
        for path, entry in entries.items():
            name = path.split("/")[-1]
            if entry.get("type") != "file" or "saved" not in entry:
                continue
            text = data.saved(full, path)
            if text is None:
                continue
            if AGENT_FILE.match(name) or name.endswith(".instructions.md"):
                row = {
                    "bytes": len(text.encode()),
                    "pointer": bool(
                        re.match(r"\s*(@|see |read |refer)", text, re.IGNORECASE)
                    )
                    or len(text) < 200,
                    "headings": headings(text)[:40],
                }
                row.update(flags(text, AGENT))
                out["agent"][f"{full}:{path}"] = row
            if re.search(
                r"(^|/)(pull_request_template(\.md)?|PULL_REQUEST_TEMPLATE/[^/]+)$",
                path,
                re.IGNORECASE,
            ):
                row = {"bytes": len(text.encode()), "headings": headings(text)[:30]}
                row.update(flags(text, PR_TEMPLATE))
                out["pr_template"][f"{full}:{path}"] = row
            if re.search(
                r"ISSUE_TEMPLATE/", path, re.IGNORECASE
            ) and not name.lower().startswith("config"):
                row = {
                    "bytes": len(text.encode()),
                    "form": name.lower().endswith((".yml", ".yaml")),
                    "headings": headings(text)[:20],
                }
                row.update(flags(text, ISSUE_TEMPLATE))
                out["issue_template"][f"{full}:{path}"] = row
    return out


def heading_vocabulary(rows, top=16):
    repos = defaultdict(set)
    for key, row in rows.items():
        for h in row["headings"]:
            repos[re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", h.lower())).strip()].add(
                key.split(":")[0]
            )
    ranked = sorted(
        ((len(v), h) for h, v in repos.items() if h), key=lambda x: (-x[0], x[1])
    )
    return [[h, n] for n, h in ranked[:top]]


def documents(data, doc_flags):
    summary = {}
    for kind, rows in doc_flags.items():
        by_repo = defaultdict(list)
        for key, row in rows.items():
            by_repo[key.split(":")[0]].append(row)
        s = {
            "files": len(rows),
            "repos": len(by_repo),
            "pointer_files": sum(row.get("pointer", False) for row in rows.values()),
            "flags": {
                flag: sum(any(row[flag] for row in fl) for fl in by_repo.values())
                for flag in DOC_KINDS[kind]
            },
            "headings": heading_vocabulary(rows),
        }
        if kind == "contributing":
            s["repos_only_pointer_files"] = sum(
                all(row["pointer"] for row in fl) for fl in by_repo.values()
            )
            s["repos_only_outside_root"] = sum(
                all("/" in p for p in r["files"]["contributing"])
                for r in data.repos
                if "contributing" in r["files"]
            )
        if kind == "code_of_conduct":
            versions = Counter(
                row["version"] for row in rows.values() if row["covenant"]
            )
            s["covenant_versions"] = {
                str(k): v
                for k, v in sorted(versions.items(), key=lambda kv: str(kv[0]))
            }
            s["covenant_1_x"] = sum(
                v for k, v in versions.items() if k and k.startswith("1.")
            )
            s["covenant_2_x"] = sum(
                v for k, v in versions.items() if k and k.startswith("2.")
            )
            s["covenant_3_x"] = sum(
                v for k, v in versions.items() if k and k.startswith("3.")
            )
        if kind == "issue_template":
            s["forms"] = sum(row["form"] for row in rows.values())
            s["markdown"] = sum(not row["form"] for row in rows.values())
        summary[kind] = s
    summary["issue_template_config"] = sum(
        any(
            re.search(r"issue_template/config\.ya?ml$", p, re.IGNORECASE)
            for p in entries
        )
        for full, entries in data.manifest.items()
    )
    ai_files = {
        r["full_name"]
        for r in data.repos
        if repos_with_name(r, NAME_GROUPS["AI_POLICY / AGENT_POLICY"])
    }
    ai_contributing = {
        k.split(":")[0] for k, row in doc_flags["contributing"].items() if row["ai"]
    }
    ai_template = {
        k.split(":")[0] for k, row in doc_flags["pr_template"].items() if row["ai"]
    }
    summary["ai_rules"] = {
        "policy_file": len(ai_files),
        "contributing": len(ai_contributing),
        "pr_template": len(ai_template),
        "any": len(ai_files | ai_contributing | ai_template),
    }
    asks = set()
    for kind in ("contributing", "agent", "pr_template"):
        for key, row in doc_flags[kind].items():
            full, path = key.split(":", 1)
            if CHANGE_NOTE_ASK.search(data.saved(full, path) or ""):
                asks.add(full)
    template_field = {
        k.split(":")[0]
        for k, row in doc_flags["pr_template"].items()
        if row["release_note"]
    }
    summary["change_note_asks"] = {
        "text": len(asks),
        "text_or_pr_template_field": len(asks | template_field),
    }
    return summary


def security_classes(data, doc_flags):
    path = data.optional("of2-security-channel.json")
    labels = json.loads(path.read_text())["files"] if path else {}
    order = ["named", "points_elsewhere", "placeholder", "not_a_policy", "unlabelled"]
    repos = {}
    for key, row in doc_flags["security"].items():
        label = labels.get(key) or ("named" if row["channel"] else "unlabelled")
        repo = key.split(":")[0]
        if repo not in repos or order.index(label) < order.index(repos[repo]):
            repos[repo] = label
    tally = Counter(repos.values())
    return {
        "labels_file": bool(path),
        "repos_by_class": ranked(tally),
        "reporting_policies": len(repos) - tally["not_a_policy"],
    }


def small_files(data):
    funding = Counter()
    for r in data.repos:
        for p in r["files"].get("funding", []):
            funding.update(
                set(
                    re.findall(
                        r"(?m)^\s*([a-z_]+)\s*:", data.saved(r["full_name"], p) or ""
                    )
                )
            )
    citation = Counter()
    citation_files = 0
    for r in data.repos:
        for p in r["files"].get("citation", []):
            citation_files += 1
            citation.update(
                re.findall(r"(?m)^([a-z-]+)\s*:", data.saved(r["full_name"], p) or "")
            )
    codeowners = {"repos": 0, "catch_all_line": 0}
    for r in data.repos:
        for p in r["files"].get("codeowners", []):
            text = data.saved(r["full_name"], p)
            if text is None:
                continue
            codeowners["repos"] += 1
            lines = [
                x
                for x in text.splitlines()
                if x.strip() and not x.strip().startswith("#")
            ]
            codeowners["catch_all_line"] += any(x.split()[0] == "*" for x in lines)
            break
    approval = {
        r["full_name"]
        for r in data.repos
        if "codeowners" in r["files"]
        or any(
            re.match(r"^owners(\.ya?ml)?$", n, re.IGNORECASE) and t != "dir"
            for w in corpus_fetch.LOCATIONS
            for n, t in listing(r, w)
        )
    }
    maintainers = Counter()
    for r in data.repos:
        for p in r["files"].get("maintainers", []):
            text = data.saved(r["full_name"], p)
            if text is None:
                continue
            maintainers["files"] += 1
            maintainers["with_address_or_handle"] += bool(
                re.search(r"@[\w-]+|[\w.+-]+@[\w-]+\.\w+", text)
            )
            maintainers["with_emeritus_or_former"] += bool(
                re.search(r"(?i)emerit|former|alumni|retired", text)
            )
            maintainers["with_area"] += bool(
                re.search(
                    r"(?i)\|\s*(area|component|responsibilit|focus)|owns?\b|area", text
                )
            )
    license_files = copyright_lines = 0
    for r in data.repos:
        paths = r["files"].get("license", [])
        text = data.saved(r["full_name"], paths[0]) if paths else None
        if text is None:
            continue
        license_files += 1
        copyright_lines += bool(
            re.search(r"(?i)copyright\s*(\(c\)|©)?\s*(\d{4}|\[?\d{4})(?!\s*\])", text)
        )
    governance = Counter()
    governance_files = 0
    governance_rules = {
        "roles": r"(?i)\b(roles?|maintainers?|committers?|steering)\b",
        "decision_rule": r"(?i)(voting|consensus|lazy consensus|majority|vote)",
        "amend": r"(?i)(amend|change(s)? to this|modif(y|ication) of (this )?governance)",
        "pointer": r"(?i)(published|maintained) at|can be found in|dedicated repository",
    }
    for r in data.repos:
        for p in r["files"].get("governance", []):
            text = data.saved(r["full_name"], p)
            if text is None:
                continue
            governance_files += 1
            governance.update(
                k for k, rx in governance_rules.items() if re.search(rx, text)
            )
    return {
        "funding_keys": ranked(funding),
        "citation_files": citation_files,
        "citation_keys": ranked(citation),
        "codeowners": codeowners,
        "codeowners_or_owners_file": len(approval),
        "maintainers": ranked(maintainers),
        "maintainers_repos": sum("maintainers" in r["files"] for r in data.repos),
        "credits_repos": sum("credits" in r["files"] for r in data.repos),
        "license_files": license_files,
        "license_copyright_line": copyright_lines,
        "governance_files": governance_files,
        "governance": ranked(governance),
    }


def agent_files(data):
    names = {
        "AGENTS.md": r"^agents\.md$",
        "CLAUDE.md": r"^claude\.md$",
        "GEMINI.md": r"^gemini\.md$",
        "copilot-instructions.md": r"^copilot-instructions\.md$",
        ".cursorrules": r"^\.cursorrules$",
        ".clauderules": r"^\.clauderules$",
        ".windsurfrules": r"^\.windsurfrules$",
        "CRUSH.md": r"^crush\.md$",
        "AGENT.md": r"^agent\.md$",
        "AGENT_INSTRUCTIONS.md": r"^agent_instructions\.md$",
        "AI.md": r"^ai\.md$",
        "AGENT_POLICY.md": r"^agent_policy\.md$",
        "SKILLS.md": r"^skills\.md$",
        "QWEN.md": r"^qwen\.md$",
        "CONVENTIONS.md": r"^conventions\.md$",
    }
    folders = {
        ".claude": r"^\.claude$",
        ".agents": r"^\.agents?$",
        ".cursor": r"^\.cursor$",
        ".codex": r"^\.codex$",
        ".gemini": r"^\.gemini$",
        ".roo": r"^\.roo$",
        ".clinerules": r"^\.clinerules$",
        ".cline": r"^\.cline$",
        ".opencode": r"^\.opencode$",
        "skills": r"^skills$",
        ".claude-plugin": r"^\.claude-plugin$",
        ".windsurf": r"^\.windsurf$",
        ".zed": r"^\.zed$",
        ".ai": r"^\.ai$",
    }
    by_name = defaultdict(set)
    for r in data.repos:
        for entries in r["listing"].values():
            for n, t in entries:
                for label, rx in names.items():
                    if re.match(rx, n, re.IGNORECASE) and t != "dir":
                        by_name[label].add(r["full_name"])
    tool = defaultdict(set)
    for r in data.repos:
        root_dirs = {n for n, t in listing(r, "/") if t == "dir"}
        github_dirs = {n for n, t in listing(r, ".github/") if t == "dir"}
        for label, rx in folders.items():
            if any(re.match(rx, n, re.IGNORECASE) for n in root_dirs):
                tool[label].add(r["full_name"])
        if "instructions" in github_dirs:
            tool[".github/instructions"].add(r["full_name"])
        if "agents" in github_dirs:
            tool[".github/agents"].add(r["full_name"])
    agents, claude, copilot = (
        by_name["AGENTS.md"],
        by_name["CLAUDE.md"],
        by_name["copilot-instructions.md"],
    )
    any_file = set().union(*by_name.values())
    tool_kinds = [
        k for k in tool if k not in ("skills", ".claude-plugin", ".zed", ".ai")
    ]
    any_tool = any_file | set().union(*(tool[k] for k in tool_kinds))
    pointer = Counter()
    for full in sorted(agents & claude):
        texts = {}
        for p, entry in data.manifest.get(full, {}).items():
            if p.lower() in ("claude.md", "agents.md") and entry.get("saved"):
                texts[p.lower()] = data.saved(full, p, symlinks=True)
        tc, ta = texts.get("claude.md"), texts.get("agents.md")
        if tc is None or ta is None:
            continue
        if tc.strip() == ta.strip():
            pointer["identical"] += 1
        elif len(tc) < 400 and re.search(r"agents\.md", tc, re.IGNORECASE):
            pointer["claude_points_to_agents"] += 1
        elif len(ta) < 400 and re.search(r"claude\.md", ta, re.IGNORECASE):
            pointer["agents_points_to_claude"] += 1
    return {
        "repos_by_file_name": {
            k: len(v)
            for k, v in sorted(by_name.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        },
        "tool_folders": {
            k: len(v)
            for k, v in sorted(tool.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        },
        "agents_claude_or_copilot": len(agents | claude | copilot),
        "any_named_file": len(any_file),
        "any_named_file_or_tool_folder": len(any_tool),
        "agents_and_claude": len(agents & claude),
        "agents_only": len(agents - claude),
        "claude_only": len(claude - agents),
        "agents_claude_and_copilot": len(agents & claude & copilot),
        "pointer_checks": ranked(pointer),
    }


# Names and trees


def name_inventory(data):
    """Every (location, name) pair at the three locations, most repos first."""
    repos = defaultdict(set)
    types = {}
    matched = set()
    for r in data.repos:
        for where, entries in r["listing"].items():
            for name, kind in entries:
                repos[(where, name)].add(r["full_name"])
                types[(where, name)] = kind
                if any(
                    re.search(p, name, re.IGNORECASE)
                    for p in corpus_fetch.PATTERNS.values()
                ):
                    matched.add((where, name))
    keys = sorted(repos, key=lambda k: (-len(repos[k]), k))
    return [
        {
            "location": k[0],
            "name": k[1],
            "type": types[k],
            "repos": len(repos[k]),
            "matched": k in matched,
        }
        for k in keys
    ]


def repos_with_name(record, group):
    pattern, kind, locations = group
    found = []
    for where, entries in record["listing"].items():
        if locations and where not in locations:
            continue
        for n, t in entries:
            if re.match(pattern, n, re.IGNORECASE) and (
                kind is None
                or t == kind
                or (kind == "file" and t in ("file", "symlink"))
            ):
                found.append(where + n)
    return found


def names(data):
    rows = name_inventory(data)
    unmatched = [r for r in rows if not r["matched"]]
    stems = {
        DOC_LIKE.sub("", r["name"]).lower()
        for r in unmatched
        if r["type"] == "file"
        and (DOC_LIKE.search(r["name"]) or CAPS_NAME.match(r["name"]))
    }
    groups = {}
    for label, group in NAME_GROUPS.items():
        hits = {r["full_name"]: repos_with_name(r, group) for r in data.repos}
        hits = {k: v for k, v in hits.items() if v}
        groups[label] = {
            "repos": len(hits),
            "paths": sum(len(v) for v in hits.values()),
        }
    dev = NAME_GROUPS["DEVELOPMENT / HACKING / DEVELOPING"]
    linked = total = 0
    for r in data.repos:
        found = repos_with_name(r, dev)
        if not found:
            continue
        total += 1
        texts = [
            data.saved(r["full_name"], p) or ""
            for p in r["files"].get("contributing", [])
        ]
        linked += any(
            re.search(re.escape(p.split("/")[-1]), t, re.IGNORECASE)
            for t in texts
            for p in found
        )
    docs_listing = sum(bool(listing(r, "docs/")) for r in data.repos)
    return {
        "pairs": len(rows),
        "matched_pairs": sum(r["matched"] for r in rows),
        "unmatched_pairs": len(unmatched),
        "entries_by_location": {
            w: sum(len(listing(r, w)) for r in data.repos)
            for w in corpus_fetch.LOCATIONS
        },
        "unmatched_document_stems": len(stems),
        "groups": groups,
        "contributing_names_development_document": {"repos": total, "linked": linked},
        "docs_folder": {
            "docs_dir_pattern": sum("docs_dir" in r["files"] for r in data.repos),
            "docs_listing": docs_listing,
            "with_second_level_folders": sum(
                bool(
                    data.manifest.get(r["full_name"], {})
                    .get("docs/__second_level", {})
                    .get("dirs")
                )
                for r in data.repos
            ),
        },
    }


def tree_repos(data, test):
    return sorted(
        full
        for full, tree in data.trees.items()
        if any(test(p) for p in tree.get("doc_paths", []))
    )


def proposal_folder(path):
    found = PROPOSAL_FOLDERS.match(path)
    return found.group(0) if found else None


def adr_folder(path):
    found = ADR_FOLDERS.search(path)
    return path[: found.end()] if found else None


def folder_member(path, folder):
    """True for a file inside the folder other than the folder's own README, index or template."""
    rest = path[len(folder) :]
    if "/" not in rest and FOLDER_INDEX.match(rest):
        return False
    return not re.search(r"template", rest, re.IGNORECASE)


def subfolder_readmes(data, narrow=True):
    out = {}
    for full, tree in data.trees.items():
        paths = [
            p
            for p in tree.get("doc_paths", [])
            if "/" in p
            and SUBFOLDER_README.match(p.rsplit("/", 1)[-1])
            and not SUBFOLDER_SKIP.search(p)
        ]
        if narrow:
            paths = [
                p for p in paths if not VENDORED.search(p) and not LOCALE_COPY.search(p)
            ]
        if paths:
            out[full] = paths
    return out


def architecture_files(data):
    out = {}
    for full, tree in data.trees.items():
        hits = [
            p
            for p in tree.get("doc_paths", [])
            if "architecture" in p.rsplit("/", 1)[-1].lower()
            and re.search(r"\.(md|mdx|rst)$", p, re.IGNORECASE)
            and not ARCHITECTURE_SKIP.search(p)
        ]
        if hits:
            out[full] = sorted(hits, key=lambda p: (p.count("/"), len(p), p))
    return out


def trees(data):
    proposals = tree_repos(
        data, lambda p: (f := proposal_folder(p)) is not None and folder_member(p, f)
    )
    adrs = tree_repos(
        data, lambda p: (f := adr_folder(p)) is not None and folder_member(p, f)
    )
    wide = subfolder_readmes(data, narrow=False)
    narrow = subfolder_readmes(data)
    architecture = architecture_files(data)
    folder_only = tree_repos(
        data,
        lambda p: (
            re.search(r"(^|/)architecture/", p, re.IGNORECASE) is not None
            and not ARCHITECTURE_SKIP.search(p)
        ),
    )
    workflows = {full: tree.get("workflows", []) for full, tree in data.trees.items()}
    return {
        "trees": len(data.trees),
        "complete": sum(
            not t.get("truncated") and "error" not in t for t in data.trees.values()
        ),
        "proposal_folders": {"repos": len(proposals), "names": proposals},
        "decision_record_folders": {"repos": len(adrs), "names": adrs},
        "subfolder_readmes": {
            "repos": len(narrow),
            "repos_with_5_or_more": sum(len(v) >= 5 for v in narrow.values()),
            "files": sum(len(v) for v in narrow.values()),
            "before_vendored_and_locale_exclusions": {
                "repos": len(wide),
                "repos_with_5_or_more": sum(len(v) >= 5 for v in wide.values()),
            },
        },
        "architecture_file_names": {"repos": len(architecture)},
        "architecture_folder_repos_outside_file_names": sorted(
            set(folder_only) - set(architecture)
        ),
        "names": {
            k: len(
                tree_repos(
                    data, lambda p, rx=rx: re.search(rx, p, re.IGNORECASE) is not None
                )
            )
            for k, rx in TREE_NAMES.items()
        },
        "sbom_workflows": {
            k: len([w for w in v if re.search("sbom", w, re.IGNORECASE)])
            for k, v in workflows.items()
            if any(re.search("sbom", w, re.IGNORECASE) for w in v)
        },
        "sbom_folders": sorted(
            full
            for full, tree in data.trees.items()
            if "sbom" in [d.lower() for d in tree.get("dirs", [])]
            or any(
                re.search(r"(^|/)sbom/", p, re.IGNORECASE)
                for p in tree.get("doc_paths", [])
            )
        ),
        "provenance_workflows": sum(
            bool(re.search(r"slsa|provenance|attest", w, re.IGNORECASE))
            for v in workflows.values()
            for w in v
        ),
    }


# Hand labels and terms


KIND_LABELS = {
    "D": "developer tool, library or framework",
    "O": "operations software",
    "E": "end-user application",
    "C": "collection or theme",
    "R": "research model release",
}


def kind_labels(data):
    """Kind code per repository: `of6_labels.tsv`, else the list's `kind` field."""
    path = data.optional("of6_labels.tsv")
    if path:
        return dict(
            line.rstrip("\n").split("\t") for line in path.open() if line.strip()
        )
    return {r["full_name"]: r["kind"] for r in data.repos if r.get("kind")}


def repo_kinds(data):
    labels = kind_labels(data)
    if not labels:
        return None
    kinds = Counter(labels.get(r["full_name"], "unlabelled") for r in data.repos)
    developer_or_operator = kinds["D"] + kinds["O"]
    return {
        "kinds": ranked(kinds),
        "developer_or_operator": developer_or_operator,
        "share": round(developer_or_operator / len(data.repos), 2),
    }


def term_documents(data):
    """(kind, repo, text) for every README, CONTRIBUTING, SECURITY, PR template, agent file and release body."""
    docs = []
    for r in data.repos:
        full = r["full_name"]
        readme = data.root / "readmes" / f"{corpus_fetch.slug(full)}.md"
        if readme.exists():
            docs.append(("readme", full, readme.read_text(errors="replace")))
        for body in r["releases"].get("bodies") or []:
            if body["body"]:
                docs.append(("release_notes", full, body["body"]))
        for path, entry in data.manifest.get(full, {}).items():
            if entry.get("type") != "file" or "saved" not in entry:
                continue
            name = path.split("/")[-1].lower()
            if name.startswith("contributing"):
                kind = "contributing"
            elif name.startswith("security"):
                kind = "security"
            elif "pull_request_template" in path.lower():
                kind = "pr_template"
            elif re.match(r"(agents|claude|gemini|copilot-instructions)", name):
                kind = "agent_file"
            else:
                continue
            text = data.saved(full, path)
            if text is not None:
                docs.append((kind, full, text))
    return docs


def clean_text(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return re.sub(r"<[^>]+>|https?://\S+|!\[[^\]]*\]\([^)]*\)", " ", text)


def terms(data):
    docs = term_documents(data)
    occurrences = {w: Counter() for w in TERMS}
    repos = {w: set() for w in TERMS}
    for kind, full, text in docs:
        clean = clean_text(text)
        for word, rx in TERMS.items():
            n = len(re.findall(rx, clean, re.IGNORECASE))
            if n:
                occurrences[word][kind] += n
                repos[word].add(full)
    out = {
        "documents": ranked(Counter(k for k, _, _ in docs)),
        "words": {
            w: {"occurrences": ranked(occurrences[w]), "repos": len(repos[w])}
            for w in TERMS
        },
    }
    path = data.optional("of7-labels.json")
    if path:
        labels = json.loads(path.read_text())["labels"]
        out["senses"] = {w: ranked(Counter(v.split())) for w, v in labels.items()}
    return out


def earlier_sample(data, earlier_run, mostly_pr_refs, tools):
    """The release-note measure over the 2026-10-03 reading sample of 28 repositories.

    Under the 2026-10-03 rule, each stratum is sorted by documentation
    richness, then by stars, and the draw takes one repository per stratum in turn.
    """
    before = {r["full_name"] for r in data.stars if before_run(r, earlier_run)}
    pool = [r for r in data.repos if r["full_name"] in before]
    buckets = {}
    for r in sorted(
        pool, key=lambda r: (-sum(k in r["files"] for k in RICHNESS_KEYS), -r["stars"])
    ):
        language = r.get("language") or "none"
        tier = (
            "40k+"
            if r["stars"] >= 40000
            else "10-40k"
            if r["stars"] >= 10000
            else "3-10k"
        )
        buckets.setdefault(
            (language if language in LANGUAGES else "other", tier), []
        ).append(r["full_name"])
    picked = []
    while len(picked) < 28 and any(buckets.values()):
        for key in sorted(buckets):
            if buckets[key] and len(picked) < 28:
                picked.append(buckets[key].pop(0))
    sample = set(picked)
    note_files = set()
    for key in ("changeset", "towncrier_style_folder", "reno"):
        note_files |= set(tools["tools"].get(key, {}).get("names", []))
    return {
        "repos": len(sample),
        "mostly_pr_refs": len(sample & set(mostly_pr_refs)),
        "note_file_tools": sorted(sample & note_files),
        "either": len(sample & (set(mostly_pr_refs) | note_files)),
    }


# Repository list

# Pattern keys left out of the list's document column: configuration and
# example folders, not documents.
REPO_LIST_SKIP = {"workflows_dir", "dependency_bot", "devcontainer", "examples_dir"}


def repo_list(data):
    """The repository list table of the research document, one row per repository."""
    kinds = kind_labels(data)
    rows = []
    for r in data.repos:
        folders = {
            ("" if where == "/" else where) + name
            for where, entries in r["listing"].items()
            for name, kind in entries
            if kind == "dir"
        }
        paths = []
        for key, found in r["files"].items():
            if key in REPO_LIST_SKIP:
                continue
            for p in found:
                p = p + "/" if p in folders else p
                if p not in paths:
                    paths.append(p)
        paths.sort(key=str.lower)
        cells = [
            r["full_name"],
            "yes" if r.get("archived") else "no",
            f"{r['stars']:,}",
            r.get("language") or "none",
            KIND_LABELS.get(kinds.get(r["full_name"]), "unlabelled"),
            ", ".join(f"`{p}`" for p in paths),
        ]
        rows.append((r["full_name"].lower(), "| " + " | ".join(cells) + " |"))
    head = [
        (
            "| Repository | Archived | Stars at freeze | Primary language | Kind label "
            "| Document files found |"
        ),
        "| --- | --- | --- | --- | --- | --- |",
    ]
    return "\n".join(head + [row for _, row in sorted(rows)]) + "\n"


# Reads


def read_headings(text):
    return [h.strip().lower() for h in re.findall(r"(?m)^\s*#{1,6}\s+(.+)$", text)]


def has_heading(text, pattern):
    return any(re.search(pattern, h) for h in read_headings(text))


def has_field(text, name):
    return bool(
        re.search(r"(?im)^\W{0,6}" + name + r"\W{0,4}\s*[:|]", text)
    ) or has_heading(text, r"^" + name + r"\b")


def goals_heading(text):
    goals = [h for h in read_headings(text) if re.search(r"\bgoals?\b", h)]
    return bool(goals) and not all(re.search(r"non-?goals", h) for h in goals)


READ_CHECKS = {
    "proposal": {
        "status_field": lambda t: has_field(t, "status"),
        "goals_heading": goals_heading,
        "non_goals_heading": lambda t: has_heading(t, r"non-?goals"),
        "problem_or_motivation_heading": lambda t: has_heading(
            t, r"problem|motivation|why\b|background|context"
        ),
        "alternatives_heading": lambda t: has_heading(
            t, r"alternative|options considered|pros and cons"
        ),
        "open_questions_heading": lambda t: has_heading(
            t, r"open questions|unresolved|key questions"
        ),
    },
    "adr": {
        "status_field_or_heading": lambda t: has_field(t, "status"),
        "context_heading": lambda t: has_heading(t, r"context|problem"),
        "decision_heading": lambda t: has_heading(t, r"^decision"),
        "alternatives_heading": lambda t: has_heading(
            t, r"alternative|options considered"
        ),
        "consequences_heading": lambda t: has_heading(t, r"consequences"),
        "superseded_or_replaced_link": lambda t: bool(
            re.search(r"(?i)supersed|replaced by", t)
        ),
    },
    "architecture": {
        "flow_heading": lambda t: has_heading(
            t, r"flow|pipeline|lifecycle|request|path\b"
        ),
        "code_location": lambda t: bool(
            re.search(
                r"(?i)(\]\((\.\./)*[\w./-]+\.(go|ts|tsx|py|rs|js)[)#]|blob/[^ )]+\.(go|ts|py|rs|js)"
                r"|directory structure|repository structure|codebase|source code|where the code)",
                t,
            )
        ),
        "diagram": lambda t: bool(
            re.search(r"```mermaid|!\[|[┌└│]|```text\n[^`]*->", t)
        ),
    },
}


def reads(index_path):
    """Element counts over read files, by the group a reader gave each file."""
    index_path = Path(index_path)
    entries = json.loads(index_path.read_text())
    if isinstance(entries, dict):
        entries = entries.get("picks", [])
    out = {}
    for group, checks in READ_CHECKS.items():
        files = []
        for e in entries:
            if e.get("group") != group:
                continue
            path = Path(e["file"])
            path = path if path.is_absolute() else index_path.parent / path
            files.append((e["repo"], path.read_text(errors="replace")))
        if not files:
            continue
        counts = {"files": len(files), "repos": len({r for r, _ in files})}
        for name, check in checks.items():
            hit = [r for r, t in files if check(t)]
            counts[name] = {"files": len(hit), "repos": len(set(hit))}
        out[group] = counts
    return out


def count(data, earlier_run=None, reads_index=None):
    doc_flags = document_flags(data)
    release = releases(data)
    mostly_pr_refs = release.pop("_mostly_pr_refs")
    tools = change_note_tools(data, mostly_pr_refs)
    out = {
        "corpus": corpus_counts(data, earlier_run),
        "prevalence": prevalence(data),
        "releases": release,
        "release_lines_and_pr_titles": pr_titles(data),
        "change_note_tools": tools,
        "commits": commits(data),
        "pulls": pulls(data),
        "documents": documents(data, doc_flags),
        "security_classes": security_classes(data, doc_flags),
        "small_files": small_files(data),
        "agent_files": agent_files(data),
        "names": names(data),
        "trees": trees(data),
        "repo_kinds": repo_kinds(data),
        "terms": terms(data),
    }
    if earlier_run:
        out["earlier_sample"] = earlier_sample(data, earlier_run, mostly_pr_refs, tools)
    if reads_index:
        out["reads"] = reads(reads_index)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--data", required=True, type=Path, help="raw data folder from corpus_fetch.py"
    )
    parser.add_argument("--min-stars", type=int, default=3000)
    parser.add_argument(
        "--earlier-run",
        help="UTC time of an earlier star fetch, such as 2026-10-03T18:00:00Z",
    )
    parser.add_argument(
        "--reads", type=Path, help="reads index with a group per read file"
    )
    parser.add_argument(
        "--labels",
        type=Path,
        help="folder with reader label files (default: the raw data folder)",
    )
    parser.add_argument("--out", type=Path, help="counts file (default: print)")
    parser.add_argument(
        "--repo-list", type=Path, help="also write the repository list table here"
    )
    args = parser.parse_args(argv)
    data = load(args.data, args.min_stars, args.labels)
    if args.repo_list:
        args.repo_list.write_text(repo_list(data))
    result = count(data, args.earlier_run, args.reads)
    text = json.dumps(result, indent=1, ensure_ascii=False, default=list) + "\n"
    if args.out:
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
