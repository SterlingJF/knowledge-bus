"""Vendor adapters for the decision and judgment tiers. Only this file names vendors.

Decision: Jev (TypeSafe), one request per text with every rule's typed question about it.
Judgment: each named model, one call per rule and batch, with structured output. A model named
codex:<model> runs through `codex exec` (OpenAI side); any other name through `claude -p`.
Sort: the same models write, validate and file probes; Jev files each probe as a typed choice.
Recognition: the same models and Jev pick the option that fits each situation, one per call.
Agents under test (tools/evals/play.py): `claude -p` with the skills as a session-only plugin, or
`codex exec` with the skills in the project's .agents/skills/; each owner reply resumes the session.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from tiers import JUDGES_ONLY, PER_ITEM, Outcome, set_key

JEV_URL = "https://api.typesafe.ai/v1/systemone"
RETRY = (429, 529, 500, 502, 503, 504)


def _context(case):
    """The case's context for Jev: the owner turns either side are for the judges only."""
    return {k: v for k, v in case.context.items() if k not in JUDGES_ONLY}


def _state(case):
    context = _context(case)
    return case.text if not context else {"text": case.text, **context}


def _instructions(case, ask):
    return ask if not _context(case) else f"{ask}\nThe text to judge is `text`."


class Jev:
    """Decision tier. A yes-no answer settles at P(yes) >= yes or <= no; choice and score at confidence >= confidence."""

    name = "jev"

    def __init__(
        self,
        key,
        model="jev-latest",
        yes=0.7,
        no=0.3,
        confidence=0.6,
        workers=8,
        post=None,
    ):
        self.key, self.model, self.yes, self.no, self.confidence = (
            key,
            model,
            yes,
            no,
            confidence,
        )
        self.workers, self.version, self.tokens = workers, None, 0
        self._post = post or self._http

    def _http(self, body):
        request = urllib.request.Request(
            JEV_URL,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code not in RETRY or attempt == 5:
                    raise
            except urllib.error.URLError:
                if attempt == 5:
                    raise
            time.sleep(2**attempt)

    @staticmethod
    def question(case):
        block = case.rule["decision"]
        ask = _instructions(case, block["ask"])
        if block["type"] == "yes-no":
            q = {"type": "noul", "instructions": ask}
            if block.get("criteria"):
                q["criteria"] = {
                    "true": block["criteria"]["yes"],
                    "false": block["criteria"]["no"],
                }
            return q
        if block["type"] == "choice":
            return {
                "type": "choice",
                "instructions": ask,
                "criteria": block["criteria"],
            }
        return {"type": "score", "instructions": ask, "criteria": block["levels"]}

    def read(self, case, answer):
        block = case.rule["decision"]
        detail = {k: v for k, v in answer.items() if k != "legend"}
        if block["type"] == "yes-no":
            p = answer["noul"]
            said = "yes" if p >= self.yes else "no" if p <= self.no else None
            if said is None:
                return Outcome("undecided", "decision", detail)
            return Outcome(
                "fail" if said == block["fail_when"] else "pass", "decision", detail
            )
        if answer["confidence"] < self.confidence:
            return Outcome("undecided", "decision", detail)
        if block["type"] == "choice":
            return Outcome(
                "fail" if answer["choice"] in block["fail_when"] else "pass",
                "decision",
                detail,
            )
        return Outcome(
            "fail" if answer["score"] < block["fail_when"]["below"] - 0.5 else "pass",
            "decision",
            detail,
        )

    def __call__(self, cases):
        groups = {}
        for i, case in enumerate(cases):
            groups.setdefault(json.dumps(_state(case), sort_keys=True), []).append(i)
        outcomes = [None] * len(cases)

        def ask(indexes):
            body = {
                "state": _state(cases[indexes[0]]),
                "model": self.model,
                "questions": {f"q{i}": self.question(cases[i]) for i in indexes},
            }
            response = self._post(body)
            self.version = response.get("model", self.version)
            self.tokens += sum((response.get("usage") or {}).values())
            for i in indexes:
                outcomes[i] = self.read(cases[i], response["answers"][f"q{i}"])

        with ThreadPoolExecutor(self.workers) as pool:
            list(pool.map(ask, groups.values()))
        return outcomes


JUDGE_SYSTEM = (
    "You grade texts against one quality rule set by their owner. Judge each item on its own text. "
    "Apply the PASS and FAIL criteria exactly as written. Answer unknown only when the text alone "
    "cannot settle it. Give a one-sentence critique in plain words."
)
VERDICTS = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "integer"},
                    "verdict": {"type": "string", "enum": ["pass", "fail", "unknown"]},
                    "critique": {"type": "string"},
                },
                "required": ["item", "verdict", "critique"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}


SHARED_LABELS = {"enablement": "Artifact enablement"}


def _set_items(cases):
    members, context = cases[0].context["set"], cases[0].context
    lines = [f"The whole set ({len(members)} items), for reference:"]
    lines += [
        f"{n}. {json.dumps(m, ensure_ascii=False)}" for n, m in enumerate(members, 1)
    ]
    shared = [
        f"{SHARED_LABELS.get(k, k)}: {v}"
        for k, v in context.items()
        if k not in PER_ITEM
    ]
    lines += ["", *shared] if shared else []
    lines += ["", "Items to judge, each as a member of the set above:"]
    for n, case in enumerate(cases, 1):
        strength = case.context.get("strength")
        suffix = f" (strength: {strength})" if strength else ""
        lines.append(f"Item {n}: {json.dumps(case.text, ensure_ascii=False)}{suffix}")
    lines += [
        "",
        "When a critique concerns another item in the set, name that item by its text.",
        f"Return one verdict for each of the {len(cases)} items.",
    ]
    return lines


def claude_cli(prompt, model, schema, system):
    """One `claude -p` call with structured output, user settings, tools and MCP servers off."""
    command = [
        "claude", "-p", "--model", model, "--output-format", "json",
        "--no-session-persistence", "--tools", "", "--setting-sources", "",
        "--strict-mcp-config", "--exclude-dynamic-system-prompt-sections",
        "--json-schema", json.dumps(schema), "--system-prompt", system, prompt,
    ]  # fmt: skip
    with tempfile.TemporaryDirectory(prefix="evals-judge-") as cwd:
        done = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
            env=os.environ,
            check=False,
        )
    reply = json.loads(done.stdout) if done.stdout.strip().startswith("{") else {}
    if done.returncode or reply.get("is_error") or "structured_output" not in reply:
        detail = done.stderr.strip() or str(reply.get("result", done.stdout))
        raise RuntimeError(f"model call failed: {detail[:300]}")
    return reply


CODEX = "codex:"
# Tools Codex turns on by default, beyond its shell; --ignore-user-config does not reach them.
CODEX_OFF = (
    "apps", "browser_use", "computer_use", "hooks", "image_generation", "multi_agent",
    "plugins",
)  # fmt: skip


def _codex_off():
    return [flag for feature in CODEX_OFF for flag in ("--disable", feature)]


def _codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _home_skills_off():
    """A config override that disables each skill in the Codex home, by its SKILL.md; the bundled
    system skills under skills/.system and the project's own skills stay."""
    root = _codex_home() / "skills"
    found = (
        sorted(
            p / "SKILL.md"
            for p in root.iterdir()
            if not p.name.startswith(".") and (p / "SKILL.md").is_file()
        )
        if root.is_dir()
        else []
    )
    if not found:
        return []
    entries = ",".join(
        f"{{path={json.dumps(str(p), ensure_ascii=False)},enabled=false}}"
        for p in found
    )
    return ["-c", f"skills.config=[{entries}]"]


def codex_cli(prompt, model, schema, system):
    """One `codex exec` call, read-only and ephemeral in an empty folder, with user config, rules,
    project instructions, skills and the default extra tools off. Its last message is the
    structured output; tokens are kept when the run reports them."""
    with (
        tempfile.TemporaryDirectory(prefix="evals-judge-") as cwd,
        tempfile.TemporaryDirectory(prefix="evals-codex-") as io,
    ):
        shape, last = Path(io) / "schema.json", Path(io) / "last.json"
        shape.write_text(json.dumps(schema))
        command = [
            "codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "-s", "read-only", "--skip-git-repo-check", "-C", cwd, "-m", model,
            "-c", "project_doc_max_bytes=0", "-c", f"developer_instructions={json.dumps(system)}",
            "-c", "skills.include_instructions=false", *_codex_off(), "--output-schema", str(shape), "-o", str(last), "--json", "-",
        ]  # fmt: skip
        done = subprocess.run(
            command,
            input=prompt,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
            env=os.environ,
            check=False,
        )
        text = last.read_text() if last.exists() else ""
    events = _jsonl(done.stdout)
    try:
        output = json.loads(text)
    except ValueError:
        output = None
    if done.returncode or not isinstance(output, dict):
        errors = [
            e.get("message") or (e.get("error") or {}).get("message") or ""
            for e in events
            if e.get("type") in ("error", "turn.failed")
        ]
        detail = "; ".join(filter(None, errors)) or done.stderr.strip() or text
        raise RuntimeError(f"model call failed: {detail[:300]}")
    reply = {"structured_output": output}
    usage = next(
        (
            e["usage"]
            for e in events
            if e.get("type") == "turn.completed" and e.get("usage")
        ),
        None,
    )
    if usage:
        reply["tokens"] = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    return reply


def _jsonl(stdout):
    """The JSON objects among a CLI's output lines; other lines are skipped."""
    events = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def on_codex(model):
    """Whether a model runs through the Codex CLI (codex:<model>) rather than through claude."""
    return model.startswith(CODEX)


def model_call(prompt, model, schema, system):
    """One structured call: codex:<model> through the Codex CLI, any other name through claude."""
    if on_codex(model):
        return codex_cli(prompt, model[len(CODEX) :], schema, system)
    return claude_cli(prompt, model, schema, system)


def unavailable(models):
    """Why the named models cannot be called from here, or None. Each CLI is needed only when one
    of its models is named. The Codex home must hold no instructions of its own: `codex exec`
    loads its AGENTS.md into every call, and none of its flags turns that off. The home's own
    skills are switched off per call instead."""
    if any(not on_codex(m) for m in models) and not shutil.which("claude"):
        return "the claude CLI is not on PATH"
    if not any(on_codex(m) for m in models):
        return None
    if not shutil.which("codex"):
        return "the codex CLI is not on PATH"
    home = _codex_home()
    found = [
        name
        for name in ("AGENTS.override.md", "AGENTS.md")
        if (home / name).is_file() and (home / name).stat().st_size
    ]
    if not found:
        return None
    return (
        f"the Codex home {home} holds {', '.join(found)}, which would reach every call; "
        "set CODEX_HOME to a folder holding only a login (CODEX_HOME=<folder> codex login)"
    )


def _spend(adapter, reply):
    """Add a reply's reported dollars and tokens; what no reply reports stays None."""
    if "total_cost_usd" in reply:
        adapter.cost = (adapter.cost or 0.0) + reply["total_cost_usd"]
    if "tokens" in reply:
        adapter.tokens = (adapter.tokens or 0) + reply["tokens"]


def retrying(call, attempts=3, sleep=time.sleep):
    """call(), retried with backoff on RuntimeError; the last error is raised."""
    for attempt in range(attempts):
        try:
            return call()
        except RuntimeError:
            if attempt == attempts - 1:
                raise
            sleep(5 * 2**attempt)


class Judge:
    """Judgment tier: each named model through its CLI (see model_call), isolated from user
    settings, tools and instructions.

    With several models, every model judges every item and a verdict stands only when all agree;
    a split is undecided and goes to the owner. Each model's own vote is kept in the outcome's
    detail as `votes`, so any pairing of judges can be worked out later.
    """

    def __init__(
        self,
        models=("claude-opus-5-5", "claude-fable-5-1"),
        batch=20,
        workers=4,
        call=None,
        attempts=3,
        sleep=time.sleep,
    ):
        self.models, self.batch, self.workers = tuple(models), batch, workers
        self.version, self.failures = "+".join(self.models), 0
        self.cost = self.tokens = None
        self._call, self._attempts, self._sleep = call or self._cli, attempts, sleep
        self._lock = threading.Lock()

    @staticmethod
    def _cli(prompt, model):
        return model_call(prompt, model, VERDICTS, JUDGE_SYSTEM)

    @staticmethod
    def prompt(cases):
        rule = cases[0].rule
        lines = [f"Rule: {rule.get('rule') or rule.get('behaviour')}"]
        if rule.get("why"):
            lines.append(f"Why it matters: {rule['why']}")
        lines += [rule["judgment"]["pass"], rule["judgment"]["fail"], ""]
        if "set" in cases[0].context:
            return "\n".join(lines + _set_items(cases))
        lines.append("Items:")
        for n, case in enumerate(cases, 1):
            lines.append(f"{n}. {json.dumps(case.text, ensure_ascii=False)}")
            if case.context:
                lines.append(
                    f"   context, for reference only (judge the quoted text): {json.dumps(case.context, ensure_ascii=False)}"
                )
        lines.append("")
        lines.append(f"Return one verdict for each of the {len(cases)} items.")
        return "\n".join(lines)

    def __call__(self, cases):
        groups = {}
        for i, case in enumerate(cases):
            groups.setdefault((case.rule_id, set_key(case)), []).append(i)
        batches = [
            idx[s : s + self.batch]
            for idx in groups.values()
            for s in range(0, len(idx), self.batch)
        ]
        jobs = [(model, b) for b in batches for model in self.models]
        said = [{} for _ in cases]

        def judge(job):
            model, indexes = job
            prompt = self.prompt([cases[i] for i in indexes])
            try:
                reply = retrying(
                    lambda: self._call(prompt, model), self._attempts, self._sleep
                )
            except RuntimeError as error:
                with self._lock:
                    self.failures += 1
                for i in indexes:
                    said[i][model] = {
                        "verdict": "unknown",
                        "critique": f"{model} call failed: {error}",
                    }
                return
            with self._lock:
                _spend(self, reply)
            by_item = {v["item"]: v for v in reply["structured_output"]["verdicts"]}
            for n, i in enumerate(indexes, 1):
                said[i][model] = by_item.get(
                    n, {"verdict": "unknown", "critique": "no verdict returned"}
                )

        with ThreadPoolExecutor(self.workers) as pool:
            list(pool.map(judge, jobs))
        outcomes = []
        for votes in said:
            verdicts = {v["verdict"] for v in votes.values()}
            settled = len(verdicts) == 1 and "unknown" not in verdicts
            if len(self.models) == 1:
                critique = next(iter(votes.values()))["critique"]
            else:
                critique = " | ".join(
                    f"{m}: {votes[m]['critique']}" for m in self.models
                )
            outcomes.append(
                Outcome(
                    verdicts.pop() if settled else "undecided",
                    "judgment",
                    {
                        "critique": critique,
                        "votes": {m: _vote(votes[m]) for m in self.models},
                    },
                )
            )
        return outcomes


def _vote(said):
    return {"verdict": said["verdict"], "critique": said.get("critique", "")}


def _schema(key, item):
    return {
        "type": "object",
        "properties": {key: {"type": "array", "items": item}},
        "required": [key],
        "additionalProperties": False,
    }


PASSAGES = _schema("passages", {"type": "string"})
ANSWERS = _schema(
    "answers",
    {
        "type": "object",
        "properties": {
            "passage": {"type": "integer"},
            "answers": {"type": "boolean"},
        },
        "required": ["passage", "answers"],
        "additionalProperties": False,
    },
)
FILINGS = _schema(
    "filings",
    {
        "type": "object",
        "properties": {
            "passage": {"type": "integer"},
            "question": {"type": "integer"},
        },
        "required": ["passage", "question"],
        "additionalProperties": False,
    },
)
WRITE_SYSTEM = (
    "You write short constructed passages for a test of how knowledge is filed. "
    "Follow the instruction exactly and return only the passages."
)
CHECK_SYSTEM = (
    "You check passages against one question. Judge each passage on its own: say whether it "
    "answers the question, fully or in part, as it stands."
)
FILE_SYSTEM = (
    "You file passages from working documents. Read the questions carefully, then put each "
    "passage under the one question it answers. Answer 0 only when it answers none of them."
)
OPTION = {
    "type": "object",
    "properties": {"option": {"type": "integer"}},
    "required": ["option"],
    "additionalProperties": False,
}
RECOGNISE_SYSTEM = (
    "You read an everyday situation and pick the option that fits it. Read the options "
    "carefully, then give the number of the one that fits best. Answer 0 only when none fits."
)


def _numbered(texts):
    return [f"{n}. {json.dumps(t, ensure_ascii=False)}" for n, t in enumerate(texts, 1)]


class Models:
    """Probe writer, validity judge, filer and recognition reader, each model through its CLI (see
    model_call), with the judge's retry and backoff."""

    def __init__(self, call=None, attempts=3, sleep=time.sleep):
        self._call, self._attempts, self._sleep = call or model_call, attempts, sleep
        self.cost = self.tokens = None
        self.failures, self._lock = 0, threading.Lock()

    def _ask(self, prompt, model, schema, system, read):
        def once():
            reply = self._call(prompt, model, schema, system)
            with self._lock:
                _spend(self, reply)
            return read(reply["structured_output"])

        try:
            return retrying(once, self._attempts, self._sleep)
        except RuntimeError:
            with self._lock:
                self.failures += 1
            raise

    def write(self, model, question, instruction, scope=""):
        prompt = f"{instruction}\n\nQuestion: {question}"
        if scope:
            prompt = f"{scope}\n\n{prompt}"
        return self._ask(
            prompt, model, PASSAGES, WRITE_SYSTEM, lambda out: list(out["passages"])
        )

    def answers(self, model, question, passages, scope=""):
        lines = [f"Question: {json.dumps(question, ensure_ascii=False)}", ""]
        if scope:
            lines = [scope, "", *lines]
        lines += ["Passages:", *_numbered(passages), ""]
        lines.append(
            f"For each of the {len(passages)} passages, say whether it answers the question."
        )
        return self._ask(
            "\n".join(lines),
            model,
            ANSWERS,
            CHECK_SYSTEM,
            lambda out: _by_passage(out["answers"], "answers", len(passages)),
        )

    def file(self, model, questions, passages, ask):
        lines = [ask, "", "Questions:", *_numbered(questions), ""]
        lines += ["Passages:", *_numbered(passages), ""]
        lines.append(
            f"For each of the {len(passages)} passages, give the number of the question it "
            "answers, or 0 if it answers none of them."
        )
        return self._ask(
            "\n".join(lines),
            model,
            FILINGS,
            FILE_SYSTEM,
            lambda out: _by_passage(out["filings"], "question", len(passages)),
        )

    def recognise(self, model, options, situations, ask):
        """One situation per call: the number of the option that fits it, or 0 for none."""
        (situation,) = situations
        lines = [ask, "", "Options:", *_numbered(options), ""]
        lines += [f"Situation: {json.dumps(situation, ensure_ascii=False)}", ""]
        lines.append(
            "Give the number of the option that fits the situation, or 0 if none fits."
        )
        return [
            self._ask(
                "\n".join(lines), model, OPTION, RECOGNISE_SYSTEM, lambda o: o["option"]
            )
        ]


def _by_passage(rows, field, count):
    said = {row["passage"]: row[field] for row in rows}
    missing = [n for n in range(1, count + 1) if n not in said]
    if missing:
        noun = "filing" if field == "question" else "answer"
        raise RuntimeError(f"no {noun} for passage {missing[0]}")
    return [said[n] for n in range(1, count + 1)]


class JevChoice:
    """Sort filer: one typed choice per probe, options "1".."N" whose criteria are the questions.

    A choice below the decision adapter's confidence threshold is "unsure": it leaves the member
    undecided unless another filer puts the probe elsewhere."""

    name = "jev"

    def __init__(self, key, model="jev-latest", confidence=0.6, workers=8, post=None):
        self._jev = Jev(key, model=model, confidence=confidence, post=post)
        self.confidence, self.workers = confidence, workers
        self.version, self.tokens, self._lock = None, 0, threading.Lock()

    def file(self, questions, passages, ask):
        criteria = {str(n): q for n, q in enumerate(questions, 1)}

        def one(passage):
            body = {
                "state": passage,
                "model": self._jev.model,
                "questions": {
                    "q": {"type": "choice", "instructions": ask, "criteria": criteria}
                },
            }
            response = self._jev._post(body)
            with self._lock:
                self.version = response.get("model", self.version)
                self.tokens += sum((response.get("usage") or {}).values())
            answer = response["answers"]["q"]
            if answer["confidence"] < self.confidence:
                return "unsure"
            return int(answer["choice"])

        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(one, passages))


ROOT = Path(__file__).resolve().parents[2]
TRIM = 300
AGENT_TIMEOUT = 1800


@dataclass
class Turn:
    """One agent turn: its steps in order ({"kind": "text", "text"} or {"kind": "tool", "name",
    "input", "output"}), its final message, the raw events, and what the host reported loading."""

    session: str = ""
    steps: list = field(default_factory=list)
    final: str = ""
    events: list = field(default_factory=list)
    error: str | None = None
    loaded: dict | None = None


def _trim(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= TRIM else text[:TRIM] + "…"


def _version(cli):
    done = subprocess.run(
        [cli, "--version"], capture_output=True, text=True, check=False
    )
    return done.stdout.strip()


def _agent(command, stdin, work, cache, extra=None):
    """Run one agent turn in the work folder; the bundled checker keeps its cache in `cache`, and
    `extra` (name, value) pairs add to the environment."""
    env = {**os.environ, **dict(extra or ()), "KNOWLEDGE_BUS_CACHE_DIR": str(cache)}
    try:
        done = subprocess.run(
            command,
            input=stdin,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=AGENT_TIMEOUT,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [], f"no reply within {AGENT_TIMEOUT} seconds", 1
    return _jsonl(done.stdout), done.stderr.strip()[:TRIM], done.returncode


class ClaudeAgent:
    """`claude -p` in the work folder, with the skills under test as a session-only plugin and user
    settings and MCP servers off, as for the judges. Each owner reply resumes the session by id.
    Bash runs without asking only for python3 and the read-only ls, cat, head, tail, wc and grep
    (not find, whose -delete and -exec a prefix rule cannot exclude; Glob finds files), and a note
    appended to the system prompt tells the agent so. Auto-memory is off for every call, so the
    agent writes no notes under ~/.claude/projects/<work folder>/memory/. Run notes list the set,
    the note and the environment."""

    name = "claude"
    tools = ("Read", "Glob", "Grep", "Skill", "Write", "Edit", "Bash")
    allowed = (
        "Read", "Glob", "Grep", "Skill", "Write", "Edit", "Bash(python3:*)",
        "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)",
        "Bash(grep:*)",
    )  # fmt: skip
    note = (
        "Harness note: Bash runs without asking only for python3, ls, cat, head, tail, wc and "
        "grep. Run one simple command at a time, with no loops, chaining, cd or variables. A "
        "denied command does not mean the shell is unavailable; run the next simple command."
    )
    env = (("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "1"),)

    def __init__(self, model, budget=3.0):
        self.model, self.budget = model, budget
        self.cost = self.tokens = None
        self._plugin = self._cache = None

    @staticmethod
    def unavailable():
        return None if shutil.which("claude") else "the claude CLI is not on PATH"

    @staticmethod
    def version():
        return _version("claude")

    def install(self, skills, work, scratch):
        """The skills, as this checkout holds them, under the Claude plugin manifest."""
        self._plugin = Path(scratch) / "plugin/knowledge-bus"
        manifest = ROOT / "plugins/claude/knowledge-bus/.claude-plugin/plugin.json"
        (self._plugin / ".claude-plugin").mkdir(parents=True)
        shutil.copyfile(manifest, self._plugin / ".claude-plugin/plugin.json")
        for name, folder in skills.items():
            shutil.copytree(folder, self._plugin / "skills" / name)
        self._cache = Path(scratch) / "cache"
        self._cache.mkdir(exist_ok=True)

    def start(self, work, prompt):
        return self._turn(work, prompt, ["--session-id", str(uuid.uuid4())])

    def reply(self, work, session, text):
        return self._turn(work, text, ["--resume", session])

    def _turn(self, work, text, session):
        command = [
            "claude", "-p", "--verbose", "--output-format", "stream-json",
            "--model", self.model, "--max-budget-usd", str(self.budget),
            "--setting-sources", "", "--strict-mcp-config",
            "--exclude-dynamic-system-prompt-sections", "--plugin-dir", str(self._plugin),
            "--tools", ",".join(self.tools), "--allowedTools", *self.allowed,
            "--permission-mode", "dontAsk", "--append-system-prompt", self.note, *session,
        ]  # fmt: skip
        events, stderr, code = _agent(command, text, work, self._cache, self.env)
        turn, tools = Turn(session=session[1], events=events), {}
        result = None
        for event in events:
            if event.get("type") == "system" and event.get("subtype") == "init":
                turn.loaded = {k: event.get(k) or [] for k in ("plugins", "skills")}
            message = event.get("message")
            for block in (message if isinstance(message, dict) else {}).get(
                "content"
            ) or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    turn.steps.append({"kind": "text", "text": block["text"]})
                elif block.get("type") == "tool_use":
                    step = {
                        "kind": "tool",
                        "name": block.get("name"),
                        "input": block.get("input") or {},
                    }
                    tools[block.get("id")] = step
                    turn.steps.append(step)
                elif (
                    block.get("type") == "tool_result"
                    and block.get("tool_use_id") in tools
                ):
                    tools[block["tool_use_id"]]["output"] = _trim(
                        block.get("content", "")
                    )
            if event.get("type") == "result":
                result = event
        texts = [s["text"] for s in turn.steps if s["kind"] == "text"]
        turn.final = (result or {}).get("result") or (texts[-1] if texts else "")
        if result:
            _spend(self, result)
        if code or not result or result.get("is_error"):
            turn.error = (result or {}).get("subtype") or stderr or f"exit code {code}"
        return turn

    def _from_test(self, path):
        """Whether a plugin path is the folder passed as --plugin-dir; without a path, assumed."""
        if not path or not self._plugin:
            return True
        return Path(path).resolve() == Path(self._plugin).resolve()

    @staticmethod
    def fired(turns, skill):
        """A Skill call naming the skill, bare or under the plugin's name."""
        pattern = rf"(?:[\w-]+:)?{re.escape(skill)}"
        return any(
            s["kind"] == "tool"
            and s["name"] == "Skill"
            and re.fullmatch(pattern, str(s["input"].get("skill", "")))
            for t in turns
            for s in t.steps
        )

    def extra(self, turns, names):
        """Plugins other than the one under test (an installed knowledge-bus included), and copies
        of its skills from elsewhere, as the session's init event lists them."""
        loaded = next((t.loaded for t in turns if t.loaded), None) or {}
        found, ours = [], None
        for plugin in loaded.get("plugins", []):
            if not isinstance(plugin, dict):
                continue
            name, path = plugin.get("name"), plugin.get("path")
            if ours is None and name == "knowledge-bus" and self._from_test(path):
                ours = plugin
                continue
            found.append(f"plugin {name}" + (f" ({path})" if path else ""))
        for skill in loaded.get("skills", []):
            skill = skill.get("name", "") if isinstance(skill, dict) else str(skill)
            if skill.rsplit(":", 1)[-1] in names and not skill.startswith(
                "knowledge-bus:"
            ):
                found.append(f"skill {skill}")
        return found


class CodexAgent:
    """`codex exec` in the work folder, sandboxed to it and the checker's cache, with user config,
    rules, project instructions and the default extra tools off as for the judges, the Codex
    home's own skills disabled, and the skills under test in the project's .agents/skills/. Each
    owner reply resumes the thread by id."""

    name = "codex"

    def __init__(self, model):
        self.model = model
        self.cost = self.tokens = None
        self._cache = None

    def unavailable(self):
        return unavailable([CODEX + self.model])

    @staticmethod
    def version():
        return _version("codex")

    def install(self, skills, work, scratch):
        """The skills, as this checkout holds them, where Codex reads project skills."""
        for name, folder in skills.items():
            shutil.copytree(folder, Path(work) / ".agents/skills" / name)
        self._cache = Path(scratch) / "cache"
        self._cache.mkdir(exist_ok=True)

    def _options(self):
        return [
            "--json", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
            "-m", self.model, "-c", 'sandbox_mode="workspace-write"',
            "-c", 'approval_policy="never"',
            "-c", f"sandbox_workspace_write.writable_roots={json.dumps([str(self._cache)])}",
            "-c", "project_doc_max_bytes=0", *_home_skills_off(), *_codex_off(),
        ]  # fmt: skip

    def start(self, work, prompt):
        return self._turn(
            work, prompt, ["exec", *self._options(), "-C", str(work), "-"]
        )

    def reply(self, work, session, text):
        return self._turn(
            work, text, ["exec", "resume", *self._options(), session, "-"]
        )

    def _turn(self, work, text, arguments):
        events, stderr, code = _agent(["codex", *arguments], text, work, self._cache)
        turn, errors = Turn(events=events), []
        for event in events:
            kind, item = event.get("type"), event.get("item") or {}
            if kind == "thread.started":
                turn.session = event.get("thread_id", "")
            elif kind == "item.completed" and item.get("type") == "agent_message":
                turn.steps.append({"kind": "text", "text": item.get("text", "")})
            elif kind == "item.completed" and item.get("type") not in (
                None,
                "reasoning",
            ):
                shown = {
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "type", "aggregated_output")
                }
                step = {"kind": "tool", "name": item["type"], "input": shown}
                if "aggregated_output" in item:
                    step["output"] = _trim(item["aggregated_output"])
                turn.steps.append(step)
            elif kind == "turn.completed" and event.get("usage"):
                usage = event["usage"]
                _spend(
                    self,
                    {
                        "tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0)
                    },
                )
            elif kind in ("error", "turn.failed"):
                errors.append(
                    event.get("message")
                    or (event.get("error") or {}).get("message")
                    or kind
                )
        texts = [s["text"] for s in turn.steps if s["kind"] == "text"]
        turn.final = texts[-1] if texts else ""
        if code or errors:
            turn.error = "; ".join(errors) or stderr or f"exit code {code}"
        return turn

    @staticmethod
    def fired(turns, skill):
        """A command that reads the skill's SKILL.md: Codex lists skills by name and description
        and reads the file when it uses one."""
        return any(
            s["kind"] == "tool"
            and f"{skill}/SKILL.md" in str(s["input"].get("command", ""))
            for t in turns
            for s in t.steps
        )

    @staticmethod
    def extra(turns, names):
        """Skills in the user and admin scopes, which Codex loads beside the project's own; the
        Codex home's own skills are disabled on every call, so they are not listed."""
        found = []
        for root in (Path.home() / ".agents/skills", Path("/etc/codex/skills")):
            if root.is_dir():
                found += sorted(
                    f"{root}/{p.name}"
                    for p in root.iterdir()
                    if not p.name.startswith(".")
                )
        return found


AGENTS = {"claude": ClaudeAgent, "codex": CodexAgent}
