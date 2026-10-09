# Code Repository Universe Research

> **Renamed:** after the stage 6 evals, this preset became `codebase-recordkeeping` ("Codebase recordkeeping"). The counts, grades and eval results below are unchanged.

Corpus frozen: 2026-10-08 23:54 EDT

## Purpose

This document holds the evidence behind the code-repository universe spec (now codebase-recordkeeping), a preset for the written documents of a codebase. Stage 1 covers the corpus, the method, the counts, the grades and the sources. Each later stage has its own section in this document: stage 2 covers the header and the document types, stage 3 covers the element questions, stage 4 covers the frames and factors, stage 5 covers the type guidance, stage 6 covers the grades and the fixes to failing texts, and stage 7 covers shipping the universe spec with the tools and docs.

Readers:

- A person adopting the preset checks the counts, sources and refusals behind each document type.
- A universe spec maintainer declares the document types at stage 2 from the tables in this document.
- A community fork reruns every count with the scripts in `tools/research/` and the [repository list](#repository-list).

## Corpus

Corpus rule: "repositories with 3,000+ stars among the maintainer's public GitHub stars, as of 2026-10-08 23:54 EDT".

- Freeze: 2026-10-08 23:54 EDT (2026-10-09T03:54:28Z). One fetch at that time gave the star list and the star counts. Files, commits, releases and pull requests were gathered in the next 30 minutes.
- 146 of 207 starred repositories pass the rule. Stars at freeze: median 17,931, minimum 3,016, maximum 324,739. 4 repositories are archived. No repository is a fork.
- Primary languages: TypeScript 34, Go 33, Python 26, Rust 11, JavaScript 9, Swift 6, and 27 repositories across 15 other languages or with no language.
- The [repository list](#repository-list) names all 146 repositories. `tools/research/fixtures/corpus-2026-10-08.jsonl` holds the same list for the scripts: name, primary language and stars at freeze, kind label and a first-pass flag. A rerun starts from the list file.
- A first pass on 2026-10-03 drafted the candidates and the file-name patterns from 143 repositories. Three repositories were starred after the first pass: gastownhall/gastown, dolthub/dolt and harbor-framework/harbor. The 2026-10-03 repository list was not kept; the first-pass flag in the list file marks the repositories starred before the first pass.

## Rerunning the Counts

Three scripts in `tools/research/` rebuild the counts. `corpus_fetch.py` takes `gh` from `PATH`, makes one GitHub API call at a time and stops on a rate limit. The other two scripts read the raw data folder offline. Each script lists its options with `--help`.

| Script | Step |
| --- | --- |
| `corpus_fetch.py` | Reads the repository list file, or fetches an account's star list, then fetches each repository's listings, file tree, releases, commits and pull requests. With `--stage reads`, fetches the files named in a picks file |
| `corpus_counts.py` | Computes file prevalence and every pattern count in this document, and writes the [repository list](#repository-list) table |
| `corpus_sample.py` | Draws the seeded reading samples |

Settings for this corpus: a minimum of 3,000 stars and seed 20261008. The 2026-10-09 reads used seed 20261009.

Rerun commands, from the repository root, with `DATA` and `READS` as two empty folders:

1. `python3 tools/research/corpus_fetch.py --repos tools/research/fixtures/corpus-2026-10-08.jsonl --out DATA`
2. `python3 tools/research/corpus_fetch.py --out READS --stage reads --picks tools/research/fixtures/element-reads-2026-10-09.json`
3. `python3 tools/research/corpus_counts.py --data DATA --labels tools/research/fixtures --earlier-run 2026-10-03T18:00:00Z --reads READS/reads-index.json --out counts.json --repo-list repo-list.md`

Fixtures in `tools/research/fixtures/`:

- `corpus-2026-10-08.jsonl`: the repository list
- `reading-slices-2026-10-08.json`: the 28-repository reading sample
- `picks-2026-10-08.json` and `picks-2026-10-09.json`: every seeded pick, by repository, path and group; for term contexts, only the repository and document kind
- `prior-2026-10-09.json`: the reads before 2026-10-09, for `corpus_sample.py --prior`
- `element-reads-2026-10-09.json`: the 73 files read for the element counts, grouped by the reader
- `of2-security-channel.json` and `of7-labels.json`: reader labels for the SECURITY files and the sampled term contexts, with no file text

Rerun limits:

- A rerun reads each repository as it stands on the day of the rerun. Changes after the freeze move the counts; membership, stars and languages stay as in the list file.
- The scripts reproduce the pattern counts and the sample draws. To reproduce a count confirmed by reading, a fork fetches the picked files with `corpus_fetch.py --stage reads` and repeats the reads.
- The star list holds 207 repositories, and this repository keeps only the 146 corpus repositories.
- A one-off script outside this repository computed the stage 4 counts from the raw data folder: tag patterns, required issue-form fields, sign-off shares, documentation page names and commit subject classes per repository. The three scripts leave out the stage 4 counts.
- Figures from the 2026-10-03 first pass are history: the earlier grades marked "was", the 117 elements, the drafted actions and the 2026-10-03 counts. The first-pass material stays outside the repository, so a fork can rerun only the stage 1 figures.
- Raw data stays out of git, in `.evidence/2026-10-08/research/code-repository/` (git-ignored): about 26 MB of files copied from 146 projects under their own licences, literature copies and reading samples.

## Method and Limits

### Gathering

For each repository, `gh api` fetched, one call at a time:

- listings of the root, `.github/` and `docs/`
- the latest 10 releases with their bodies
- the latest 30 commits with full messages
- the latest 10 closed pull requests with their bodies
- the full file tree, complete for 143 of 146 repositories

`corpus_fetch.py` made about 4,400 calls and hit no rate limit. A later pass read the latest 100 commits of 65 repositories (6,435 commits) to check breaking-change footers. Stage 1 reads on 2026-10-09 added 39 calls.

### Counting Rule

A count is cited only after a sample of the matched files has been read. Each count cell gives two counts: repositories confirmed by reading, then repositories matched by pattern. Two of the first patterns matched the wrong files, and both were tightened before counting.

Count cells read "confirmed by reading / by pattern":

- **Confirmed by reading:** repositories where a person or an agent read the matched file and confirmed the document type.
- **By pattern:** repositories matched by a file name, folder name or keyword rule.

Counts are repositories out of 146 unless a cell says otherwise.

### Reading Samples

Stage 1 drew a rerunnable 28-repository sample for later stages: 4 slices of 7 repositories.

- Each stratum holds the repositories of one language (TypeScript, Go, Python, Rust, JavaScript, Swift or other) in one star tier (40,000 and over; 10,000 to 39,999; 3,000 to 9,999).
- `corpus_sample.py` shuffles each stratum with seed 20261008, then picks the sample round robin over the strata in sorted order.
- The draw gives no extra weight to well-documented repositories.
- Two runs gave identical samples. A test in `tools/research/` reruns the draw and compares the samples.

The 28 repositories: kubernetes/ingress-nginx, swagger-api/swagger-editor, virattt/ai-hedge-fund, altic-dev/FluidVoice, latitude-dev/latitude-llm, pi-hole/pi-hole, remarkjs/react-markdown; prometheus-operator/prometheus-operator, tt-a1i/archify, casey/just, lysyi3m/macos-terminal-themes, strapi/strapi, siderolabs/talos, json-schema-faker/json-schema-faker; spf13/cobra, deepseek-ai/DeepSeek-OCR, deuxfleurs-org/garage, apple/container, apache/apisix, kgateway-dev/kgateway, openai/evals; lint-staged/lint-staged, dograh-hq/dograh, starship/starship, langfuse/langfuse, jerrykuku/luci-theme-argon, junegunn/fzf, amoffat/sh.

Stage 1 reads used their own seeded picks:

- 141 file heads for file names outside the 2026-10-03 patterns
- 88 files from small groups: proposals, decision records, release procedure and release configuration files, review guides, AI policies and sub-folder READMEs
- on 2026-10-09, with seed 20261009: 6 proposals and 3 process pages, 7 decision records and 2 index pages, 14 architecture files, 4 THIRD_PARTY files, 20 sub-folder READMEs, and stored commits, agent files and pull request bodies from 30 repositories

### Skew

An agent labelled each repository by kind, and no second reader checked the labels: 74 developer tools, libraries or frameworks, 33 operations software projects, 30 end-user applications, 5 collections or themes, and 4 research model releases.

- Developer or operator software makes up 73% of the corpus (107 of 146 repositories; 72% to 76% with the borderline labels moved).
- TypeScript, Go and Python make up 64% of the corpus.
- Every share in this document is a ceiling for codebases in general.

Outside check: a study of 10,000 GitHub repositories with 100+ stars ([L80](#graded-sources)) counts the same files. Its authors state the paper is accepted to ICSME 2026. The study figures below were read twice from the HTML version and remain unchecked against the paper.

| File | Outside study | This corpus (by pattern) |
| --- | --- | --- |
| README | 95.3% | 100% |
| LICENSE | 73.1% | 98% |
| CONTRIBUTING | 31.7% | 72% |
| ISSUE_TEMPLATE | 28.2% | 75% |
| CHANGELOG | 27.9% | 42% |
| CODE_OF_CONDUCT | 16.2% | 41% |
| SECURITY | 13.5% | 51% |
| CODEOWNERS | 10.2% | 35% |
| CLAUDE.md | 9.0% | 24% |
| AGENTS.md | 8.5% | 40% |

The study counts exact file names. The corpus counts name patterns at the root, `.github/` and `docs/`. Every corpus share sits above the study share.

### GitHub-Only Hosting

Every corpus repository is hosted on GitHub. The documentation of seven other forges was read: GitLab, Gitea, Forgejo with Codeberg, Bitbucket Cloud, SourceHut, Azure Repos and Gitee.

- Most of the seven forges name README, LICENSE, CODEOWNERS, and issue and pull request templates, each forge in its own folder (`.gitlab`, `.gitea`, `.forgejo`, `.bitbucket`, `.gitee`, `.azuredevops`).
- Outside GitHub, SECURITY, CITATION, FUNDING, CODE_OF_CONDUCT and CONTRIBUTING get no forge-specific handling, apart from the items on GitLab's project overview page.
- Forge and vendor names appear in the tables below only as evidence. Declarations name no forge or vendor; forge-specific file names and paths go into aliases or guidance.

### Community Evidence

On 2026-10-08, 29 developer-community pages were read: 24 Hacker News threads and 5 blog or article pages.

- Every community page is grade C: evidence of practice and dispute, never the only basis for a document type.
- The fetch tool returned a model-written summary of each page, so the page wording stays unchecked.
- Reddit refused every fetch. No Medium page surfaced.
- No page surfaced for license-file, support-policy, threat-model or package-readme, and no thread about the CODEOWNERS or SECURITY.md file.
- No document type outside the candidates surfaced.

### Grades

Sources:

- **A:** a standards body, a specification with broad independent adoption, or a peer-reviewed meta-analysis or systematic review. A specification kept by one maintainer or one project without that adoption is B.
- **B:** documentation from a platform or foundation with wide adoption, or a peer-reviewed primary study.
- **C:** a practitioner essay, blog post, talk, preprint, other study without peer review, or vendor material.

A claim rests on its strongest source. A source that sets a document type's contents is strong; a source that gives only file syntax or placement is thin.

Candidates:

- **High:** support from both sides, corpus and A/B literature, and no other candidate with the same action.
- **Medium:** support from one side, or from both sides with a shared action.
- **Low:** thin support. The row stays as a lead.
- **Excluded:** popular but unsupported or contradicted. The row states the reason.

Elements follow the same scale. High: an A/B source sets the element, and the corpus shows the element in 2 or more repositories. Medium: only one of the two conditions holds. Low: neither condition holds.

### One-Side Rule

One side counts as support in three cases:

- A file appears in about 6 or more repositories, and a sample read confirms the type.
- A file appears in 3 to 5 repositories, and an A/B source sets its contents.
- An A/B source sets the contents, even with no files in the corpus.

Thinner support is Low.

### Floor for High

High needs three conditions:

- at least 10 repositories confirmed by reading
- A/B literature that sets the contents
- no other candidate with the same action

Below 10 confirmed repositories, a row is at most Medium.

### Overlap Test

Two candidates form one document type only when they share an action: the same actor makes the same decision. Shared content becomes a shared question for stage 3; a grade never drops for shared content. In the overlap column, "content only" means shared content, and "shares an action" means the two candidates may be one document type.

When stage 2 folds a shared-action partner into a candidate as an alias or as instances, the partner and the candidate form one document type. The grade then rests on the merged evidence and the [floor for High](#floor-for-high).

### Orthogonality

The code-repository preset stands alone. This universe spec declares each document type from this preset's evidence, in this preset's words. No declaration defers to, reuses or depends on another preset. The overlap test ignores similar document types in other presets.

## Document Types

The 30 candidates from the 2026-10-03 pass, rechecked against the frozen corpus. A grade cell such as "Medium; High once stage 2 folds in N19" gives the current grade, then the grade after the named stage 2 fold. The current grade applies until stage 2 decides the fold. Question numbers (Q1 to Q13) point to [Questions for Stage 2](#questions-for-stage-2).

| # | Candidate | Confirmed by reading / by pattern | Literature (grade) | Overlap | Grade | Basis |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | readme | 10 (headings of 10 seeded READMEs) / 146 | GitHub Docs About READMEs, five items (B); Google READMEs guide (B); Azure Repos README page, three audiences (B) | No shared action. Package front pages (C29) untested against readme | **High** | Floor met at 10 confirmed repos; B sources set the contents. Stage 2 tests package front pages against readme (Q2); readme meets the floor without the front pages |
| C2 | license-file | 143 (all file heads read; 91 carry a dated copyright line) / 143 | REUSE 3.3 (A); SPDX license expressions 2.3.1 (A); Baseline LE-03.01 names a LICENSE or COPYING file or a `LICENSES/` folder (B) | LICENSING.md (2 repos) and one adopter-facing THIRD_PARTY file share the action and enter as aliases at stage 2. Content only with NOTICE (N1) | **High** | Floor met. LICENSING.md and the adopter-facing THIRD_PARTY file join as aliases, so the grade rests on the merged evidence (Q4) |
| C3 | release-notes | 20 (28 release bodies read) plus 62 changelog heads / 133 (55 both, 71 notes only, 7 file only) | Keep a Changelog 2.0.0 (B); SemVer 2.0.0 for versions (A); Baseline BR-04.01, a change log with each release (B) | Stage 2 reopens the changelog-file fold (FE3): Keep a Changelog 2.0.0 separates the changelog from release notes | **High** | Floor met. 46 repos publish generated notes in most releases |
| C4 | security-policy | 74 reporting policies (all 77 files read; 66 name a channel, 7 point elsewhere, 1 placeholder, 14 short pointers) / 75 | GitHub Docs security policy (B); Baseline VM-01.01, VM-02.01, VM-03.01 (B) | No shared action with SECURITY_CONTACTS (N11) | **High** | Floor met |
| C5 | contributing-guide | 26 heading lists / 105 (13 stubs; 13 only in `.github/` or `docs/`) | GitHub Docs contributor guidelines (B); Baseline GV-03.01, GV-03.02 (B) | Content only with DEVELOPMENT.md (N2). AI rules inside CONTRIBUTING: Q11 and Q12 | **High** | Floor met |
| C6 | commit-message | 10 of 10 seeded repos (stored full messages) plus 15 messages read for breaking changes / 146 (4,357 commits; 59% with a body; 65 repos mostly Conventional Commits) | Git and kernel patch guides (A); Conventional Commits 1.0.0 (A); DCO 1.1 (B) | Content only with change-description (C10) and decision-record (C17) | **High** | Floor met. Breaking-change footers are nearly unused (V4) |
| C7 | code-of-conduct | 60 headers read (48 full text, 12 pointers) / 60 | Contributor Covenant 2.1, the text the corpus uses, and 3.0, the current version (B) | None | **High** | Floor met. No corpus file uses Covenant 3.0: 19 files use 1.2 to 1.4, and 23 files use 2.0 or 2.1 |
| C8 | agent-instructions | 10 of 10 seeded repos (AGENTS.md or CLAUDE.md) plus 21 pointer files / 67 by the 2026-10-03 patterns (68 with any named file; 73 with tool folders) | agents.md site (B); Claude Code docs (B); GitHub Copilot custom instructions (B); GitLab Duo AGENTS.md (B) | Content only with architecture-overview (C18): an architecture section in the agent files of 15 of 66 repos | **High** | Floor met. AGENTS.md is the shared name (OF4) |
| C9 | issue-report | 262 template files parsed in 105 repos (163 forms, 99 Markdown); duplicate-search lines read in 6 of 6 / 110 | Docs from five forges set syntax and placement only (B); Baseline DO-02.01 requires a defect-reporting guide and leaves its contents open (B) | None | **Medium** | Corpus side only: no A/B source sets the contents |
| C10 | change-description | 10 of 10 seeded pull request bodies; 78 templates parsed / 128 of 144 sampled repos have a median closed pull request body over 200 characters (124 without bot pull requests; the count of 128 includes template text); template in 78 of 146 | Google CL descriptions (B), checked against the source Markdown: problem, approach, shortcomings, background | Content only with commit-message: a reviewer decides whether to merge, and a later reader of history decides whether to keep or undo a change. 19 of 80 squash-merging repos copy the pull request body into the commit. Content only with design-proposal (C16) | **High** | Maintainer decision, 2026-10-09; the floor is also met. The id stays forge-neutral, and "pull request description" goes in the alias. Commenters (C) dispute whether the reason for a change belongs in the commit message or the pull request description; the grade stays High |
| C11 | code-owners | 51 files parsed / 51 (55 counting approval-rule OWNERS and owners.yaml files) | Six forges document the file, syntax and placement only (B) | Shares an action with maintainers-list as drafted on 2026-10-03, and with OWNERS_ALIASES (N12) | **Medium** | Medium on both counts: no A/B source sets the contents, and the row shares actions with maintainers-list and OWNERS_ALIASES. 27 files have a catch-all line |
| C12 | upgrade-guide | 6 (all 8 matches read; 6 real guides) / 8 | Keep a Changelog 2.0.0 puts substantial upgrade steps in a migration guide or the release notes (B); SemVer, implied (A) | None. Question D4 stays open | **Medium** | 6 confirmed repos, below the floor |
| C13 | maintainers-list | 19 repos read (26 files): 10 rosters, 3 pointers, 5 approval-rule files, 1 work-polling guide / 19. 10 repos keep credit lists, counted apart | CNCF MAINTAINERS.md (B); Baseline GV-01.01, GV-01.02 (B) | Shares an action with code-owners as drafted on 2026-10-03. Content only with governance-document | **Medium** | Shared action. Under a narrowed action the corpus side holds 6 rosters, below the floor (Q1) |
| C14 | governance-document | 8 read (6 documents, 2 pointers) / 8 | CNCF GOVERNANCE.md (B); Baseline GV-01.02 (B) | Content only with maintainers-list | **Medium** | Below the floor |
| C15 | documentation-set | 6 docs folders read; 76 `docs/` listings and 68 second-level folder lists / 87 | Diátaxis sets the kinds (C); Baseline DO-01.01 and SA-02.01 require user guides and interface descriptions and leave their contents open (B) | None. INSTALL, GETTING_STARTED and TROUBLESHOOTING wait on Q6 | **Medium** | Corpus side only: the contents rest on a C source |
| C16 | design-proposal | 11 (OpenAPI, prometheus-operator, kgateway, alloy, external-dns, harbor, cua, ingress-nginx, beads, backstage, gateway-api); 10 without beads, where 1 of 3 reads is a proposal / 12 by file tree | PEP 1 (B); Rust RFC template (B); CNCF DESIGN-PROPOSALS.md (B) | Content only with decision-record (an approver before the work; a later reader after the decision) and with change-description (approve an approach; merge a built change) | **High** | Floor met. Backstage keeps `beps/` next to `docs/architecture-decisions/`, and its proposal README separates the two folders |
| C17 | decision-record | 7 (backstage, coolify, diagram-design, beads, n8n, PostHog, obsidian-tasks; 19 records read) / 7 by file tree | AWS ADR process (B, not reread); MADR 4.0.0 (B) | Content only with design-proposal, and with commit-message (one change; a standing rule across many changes). Untested against change-description: the AWS source has reviewers cite decision records before a merge (Q9) | **Medium** | 7 confirmed repos, below the floor |
| C18 | architecture-overview | 18: 15 whole-system and 3 subsystem documents read; 2 more subsystem explanations by head (Ghost, PostHog) / 37 (34 repos by file name anywhere in the tree, 3 by folder name only) | Baseline SA-01.01, design documentation of all actions and actors, for contributors and security reviewers (B) | Shares an action with the subsystem explanations in N19. Content only with agent-instructions, package-readme and documentation-set | **Medium; High once stage 2 folds in N19** | The 15 whole-system documents alone meet the floor. The row shares an action with N19 and stays Medium until stage 2 decides the fold. With the subsystem explanations as instances, the grade rests on the merged evidence (Q3) |
| C19 | funding-file | 53 files parsed / 53 (`github:` key in 47 files) | GitHub Docs sponsor button, syntax only (B) | None | **Medium** | No A/B source sets the contents. No other forge documents the file |
| C20 | citation-file | 6 parsed / 6 | Citation File Format 1.2.0 (A) | None | **Medium** | Below the floor |
| C21 | bill-of-materials | 0 files at the three locations; 1 provenance record read (odysseus `THIRD_PARTY_PROVENANCE.json`) / SBOM workflows in 2 repos, 2 README mentions, an `sbom` folder in 1 repo | CISA 2026 minimum elements, 17 fields (B); SPDX (A) | None | **Medium** | Literature side only. Workflow contents are unread, so the corpus side is under-measured. An SBOM may be a release output rather than a written document |
| C22 | ai-use-policy | 11 policy files read / 45 (policy file 11, CONTRIBUTING section 31, pull request template field 24) | Linux Foundation Generative AI policy (B) | 34 of the 45 repos keep the rules inside contributing-guide or change-description. The action test has not run (Q11) | **Medium** | Held at Medium until stage 2 runs the action test (Q11). 34 of the 45 repos keep the rules inside other types; with a shared action, the rules become elements of contributing-guide. With shared content only, the row meets the floor |
| C23 | support-policy | 4 read / 4; README help sections in 70 (keyword) | GitHub Docs support resources (B); Baseline DO-04.01, DO-05.01 name SUPPORT.md for support scope and duration (B) | The two B sources give SUPPORT.md two meanings: where to ask for help, and how long releases get support. Action test not run (Q13) | **Medium** | 4 confirmed repos, below the floor |
| C24 | threat-model | 3 read (apisix, kgateway, odysseus) / 3 | Baseline SA-03.02 requires threat modelling and attack-surface analysis; publishing the result is optional (B) | None | **Medium** | One-side rule: 3 to 5 repos with a B source. Below the floor |
| C25 | compatibility-policy | 4 read (prometheus stability page, 3 deprecation pages) / 4 | SemVer 2.0.0 (A); Baseline DO-04.01, DO-05.01 (B) | Content with security-policy supported versions (42 SECURITY files) and with support-policy (Q13) | **Medium** | 4 confirmed repos, below the floor |
| C26 | release-procedure | 17 procedures read for headings / 17 (18 repos have a RELEASE or RELEASING file; 1 is a changelog) | CNCF RELEASES.md: creating a release, release roles, cadence, versioning, supported versions (B) | No shared action. Content with compatibility-policy (supported versions) | **High** | Floor met: 17 confirmed repos, a B source sets the contents, no shared action. 5 procedures name a release owner; 9 procedures give a schedule |
| C27 | review-guide | 4 read (backstage, kyverno, langfuse, archify) / 4 | CNCF REVIEWING.md (B) | None | **Medium** | 4 confirmed repos, below the floor |
| C28 | roadmap | 12 files read in 11 repos / 11 | None at A or B | None | **Medium** | One-side rule: 6 or more repos with a sample read, so corpus side only. Medium by maintainer decision, 2026-10-09 |
| C29 | package-readme | 26 sub-folder READMEs read: 11 folder notes in 11 repos, 8 package or tool front pages, 1 contributing guide, 1 test guide, 5 noise files / 99 repos with a sub-folder README (64 with 5 or more sub-folder READMEs; rule in V12) | Google READMEs guide: contents, purpose, contacts, status, usage, links (B) | Readers use sub-folder READMEs for two actions: find the right files in a folder (a folder note), or decide whether and how to use a package (a package front page). Neither action is shared with contributing-guide. Front pages untested against readme | **Medium; High on the folder-note action** | The folder-note action meets the floor with 11 confirmed repos (10 repos if the alloy component page counts as a subsystem explanation). Stage 2 picks the action (Q2) |
| C30 | build-provenance | 0 files or workflows / 1 README mention (kyverno) | SLSA v1.2 (A); Baseline DO-03.01, DO-03.02, release verification instructions (B) | None | **Medium** | Literature side only. Provenance may be a pipeline output rather than a written document |

Tally: 11 High (C1 to C8, C10, C16, C26), 19 Medium, 0 Low, 0 Excluded.

## Newly Observed Document Types

File names outside the 2026-10-03 patterns, found at the root, in `.github/` or in `docs/` (or in file trees where stated).

| # | Candidate | Confirmed by reading / by pattern | Literature (grade) | Overlap | Grade | Basis |
| --- | --- | --- | --- | --- | --- | --- |
| N1 | NOTICE | 8 read as attribution notices / 13 | Apache License 2.0 section 4(d), binding on Apache-2.0 works (B) | Shares an action with the 6 redistributor-facing THIRD_PARTY files. Content only with license-file. The minio and archify files address adopters, so redistributors are not the only readers | **Medium; High once stage 2 folds in the THIRD_PARTY files** | 8 confirmed repos, below the floor. With the redistributor-facing THIRD_PARTY files folded in, the grade rests on the merged evidence: 13 of 18 repos confirmed by reading (Q4) |
| N2 | DEVELOPMENT.md, HACKING.md | 6 read in full / 9; CONTRIBUTING links to the development document in 8 of 9 repos | Baseline DO-07.01 sets the build part only (B) | Shares an action with BUILD (N3). Content only with contributing-guide | **Medium** | Below the floor. After an N3 fold, 10 confirmed repos (Q5) |
| N3 | BUILD.md, BUILDING.md | 4 read / 4 | Baseline DO-07.01 (B) | Shares an action with N2. May share an action with install from source (N4) | **Medium** | One-side rule: 3 to 5 repos with a B source. Below the floor |
| N4 | INSTALL, INSTALL.md | 4 substantive of 5 read / 9 repos with a document (11 name matches; 2 are shell scripts) | None read (GNU Coding Standards unread: HTTP 429) | Content only with readme. Untested with N3 and documentation-set | **Medium** | One-side rule: 6 or more repos with a sample read, so corpus side only. Medium by maintainer decision, 2026-10-09 |
| N5 | GETTING_STARTED, `docs/getting-started` | 3 single pages read / 3 pages, plus 6 `docs/` folders seen in trees only | Diátaxis tutorials (C); Baseline DO-01.01, existence only (B) | Content only for the 3 pages. The 6 folders are sections of documentation-set | **Low** | One-side rule: 3 to 5 repos with no A/B source that sets the contents |
| N6 | FAQ | 2 read / 10 by name (28 in file trees) | None at A or B | None | **Medium** | One-side rule: 6 or more repos with a sample read, so corpus side only. Medium by maintainer decision, 2026-10-09 |
| N7 | TROUBLESHOOTING | 4 read, 3 substantive / 7 (husky `docs/troubleshoot.md` added) | None at A or B | Content only with the error fixes in documentation-set | **Medium** | Corpus side only. Low if stage 2 reads the 3 substantive files as thin |
| N8 | ADOPTERS.md | 2 read / 6 | CNCF ADOPTERS.md (B) | None | **Medium** | Below the floor |
| N9 | DCO, CLA.md | 6 read (3 DCO, 3 CLA) / 6 | DCO 1.1 sets the DCO text (B); Baseline LE-01.01 accepts a DCO or a CLA (B) | DCO and CLA share an action with each other. Content only with commit-message sign-off. The grade stays Medium although DCO 1.1 sets the DCO text | **Medium** | Below the floor |
| N10 | LICENSING.md, THIRD_PARTY_* | 10 read (LICENSING 2 of 2; THIRD_PARTY 8 of 8) / 10 (9 by the name pattern; a JSON provenance file adds 1 repo) | REUSE 3.3 on per-file licensing (A) | Splits by action. LICENSING.md shares an action with license-file. THIRD_PARTY: 6 redistributor-facing files share an action with N1, 1 adopter-facing file shares an action with license-file, 1 provenance record counts as bill-of-materials evidence | **Medium** | Each part shares an action with another candidate, so the grade stays Medium; the candidate dissolves at stage 2 (Q4) |
| N11 | SECURITY_CONTACTS; SECURITY-CREDITS.md | 4 read / 4; SECURITY-CREDITS 1 / 1 | No source sets the contents. Baseline VM-02 is written for reporters, and the files turn reporters away | No shared action with security-policy: the files hold no report channel, and the actor is a response team triaging an embargoed report | **Low** | One-side rule: 3 to 5 repos with no A/B source that sets the contents. 3 files share one project family's format |
| N12 | OWNERS_ALIASES | 2 read / 2, one project family | None | Shares an action with code-owners | **Low** | Thin support |
| N13 | TESTING.md | 2 read / 4 | None | None | **Low** | Thin support |
| N14 | TRADEMARK.md | 2 read / 3 | None | None | **Low** | Thin support |
| N15 | TRANSLATIONS.md; README in other languages | 3 read / 3 and 8 | None | A translated README is a readme alias, not a separate type | **Low** | Thin support |
| N16 | PRIVACY.md | 2 read / 2 | None | None | **Low** | An app's privacy policy covers the product, outside the codebase |
| N17 | llms.txt, llms-full.txt | 2 read / 2 | None read | None | **Low** | Thin support |
| N18 | Agent planning folders (`docs/superpowers/{plans,specs}`, `docs/plans`) | 6 read / 4 and 2 | None | None | **Excluded** | Working notes in one tool's output format are an internal convention and never become a candidate. Declarations name no vendor |
| N19 | `docs/internal`, `docs/codebase` | 3 heads read / 3 | No source sets per-subsystem guides | The subsystem explanations (Ghost, PostHog) share an action with architecture-overview. crawl4ai `browser.md` is a function table, a lead for package-readme. The folder names mark no type: PostHog `docs/internal/` also holds a runbook, CI notes and an environment-variable list | **Low** | Thin support; the subsystem explanations wait on the fold (Q3) |
| N20 | `docs/blog` release posts; `docs/releases` | 6 read / 3 and 6 | None | Evidence for the changelog question (D2) | **Low** | Low as document types |
| N21 | Runbook, postmortem or incident, and glossary paths | 0 read / 2, 4 and 6 in file trees | None | Untested | **Low** | Leads only |
| N22 | Rule files under `.github/` (pull request documentation, pull request titles, commit convention) | 1 each read / 1 each | None | Evidence for the commit format in contributing-guide | Not a type | Content of an existing type |
| N23 | MAINTENANCE.md, TODO, PROGRESS, PROJECT_STATUS | 6 read / 9 | None | No shared meaning across the 6 files read | **Excluded** | Five different things in 6 files; a personal to-do list is an internal convention |
| N24 | Configuration: `.github/release.yml` (5), DISCUSSION_TEMPLATE (7), `.github/instructions` (3), tool folders | 3 of 5 release.yml files read; others by name only / as listed | None | `.github/instructions` holds agent path rules (agent-instructions); release.yml configures generated notes (factor F1) | Not a type | Configuration files |

Tally: 0 High, 9 Medium, 11 Low, 2 Excluded, 2 not a type. No new type reaches High.

## Element Grades That Moved

The 2026-10-03 candidates hold 117 elements. The rows below list the elements with a changed grade or basis at stage 1. Element names are working labels; stage 3 writes every element id and question in this preset's words.

| # | Element | Corpus | Literature (grade) | Overlap | Grade | Basis |
| --- | --- | --- | --- | --- | --- | --- |
| EL1 | license-file: copyright holder | 91 of 143 file heads carry a dated copyright line | REUSE 3.3 (A) | Shared question with NOTICE (stage 3) | **High** (was Medium) | Both sides |
| EL2 | release-notes, upgrade-guide: upgrade steps | 5 of 7 read correct / release bodies in 24 repos | Keep a Changelog 2.0.0 (B) | None | **High** (was Medium) | Both sides |
| EL3 | release-notes, change-description: release-note line | 57 of 92 repos write most release lines as the pull request title (V5) | GitHub Docs automatically generated release notes (B) | Shared element | **High** (holds, new basis) | The 2026-10-03 figure (15 of 28 repos) did not reproduce; the same measure gives 11 repos (V7) |
| EL4 | commit-message: breaking change | Release bodies in 32 repos. In commits: 3 footers in 1 repo and 15 `!` markers in 4 repos (latest 100 commits of 65 repos) | Conventional Commits 1.0.0 (A) | Shared with release-notes and change-description | **High** (holds) | Flag for stage 3: nearly unused in commits |
| EL5 | contributing-guide: required evidence; change refusal | 8 of 10 and 10 of 10 read correct | Baseline GV-03.02 asks for requirements for acceptable contributions (B), which may set one of the two elements | None | **Medium** each (holds) | Flag for stage 3 |
| EL6 | code-of-conduct: five elements | The corpus uses Covenant 1.2 to 2.1 | Contributor Covenant 2.1 (B) | None | **High** (holds on 2.1) | Flag for stage 3: Covenant 3.0 drops the enforcement-responsibilities section and moves consequences into a repair ladder |
| EL7 | agent-instructions: check with a person first | 4 of 8 read correct / 9 repos; 49 repos give prohibitions instead | None | None | **Medium** (was Low) | Corpus side |
| EL8 | issue-report: duplicate search | 6 of 6 read correct / 29 repos | None | None | **Medium** (was Low) | Corpus side |
| EL9 | code-owners: default owner | 27 of 51 files have a `*` line | None | None | **Medium** (was Low) | Corpus side |
| EL10 | upgrade-guide: upgrade order; rollback; upgrade check | 5, 2 and 5 of the 6 guides | None | None | **Medium** each (was Low) | Corpus side |
| EL11 | governance-document: changing the governance | 2 of 8 files | CNCF governance template, charter modification section (B) | None | **High** (was Medium) | Both sides |
| EL12 | documentation-set: docs version | 6 repos keep versioned docs (file-tree names, unread) | None | None | **Medium** (was Low) | Corpus side, by name |
| EL13 | design-proposal: goals and non-goals; open questions; status | Non-goals heading in 17 of 36 files (8 repos); open questions in 5 of 36 (3 repos; 0 of the 6 new reads); status field in 23 of 36 (9 repos) | CNCF DESIGN-PROPOSALS.md: goals, non-goals, key questions, optional status (B); Rust RFC template: unresolved questions (B) | Status, alternatives and replacement links are shared questions with decision-record (stage 3) | **High** each (goals and non-goals; open questions; status) | Both sides |
| EL14 | decision-record: the decision; accepted consequences; superseding decision | Decision heading in 16 of 19 records (6 repos); consequences heading in 16 of 19 (7 repos); a superseding link in 0 of 19 | AWS ADR process (B, not reread); MADR 4.0.0 (B) | Reasoning is shared content with commit-message | **High** each (decision; consequences); superseding decision **Medium** | Both sides for the first two elements; literature only for the superseding decision |
| EL15 | architecture-overview: components and responsibilities; data flows | Components in 18 of 18 confirmed documents; a flow, pipeline, lifecycle or request-path heading in 12 of 18 | Baseline SA-01.01, actions and actors (B) | Components is a shared question with agent-instructions; folder purpose with package-readme (stage 3) | Components **High**; data flows **Medium** | Data flows: corpus side only, unless stage 3 counts the actions in SA-01.01 as data flows |
| EL16 | funding-file: sponsored people; sponsor tiers | `github:` accounts in 47 files; tiers in 0 files | None | None | Sponsored people **Medium** (was Low); sponsor tiers **Low** (was Medium) | Tiers live on the platform |
| EL17 | ai-use-policy: contributor accountability | 10 of 11 policy files | Linux Foundation Generative AI policy (B) | None | **High** (was Medium) | Both sides |
| EL18 | release-procedure: release steps; release owner; release schedule | 17, 5 and 9 of 17 procedures | CNCF RELEASES.md (B) | None | **High** each (was Medium) | Both sides |
| EL19 | roadmap: declined ideas; roadmap date | 2 and 5 of 12 files | None | None | **Medium** each (was Low) | Corpus side |
| EL20 | package-readme: directory purpose | 11 folder notes in 26 reads | Google READMEs guide (B) | Folder purpose is a shared question with architecture-overview | **High** (was Medium) | Both sides |
| EL21 | commit-message: sign-off | 52 repos, 535 commits | Git and kernel patch guides (A); DCO 1.1 (B); Baseline LE-01.01 (B) | References the DCO and CLA type if stage 2 keeps N9 | **High** (holds) | Both sides |
| EL22 | bill-of-materials: components, versions, links, tool | No files | CISA 2026 minimum elements, 17 fields (B) | None | **Medium** each (holds) | Recheck at stage 3 against the 17 fields |
| EL23 | package-readme: directory status; directory owner | Status in 2 of 26 reads (hedge_fund, cuabot); owner in 0 of 26 | Google READMEs guide: status, points of contact (B) | None | Status **High** (was Low); owner **Medium** | Status: both sides; owner: literature side |

## Factors and Frame Lead

Stage 4 declares this preset's frames and factors from this preset's evidence.

| # | Candidate | Corpus | Literature (grade) | Grade | Note |
| --- | --- | --- | --- | --- | --- |
| F1 | changelog-production (factor) | 405 release lines compared. 46 repos publish generated notes in most releases; 60 repos use mostly pull-request-reference lines; `.changeset` in 10 repos, towncrier-style in 3 repos, reno in 1 repo | Keep a Changelog 2.0.0: machines draft, humans curate (B) | **Medium** | Stage 4 needs cases across every value |
| F2 | commit-convention (factor) | 65 repos mostly Conventional Commits, 75 repos neither; an area-prefix pattern in 6 repos (unread) | Conventional Commits 1.0.0 (A); community dispute (C) | **Medium** | Stage 4 |
| F3 | assurance-level (factor) | Scorecard badges in 9 READMEs, Best Practices badges in 12 READMEs | OpenSSF Baseline v2026.08.28, three levels (B) | **Medium** | Stage 4 |
| F4 | intake-stance (factor) | 10 read / 44 repos ask for an issue or discussion before a pull request | Baseline GV-03.01 lets a project state that it accepts no public contributions (B) | **Medium** | Content shared with the contribution-route element |
| F5 | primary-reader (factor) | 67 repos keep an agent file | No source sets the dimension | **Low** | Stage 4 |
| F6 | versioning-scheme (factor) | 11 repos mention semantic versioning (pattern) | SemVer 2.0.0 (A) | **Low** | Stage 4 |
| F7 | repository-kind (frame lead) | 146 descriptions read and labelled by an agent, unchecked by a second reader: developer tool, library or framework 74; operations software 33; end-user application 30; collection or theme 5; research model release 4 | None | **Low** | Stage 4 needs cases across every observed kind |

## Refusals and Exclusions

Folded candidates join another candidate. Excluded candidates leave the list, each with a reason. N18 and N23 in [Newly Observed Document Types](#newly-observed-document-types) are also excluded, and N22 and N24 are not types.

| # | Candidate | Evidence | Literature (grade) | Result | Reason |
| --- | --- | --- | --- | --- | --- |
| FE1 | pull-request-template, folded into change-description | 78 templates parsed | GitHub and Azure Repos template docs (B) | Fold holds | A template seeds the description and shares an action with change-description; GitHub leaves the contents to the project |
| FE2 | issue-form, folded into issue-report | 163 form files parsed | Forge docs (B) | Fold holds | The form is the input side of the report; same action |
| FE3 | changelog-file, folded into release-notes | 62 changelog heads; 7 repos with a file only | Keep a Changelog 2.0.0 separates the changelog file from release notes (B); Baseline BR-04.01 (B) | Reopened | Stage 2 decides (D2) |
| FE4 | change-note, folded into the release-note line element | 4 read / 22 repos tell contributors to write a change note (32 counting a release-note field in the pull request template); 13 repos use note-file tools | Keep a Changelog 2.0.0 (B) | Fold holds on the new basis | Same element |
| FE5 | version-number, folded into the version element | Not counted | SemVer 2.0.0 (A) | Fold holds | A field in each release |
| FE6 | documentation badges, folded into guidance on project status | 106 repos, 586 badge images | Badge study, ICSE 2018 (B) | Fold holds | A badge is evidence only when a service checks the claim |
| FE7 | docs-as-code, folded into guidance | Not counted | Write the Docs, Google style guides (B); community pages agree that docs drift when kept apart from the code (C) | Fold holds | A practice with no document of its own |
| FE8 | Scorecard and Best Practices badges, folded into the factor assurance-level | 9 and 12 READMEs | Scorecard checks (B) | Fold holds | A measurement with no document of its own |
| FE10 | README table of contents as a required section | 17 READMEs with a contents heading | standard-readme (B, one maintainer); GitHub Docs (B) | Excluded | Only standard-readme requires the section; GitHub generates an outline for every Markdown file |
| FE11 | Static badges as evidence | Not counted | Badge study, ICSE 2018 (B) | Excluded | Only assessment badges track quality |
| FE12 | Sponsor and star-history blocks | Not counted | None | Excluded | No source supports the blocks |
| FE13 | Git log as changelog content | Not counted | Keep a Changelog 1.1.0 and 2.0.0 (B) | Excluded | Keep a Changelog names commit-log diffs a bad practice |
| FE14 | Agent file as rule enforcement | Not counted | Claude Code docs, reread 2026-10-09 (B); GitLab review instructions (B); community pages agree (C) | Excluded | The vendors treat agent files as context and enforce rules with hooks or checks |
| FE15 | Scorecard score as a vulnerability predictor | Not counted | Scorecard and security outcomes preprint (C, not reread) | Excluded | Scores explain little of the variance in reported vulnerabilities |
| FE16 | standard-readme compliance badge as evidence | Not counted | Badge study, ICSE 2018 (B) | Excluded | Self-applied badges are weak signals |
| FE17 | Org-wide default health files as a document type | Not counted | GitHub Docs default community health files (B); Gitee also reads a namespace-level repository (B) | Excluded | A placement rule, kept as a fact for scaffolding |

Row FE9 was withdrawn before publication; the other row numbers stay unchanged.

Sources refused or unreadable:

- GNU Coding Standards: the server answered HTTP 429, and the run stopped. INSTALL and NEWS files stay without a source.
- Reddit: every fetch refused. No Reddit claim appears in this document.
- The SECURITY.md journal paper (L55): the publisher blocks automated access. The authors' preprint and dataset were read instead.

## Recounts

Every load-bearing number was rerun or recounted from the raw outputs. Rows marked "Corrected" changed at stage 1.

| # | Item | Value | Note |
| --- | --- | --- | --- |
| V1 | Corpus and freeze | 146 of 207; frozen 2026-10-08 23:54 EDT | Holds |
| V2 | File counts by pattern | readme 146, license 143, security 75, contributing 105, code of conduct 60, codeowners 51, funding 53, citation 6, issue templates 110, pull request template 78, changelog 62 | Holds |
| V3 | Release notes, changelog file or both | 133: 55 both, 71 notes only, 7 file only | Holds |
| V4 | `BREAKING CHANGE` footers | 0 in 4,357 commits; 3 in 6,435 commits of 65 repos, all in grafana/alloy | Holds |
| V5 | Release lines equal to the pull request title | 257 of 405 lines (63%); 57 of 92 repos | A line matches when the line contains the title or the title contains the line |
| V6 | Repos with pull-request-form notes or a change-note tool | 69 of 146: repos with a change-note file tool (`.changeset`, towncrier-style, reno) plus the 60 repos whose notes are mostly pull request references. 74 counting all eight release-note tools named on 2026-10-03 | The count depends on the change-note tools in the definition |
| V7 | Same measure on the 28 repos read on 2026-10-03 | Either form 11; mostly pull request lines 8; change-note tooling 4 (backstage, lint-staged, pdm, pipx) | Corrected from 5 repos |
| V8 | Agent files | AGENTS.md 59, CLAUDE.md 35, both 29; CLAUDE.md is a pointer in 14 repos and an identical copy in 12 repos | Holds |
| V9 | AI rules in any form | 45: CONTRIBUTING 31, pull request template 24, policy file 11 | Holds |
| V10 | Design-proposal folders | 12 repos by file tree (backstage `beps/` added); 11 confirmed by reading (10 without beads); 36 files read from 12 repos | Corrected from 11 repos |
| V11 | Decision-record folders | 7 repos by file tree (obsidian-tasks added); 7 confirmed by reading; 19 records read | Corrected from 6 repos |
| V12 | Sub-folder READMEs | 99 repos (64 with 5 or more sub-folder READMEs; 2,968 files) | Rule: a README in a sub-folder, excluding paths with a `docs`, `examples`, `tests` or `templates` folder anywhere, vendored folders (`vendor`, `third_party`, `node_modules`, `Pods`, `Carthage`, `bower_components`) and locale copies (`locales`, `i18n`, `l10n` or `translations` followed by a language code). Corrected from 100 and 65 repos. A pattern count; confirmed folder notes come from reading (C29) |
| V13 | CODEOWNERS and MAINTAINERS | 12 repos have both files; 58 repos have at least one of the two files | Corrected from 13 and 57 repos |
| V14 | Developer or operator share | 107 of 146 (73%) | Holds |
| V15 | OpenSSF Baseline v2026.08.28 | 41 controls, 65 requirements; first required at levels 1, 2 and 3: 25, 19 and 21 requirements | Holds |
| V16 | SECURITY.md study dataset | 772 segments in 8 categories | Holds |
| V17 | Baseline items on written documents | VM-01.01, VM-02.01, VM-03.01, VM-04.01, QA-02.02, LE-03.01, GV-03.01, GV-03.02, DO-01.01, DO-02.01, DO-07.01; also BR-04.01, DO-03.01, DO-03.02, DO-04.01, DO-05.01, GV-01.01, GV-01.02, GV-04.01, SA-01.01, SA-02.01, SA-03.02, LE-01.01 | SA-03.02 requires threat modelling; publishing the result is optional |
| V18 | Architecture documents | 34 repos by file name anywhere in the tree, plus 3 by folder name only (coolify, istio, kgateway). Confirmed: 15 whole-system and 3 subsystem documents; in the seeded sample of 10, 5 confirmed, 1 borderline and 4 other kinds | Corrected from 36 repos. File-name rule: a `.md`, `.mdx` or `.rst` file whose name contains "architecture", excluding agent-tool and skill folders, test folders, `.changeset` and locale folders. The 2026-10-03 count of 11 matches covered three locations only |
| V19 | THIRD_PARTY files by action | 8 repos, all read: 6 redistributor-facing (turbo-fieldfare, diagram-design, beads, d2, opencost, oxc), 1 adopter-facing (archify), 1 provenance record (odysseus, JSON) | Corrected from 4 files read |
| V20 | Folder notes among sub-folder READMEs | 11 folder notes in 11 repos, from 26 reads (6 earlier, 20 drawn with seed 20261009) | Recount holds; 10 repos if the alloy component page counts as a subsystem explanation |
| V21 | change-description, corpus side | 128 of 144 sampled repos have a median closed pull request body over 200 characters; 124 without bot pull requests; 19 of 80 squash-merging repos copy the pull request body into the commit | Holds |
| V22 | Row counts corrected by the overlap recheck | decision-record 7 repos by tree; architecture-overview 9 documents read before 2026-10-09; INSTALL 9 repos with a document (2 of 11 matches are shell scripts); TROUBLESHOOTING 7 (husky added); GETTING_STARTED 3 single pages; DEVELOPMENT linked from CONTRIBUTING in 8 of 9 repos; code-owners 55 counting approval-rule OWNERS files | Applied in the document-type tables |

## Open Facts

Facts left open after the 2026-10-03 pass, each with its stage 1 answer.

| # | Fact | Answer |
| --- | --- | --- |
| OF1 | Corpus size | 146 of 207 starred repositories with 3,000+ stars, as of 2026-10-08 23:54 EDT |
| OF2 | Element-level prevalence | CONTRIBUTING (105 repos): dev setup 62, required evidence 57, test command 44, issue first 44, commit format 33, AI rules 31, refusal rules 29. Pull request templates (78 repos): description 65, checklist 62, verification 55, docs 55, related issue 50, change type 34, screenshots 27, AI 24, release note 19, breaking change 12. Notes written in the pull request: 57 of 92 repos (V5); 69 of 146 counting change-note file tools (V6). Each pattern count is cited with the share of sampled files a reader confirmed |
| OF3 | Document types missing from the 2026-10-03 count | 2,903 distinct location and name pairs; 577 document-like stems unmatched; 141 file heads read. By file tree: 12 proposal folders (11 confirmed by reading) and 7 decision-record folders (7 confirmed), against 4 proposal folders and 1 decision-record folder on 2026-10-03. [Newly Observed Document Types](#newly-observed-document-types) lists every finding |
| OF4 | Agent instruction files | AGENTS.md 59, CLAUDE.md 35, copilot instructions 14, other file names in 1 or 2 repos each. 29 repos have both AGENTS.md and CLAUDE.md: CLAUDE.md points to AGENTS.md in 14 repos and is an identical copy in 12 repos. AGENTS.md is the shared name; the agents.md site, Claude Code docs and GitHub Copilot docs (all B) each say their tools read AGENTS.md. Declarations name no vendor |
| OF5 | GitHub-only skew | Every corpus repo is hosted on GitHub. See [GitHub-Only Hosting](#github-only-hosting) |
| OF6 | Skew to developer tools | 73% developer or operator software. The outside study gives lower shares for every file. See [Skew](#skew) |
| OF7 | Terms | 30 contexts per word, labelled by hand. maintainer: one sense (28 of 30 contexts). contributor: two senses (sends changes 18; credited 8). user: at least four senses (end user 15; person running the tool 6; account record 6; operating-system user 2). release: published version 16, the process 5, the GitHub release object 4. version: this project's 13, a dependency's 9. change: unit of work 17, behaviour users meet 4. [Header](#header) gives each word one meaning, with the Baseline lexicon (L51) as the source |

## Questions for Stage 2

Stage 1 decides none of the questions below.

| # | Question | Context and evidence | Effect of each answer |
| --- | --- | --- | --- |
| Q1 | Should maintainers-list fold into code-owners, or keep a narrower action of its own? | As drafted on 2026-10-03, a contributor uses maintainers-list (find the person who can decide on a stuck change) for the same approval decision as code-owners. The 19 repos hold 10 rosters, 3 pointers, 5 approval-rule files and 1 work-polling guide; 4 rosters map areas to people in step with CODEOWNERS | Fold: maintainers-list leaves the list. Narrow: a new action, such as finding who maintains the project and how to reach them, for contributors and downstream users; rerun the overlap test against code-owners and governance-document. The corpus side holds 6 rosters, so the row stays Medium. Either way, approval-rule OWNERS and owners.yaml files count toward code-owners (51 to 55 repos) |
| Q2 | Which action does package-readme serve: a folder note or a package front page? | Of 26 sub-folder READMEs read, 11 are folder notes (11 repos) and 8 are package or tool front pages | Folder note: the floor is met (11 repos, Google READMEs guide B), so High. Front page: run the overlap test against readme first. Detection excludes vendored folders and locale copies, and counts a sub-folder README linked from the root CONTRIBUTING toward contributing-guide |
| Q3 | Should subsystem explanations fold into architecture-overview as per-subsystem instances? | Ghost `docs/codebase/authentication.md` and PostHog `docs/internal/activity-logging.md` help the same contributor make the same decision as an architecture overview, at a narrower scope. The 2026-10-09 sample found 3 more subsystem documents (TanStack router code splitting, crawl4ai Docker server, cua spacesd) | Yes: architecture-overview goes High (15 whole-system and 5 subsystem repos confirmed, Baseline SA-01.01 B), and scope becomes a cardinality choice. No: architecture-overview still shares an action with the subsystem explanations and stays Medium. Either way, record security reviewers as a second actor (cloudnative-pg writes for contributors and auditors), and keep user-facing architecture pages and folder maps out of the count |
| Q4 | Should redistributor-facing THIRD_PARTY files fold into NOTICE, with LICENSING.md and adopter-facing THIRD_PARTY files as aliases of license-file? | The 8 THIRD_PARTY files split by action: 6 carry third-party notices and licence texts for redistribution, 1 tells users to confirm their own use, 1 is a JSON provenance record. LICENSING.md (alloy, cua) maps each licence to the parts of the code under that licence | Yes: NOTICE goes High (13 of 18 repos confirmed by reading, Apache License 2.0 section 4(d) B); N10 dissolves; the provenance record becomes bill-of-materials evidence. No: NOTICE stays Medium (8 confirmed repos) |
| Q5 | Does a BUILD file serve one actor or two actors? | Handy and apple/container BUILD files serve a developer building from a checkout. git-crypt INSTALL.md is headed as a build guide, and Handy BUILD.md has a Linux install-from-source section for a user or packager | One actor: BUILD.md and BUILDING.md become aliases of DEVELOPMENT.md (N2), giving 10 confirmed repos; Baseline DO-07.01 sets only the build part. Two actors: BUILD and install-from-source may form one type with DO-07.01 as literature |
| Q6 | Does the documentation-set action (complete a task with the project) cover installing, getting started and fixing errors? | INSTALL (9 repos), GETTING_STARTED (3 pages) and TROUBLESHOOTING (7 repos) each serve a user of the software. No A/B source sets their contents | Yes: the three candidates fold into documentation-set. No: each stays a candidate at its current grade. Read the GNU Coding Standards INSTALL pages once the server stops returning HTTP 429 |
| Q7 | Should DCO and CLA form one document type with DCO 1.1 as standard text? | Baseline LE-01 accepts either a DCO or a CLA. The Contributor Covenant is the same kind of standard text for code-of-conduct | Yes: one type, and the commit-message sign-off references the type. Read the Apache ICLA as a possible B source for CLA contents (cua's CLA adapts the ICLA) |
| Q8 | Should OWNERS_ALIASES fold into code-owners as a tool-specific form? | 2 repos in one project family; with OWNERS, the file answers who must approve a change | Yes: an alias or guidance under code-owners (D9), and the OWNERS alias moves from maintainers-list to code-owners at the same time. Emeritus groups become shared content with maintainers-list |
| Q9 | Do reviewers read decision records to decide on a merge, as with change-description? | The AWS ADR process says reviewers cite decision records before a merge. In the corpus, a later reader checks whether a decision that governs many changes still applies: the backstage onboarding reference, the coolify boundary rules, and an n8n README written for an engineer who challenges a choice later | Yes: drop the reviewer use from decision-record. No: keep both uses |
| Q10 | Which document type serves later readers of design history? | As drafted on 2026-10-03, design-proposal includes the later reader as an actor. 5 of 10 earlier proposal repos keep and update the proposal after the decision; gateway-api GEP-2645 records the rationale of an existing resource after the fact | Drop the later reader from design-proposal, or move the later reader to decision-record. An accepted proposal counts toward design-proposal only |
| Q11 | Does ai-use-policy share an action with contributing-guide? | 34 of 45 repos keep AI rules inside contributing-guide or change-description; 11 keep a policy file, all read; the Linux Foundation policy (B) sets contributor duties | Content only: ai-use-policy meets the floor (11 repos, B) and goes High. Shared action: AI rules become elements of contributing-guide |
| Q12 | Are AI rules inside CONTRIBUTING elements of contributing-guide or a type of their own? | Same evidence as Q11 | Decided with Q11 |
| Q13 | Does SUPPORT.md belong to support-policy, compatibility-policy or both? | Two B sources give SUPPORT.md two meanings: where to ask for help (GitHub Docs) and how long releases get support (Baseline DO-04.01, DO-05.01) | Assign each meaning to one type, then run the action test between support-policy, compatibility-policy and the supported versions in security-policy |
| D1 | Document types to declare | The 11 High rows; each Medium row in [Document Types](#document-types) and each Medium and Low row in [Newly Observed Document Types](#newly-observed-document-types), kept or dropped with a reason | Sets the stage 2 declarations |
| D2 | Changelog file and release notes: one document type or two document types? | FE3, reopened by Keep a Changelog 2.0.0 and Baseline BR-04.01; 62 changelog files; 7 repos with a file only | One type keeps the fold; two types add a changelog-file declaration |
| D4 | Decisions open since 2026-10-03 | The actor of agent-instructions; the upgrade guide as its own type or as release-note content (Keep a Changelog 2.0.0 allows either placement); change-kind, which waits for stage 3 | Each answer sets one declaration |
| D6 | `overview` and `terms` | `covers`, `for` and `excludes` from the corpus (73% developer or operator software); one meaning each for user, contributor, release, version and change (OF7) | Sets the header |
| D7 | Placeholder ordering frame | One value until stage 4 | Sets the header |
| D9 | Forge-specific forms | [GitHub-Only Hosting](#github-only-hosting) | Forge-specific names go into aliases or guidance, never into ids |

Rows D3, D5 and D8 were withdrawn before publication.

## Still Open

- The SECURITY.md journal paper's own tables
- The "11 fields" figure from the 2025 CISA draft
- The meaning of `draft: true` in the Baseline catalog file
- The release history of the REUSE specification
- The ICSME proceedings entry for the outside study, and the study figures checked against the paper
- GNU Coding Standards (HTTP 429)
- Reddit (every fetch refused)

## Stage 2: Header and Document Types

Stage 2 writes the header of the code-repository universe spec and declares its document types in `universes/code-repository/universe.kbp.yaml`. The maintainer reviews the stage 2 answers at the end of the preset work. Stage 3 writes the element questions and fills each composition. Stage 4 replaces the placeholder ordering frame and the `no_artifact` condition.

### Declaration Rule

- Every High document type is declared.
- A Medium document type is declared when the type is confirmed by reading in at least 10 repositories and shares no action with a declared type.
- Every other Medium row and every Low row stays a candidate. [Candidates Kept](#candidates-kept) lists, for each row, the evidence that would raise the grade.

Result: 20 declared document types, 14 High and 6 Medium.

### Declared Document Types

The checker derives each name from the id. Aliases carry the file names and forge-specific names; ids and enablements name no forge or vendor. Count cells read "confirmed by reading / by pattern", as in [Document Types](#document-types).

| Id | Name | Rows | Confirmed by reading / by pattern | Literature (grade) | Grade |
| --- | --- | --- | --- | --- | --- |
| `readme` | Readme | C1; package front pages from C29 | 10 / 146; 8 package front pages read | L2, L9, L77 (B) | **High** |
| `license-file` | License file | C2; LICENSING.md and the adopter-facing THIRD_PARTY file from N10 | 143 / 143; LICENSING.md 2 of 2 | L39, L40 (A); L51 LE-03.01 (B) | **High** |
| `release-notes` | Release notes | C3; the changelog file (FE3, D2) | 20 release-body repos plus 62 changelog heads / 133 | L27 (A); L28, L51 BR-04.01 (B) | **High** |
| `security-policy` | Security policy | C4 | 74 / 75 | L43, L51 VM-01.01 to VM-03.01 (B) | **High** |
| `contributing-guide` | Contributing guide | C5; AI use policy files from C22 | 26 / 105; AI policy files 11 of 11 | L14, L51 GV-03.01 and GV-03.02, L83 (B) | **High** |
| `commit-message` | Commit message | C6 | 10 / 146 | L26, L29, L30 (A); L82 (B) | **High** |
| `code-of-conduct` | Code of conduct | C7 | 60 / 60 | L19 (B) | **High** |
| `agent-instructions` | Agent instructions | C8 | 10 / 67 | L21, L22, L23, L65 (B) | **High** |
| `change-description` | Change description | C10 | 10 / 128 of 144 sampled | L31 (B) | **High** |
| `design-proposal` | Design proposal | C16 | 11 / 12 | L20, L34, L35 (B) | **High** |
| `release-procedure` | Release procedure | C26 | 17 / 17 | L20 (B) | **High** |
| `architecture-overview` | Architecture overview | C18; subsystem explanations from N19 | 20 (15 whole-system, 5 subsystem) / 37 | L51 SA-01.01 (B) | **High** |
| `notice-file` | Notice file | N1; redistributor-facing THIRD_PARTY files from N10 | 13 / 18 | L81 (B) | **High** |
| `folder-readme` | Folder readme | C29, folder-note action | 11 / 99 | L9 (B) | **High** |
| `issue-report` | Issue report | C9 | 105 (262 template files parsed) / 110 | Forge docs, syntax only; L51 DO-02.01 (B) | **Medium** |
| `code-owners` | Code owners | C11; N12; approval-rule OWNERS and owners.yaml files | 51 / 55 | Forge docs, syntax only (B) | **Medium** |
| `documentation-set` | Documentation set | C15; N4, N5 and N7 | 6 docs folders, plus 10 repos from N4, N5 and N7 / 87 docs folders | L13 (C); L51 DO-01.01, SA-02.01 (B) | **Medium** |
| `funding-file` | Funding file | C19 | 53 / 53 | L47, syntax only (B) | **Medium** |
| `roadmap` | Roadmap | C28 | 11 / 11 | None at A or B | **Medium** |
| `development-guide` | Development guide | N2; N3 | 10 / 13 | L51 DO-07.01, build steps only (B) | **Medium** |

Each enablement, written from the corpus reads and the graded literature:

| Id | Action | Actor | Timing | Alias |
| --- | --- | --- | --- | --- |
| `readme` | decide whether to try the project or one of its packages | a first-time visitor | on the first visit to the repository or package | README file at the repository root or at a package root |
| `license-file` | decide whether the licence allows the planned use of the code | anyone who plans to use, copy or change the code | before using the code | LICENSE or COPYING file, LICENSES folder, LICENSING.md |
| `release-notes` | decide whether to upgrade to a new release | a user | when the maintainers publish a release | release notes on a release page; CHANGELOG, NEWS or HISTORY file |
| `security-policy` | report a vulnerability privately to the maintainers | a person who finds a vulnerability in the software | before telling anyone else about the vulnerability | SECURITY.md |
| `contributing-guide` | prepare a change the maintainers will accept | a contributor | before opening an issue or sending a change | CONTRIBUTING file; AI use policy file |
| `commit-message` | decide whether to keep or undo a past change | a maintainer or contributor | when reading the project history | commit message |
| `code-of-conduct` | report unacceptable behaviour by someone taking part in the project | anyone who takes part in the project | when the unacceptable behaviour happens | CODE_OF_CONDUCT file; Contributor Covenant |
| `agent-instructions` | follow the project's rules for building, testing and changing the code | a coding agent | at the start of each task in the repository | AGENTS.md, CLAUDE.md or another coding tool's instruction file |
| `change-description` | decide whether to merge a change | a maintainer | before merging the change | pull request description, merge request description or CL description; pull request template |
| `design-proposal` | accept or reject a proposed design | the maintainers who decide on designs | before anyone builds the design | RFC, enhancement proposal or design document in a proposals folder |
| `release-procedure` | publish a release by following the project's steps | the maintainer who publishes the release | when preparing each release | RELEASE.md, RELEASING.md or a release process page |
| `architecture-overview` | learn how the main parts of the code work together | a contributor or security reviewer | before working on an unfamiliar part of the code | ARCHITECTURE.md, an architecture page in the docs, or a design note for one subsystem |
| `notice-file` | include the required attribution notices in a redistributed copy of the software | anyone who redistributes the software, on its own or inside another work | before distributing the copy | NOTICE file; THIRD_PARTY_NOTICES or THIRD_PARTY_LICENSES file |
| `folder-readme` | find the files to read or change in a folder | a contributor or maintainer | on first entering the folder | README file in a sub-folder |
| `issue-report` | decide whether to fix a reported bug or build a requested feature | a maintainer | when a new issue arrives | issue; issue form or issue template |
| `code-owners` | find who must approve a change to each file or folder | a contributor | before asking for review | CODEOWNERS, OWNERS, OWNERS_ALIASES or owners.yaml file |
| `documentation-set` | complete a task with the software, such as installing it or fixing an error | a user | while setting up or using the software | docs folder or documentation site, with INSTALL, getting-started and troubleshooting pages |
| `funding-file` | give money to the project's maintainers | a sponsor | when choosing whom to fund | FUNDING.yml file |
| `roadmap` | choose which planned work to wait for or help build | a user or contributor | when planning for the project's next releases | ROADMAP.md or a roadmap page |
| `development-guide` | build, run and test the code from a local copy of the repository | a contributor | before changing the code for the first time | DEVELOPMENT.md, HACKING.md, BUILD.md or BUILDING.md |

The issue-report action applies to bug reports and feature requests. By file name, 98 of the 105 repos with issue templates keep a bug template and 77 keep a feature-request template. Of 6 seeded feature-request templates read on 2026-10-09 (seed 20261009), 5 propose a new feature and 1 tracks a release.

### Header

| Field | Value | Basis |
| --- | --- | --- |
| `id`, `label` | `code-repository`, Code repository | Stage 1 name |
| `version` | 0.1 | First version of the universe spec |
| `conforms_to` | kbp/0.8 | The protocol version the bundled checker accepts |
| `overview.covers` | The written documents of a codebase: files in its repository, commit messages, change descriptions, issue reports and release notes | The declared types: repository files, plus commit messages, change descriptions, issue reports and release notes kept outside the file tree |
| `overview.for` | Anyone who uses, changes, maintains, redistributes or funds a software project, and the coding agents that work on the project's code | The actors of the declared types; agent files in 67 repos. Developer or operator software makes up 73% of the corpus ([Skew](#skew)) |
| `overview.excludes` | The source code itself, files generated by build tools, and files that contributors usually keep out of the repository, such as personal working notes and drafts | Build outputs stay candidates (C21, C30); working notes are excluded (N18, N23). Generated release notes stay in scope as release-notes (F1) |
| `ordering_frame` | `step`, six values | D7: a placeholder `order` at stage 2; [Stage 4](#ordering-frame) replaced the placeholder |
| `no_artifact` | `when: { repository-state: [archived] }` | A placeholder `when: {}` at stage 2; [Stage 4](#wiring) replaced the placeholder |
| `statuses` | Empty | A later stage |
| `relation_kinds`, `elements`, `relations` | Declared at stage 3 | [Stage 3](#stage-3-elements-compositions-and-relations) |

Terms, one meaning each. Corpus counts come from 30 hand-labelled contexts per word (OF7). The OpenSSF Baseline lexicon (L51), read on 2026-10-09, defines all six words.

| Term | Meaning | Corpus (OF7) | Literature (grade) |
| --- | --- | --- | --- |
| user | A person who uses the project's software. | End user 15 and person running the tool 6, of 30 contexts | Baseline lexicon, User (B). Baseline also counts contributors as users; the universe spec and its enablements keep users and contributors apart |
| contributor | Anyone who sends a change to the project. | Sends changes 18 of 30 | Baseline lexicon, Contributor (B) |
| maintainer | A person who can approve changes to the project's files. | One sense, 28 of 30 | Baseline lexicon, Maintainer (B) |
| change | One set of edits to the project's code, build files or documentation that a contributor sends for review. | Unit of work 17 of 30 | Baseline lexicon, Change (B) |
| release | A bundle of the software that the maintainers publish for users, such as a package or a program file. | Published version 16 of 30 | Baseline lexicon, Release, noun (B) |
| version | The identifier of one release, such as 2.1.0. | This project's version 13 of 30 | Baseline lexicon, Version Identifier (B); L27 (A) |

### Answers to the Stage 2 Questions

| # | Answer | Basis | Effect |
| --- | --- | --- | --- |
| Q1 | Narrow the maintainers-list action to finding who maintains the project and how to reach a maintainer, for contributors and downstream users | CNCF MAINTAINERS.md (L20) and Baseline GV-01.01 and GV-01.02 (L51) set roster contents for finding and reaching a maintainer. Finding who must approve a change is a separate action. 6 of the 10 rosters list roles without paths | maintainers-list stays a Medium candidate with 6 rosters. Approval-rule OWNERS and owners.yaml files count toward code-owners. code-owners no longer shares an action with maintainers-list |
| Q2 | The folder-note action | 11 folder notes in 11 repos; the Google READMEs guide (L9, B) sets the contents | `folder-readme` is High. A would-be user reads the 8 package front pages to decide whether to try a package. The readme enablement covers the same decision at package scope, so the front pages count as readme instances |
| Q3 | Yes: subsystem explanations fold into architecture-overview as per-subsystem instances | The Ghost and PostHog subsystem documents serve the same contributor making the same decision at a narrower scope | architecture-overview is High on 20 confirmed repos. The Baseline SA-01 objective names contributors and security reviewers as readers, so the architecture-overview actor is a contributor or security reviewer |
| Q4 | Yes | V19: 6 THIRD_PARTY files carry notices for redistribution, 1 file addresses adopters, 1 file is a provenance record | `notice-file` is High (13 of 18 repos confirmed, L81). LICENSING.md and the adopter-facing file become license-file aliases. The provenance record counts as bill-of-materials evidence. N10 leaves the candidate list. The minio NOTICE file stays recorded as a notice that also addresses adopters |
| Q5 | One actor | The 4 BUILD files serve a developer who builds from a local copy to change the code. Baseline DO-07.01 recommends publishing build steps with the contributor documentation. Install-from-source sections belong to the install task in Q6 | BUILD.md and BUILDING.md become aliases of the development guide (N2). `development-guide` reaches 10 confirmed repos and is declared at Medium: DO-07.01 sets only the build-step contents |
| Q6 | Yes: INSTALL, GETTING_STARTED and TROUBLESHOOTING fold into documentation-set | 5 of the 9 install documents sit in `docs/`, all 7 troubleshooting repos keep the page or folder in `docs/`, and 6 getting-started folders sit in `docs/` and hold install, configuration, upgrade and troubleshooting pages. A user reads install, getting-started and troubleshooting documents while setting up or using the software. The Baseline DO-01.01 recommendation names installing, configuring and using as user-guide topics. No A/B source sets the contents of a standalone INSTALL, GETTING_STARTED or TROUBLESHOOTING document | documentation-set gains 10 confirmed repos from the three rows and is declared at Medium: only a C source (L13) sets the documentation-set contents |
| Q7 | Yes: DCO and CLA form one candidate, with DCO 1.1 as standard text | Baseline LE-01.01 accepts either form for the same contributor decision | The candidate stays Medium with 6 repos. The commit-message sign-off stays a commit-message element until the candidate is declared |
| Q8 | Yes | With OWNERS, the OWNERS_ALIASES file answers who must approve a change | OWNERS_ALIASES and OWNERS become code-owners aliases. Emeritus groups become shared content with maintainers-list at stage 3 |
| Q9 | Drop the reviewer use | Deciding whether to merge a change is the change-description action. The corpus reads show only later readers checking whether a standing decision still applies (backstage, coolify, n8n); the AWS source (L33) was not reread | decision-record keeps one action and stays a Medium candidate with 7 repos |
| Q10 | Move the later reader to decision-record | design-proposal serves the maintainers who accept or reject a design before anyone builds the design | An accepted proposal counts toward design-proposal only |
| Q11 | Shared action | AI rules state which AI-assisted changes the maintainers accept. A contributor reads the AI rules while preparing a change, at the same time as the contributing guide. 34 of the 45 repos keep the rules in CONTRIBUTING or the change-description template. Rule files for commit conventions (N22) are likewise contributing-guide content | ai-use-policy folds into contributing-guide. AI policy files become a contributing-guide alias, and EL17 moves to contributing-guide at stage 3 |
| Q12 | Elements of contributing-guide | Decided with Q11 | Stage 3 writes the AI rules as contributing-guide elements |
| Q13 | support-policy covers where to ask for help. compatibility-policy covers how long each release gets fixes | GitHub Docs (L18) gives the help meaning. Baseline DO-04.01 and DO-05.01 give the support-duration meaning and also accept a support section in SECURITY.md | Deciding where to ask for help and planning upgrades before support ends are two actions, so the two candidates share content only. Support duration becomes one question shared by compatibility-policy and the supported-versions section of security-policy. Both candidates stay Medium with 4 repos each |
| D1 | 20 declared types; see [Declaration Rule](#declaration-rule) | High rows, plus Medium rows that are confirmed in 10 or more repos and share no action with a declared type | Sets the declarations |
| D2 | One document type: the changelog file stays folded into release-notes | Keep a Changelog 2.0.0 (L28) separates a cumulative record from a per-release announcement, and tells projects to write the release notes from the changelog. Both forms serve a user deciding about a new release. Corpus: 55 repos keep both, 71 keep release notes only, 7 keep a changelog file only | Changelog file names go into the release-notes alias. The release-notes form (changelog file, release page or both) becomes a stage 4 lead |
| D4 | agent-instructions actor: a coding agent. Upgrade guide: its own candidate. change-kind: stage 3 | The agent sources (L21, L22, L23) address the agent, and 49 repos give the agent prohibitions. Changing a working setup to fit a new version is a different action from deciding whether to upgrade; the upgrade-order, rollback and upgrade-check elements (EL10) appear only in upgrade guides | upgrade-guide stays a Medium candidate with 6 repos. At stage 3, upgrade-guide and release-notes share one question about upgrade steps |
| D6 | See [Header](#header) | Corpus kinds and OF7 counts; Baseline lexicon | Sets the header |
| D7 | Frame `order` with the one value `unordered` | Stage 4 declares the ordering frame | Sets the header |
| D9 | Forge-specific names appear only in aliases | [GitHub-Only Hosting](#github-only-hosting) | `change-description` keeps a forge-neutral id; "pull request description" sits in the alias |

### Candidates Kept

| # | Candidate | Grade | Evidence that would raise the grade |
| --- | --- | --- | --- |
| C12 | upgrade-guide | Medium | 4 more upgrade guides confirmed by reading |
| C13 | maintainers-list (narrowed action) | Medium | 4 more rosters confirmed by reading under the narrowed action |
| C14 | governance-document | Medium | 4 more governance documents confirmed by reading |
| C17 | decision-record | Medium | 3 more repos with decision records confirmed by reading; the AWS ADR process (L33) reread |
| C20 | citation-file | Medium | 4 more CITATION files confirmed by reading, from a corpus with more research software |
| C21 | bill-of-materials | Medium | SBOM files or workflows read in 10 repos, and evidence that people write SBOM content by hand |
| C23 | support-policy (where to ask for help) | Medium | 6 more SUPPORT files confirmed by reading |
| C24 | threat-model | Medium | 7 more published threat models confirmed by reading |
| C25 | compatibility-policy (stability and support duration) | Medium | 6 more stability, deprecation or support-duration pages confirmed by reading |
| C27 | review-guide | Medium | 6 more review guides confirmed by reading |
| C30 | build-provenance | Medium | Hand-written provenance documents, read in 10 repos |
| N6 | FAQ | Medium | An A/B source that sets the contents and 8 more FAQ files read; the Q6 test against documentation-set, since the 2 FAQ files already read sit in `docs/` |
| N8 | ADOPTERS.md | Medium | 8 more adopter lists confirmed by reading |
| N9 | DCO and CLA, one candidate | Medium | 4 more repos confirmed by reading; the Apache ICLA read as a source for CLA contents |
| N11 | SECURITY_CONTACTS | Low | An A/B source that sets the contents, and 3 or more repos outside one project family |
| N13 | TESTING.md | Low | An A/B source that sets the contents, and 4 or more repos confirmed by reading |
| N14 | TRADEMARK.md | Low | An A/B source that sets the contents, and 4 or more repos confirmed by reading |
| N15 | TRANSLATIONS.md | Low | An A/B source that sets the contents. Translated READMEs count as readme instances |
| N16 | PRIVACY.md | Low | Evidence that the file covers only the codebase, an A/B source that sets the contents, and 1 more repo confirmed by reading |
| N17 | llms.txt | Low | An A/B source, read, that sets the contents, and 4 or more repos confirmed by reading |
| N20 | release posts in `docs/` | Low | Evidence that release posts share no action with release-notes |
| N21 | runbook, postmortem and glossary paths | Low | Reads of the 2, 4 and 6 matched repos |

Folded at stage 2: C22 into contributing-guide; package front pages from C29 into readme; N3 into development-guide; N4, N5 and N7 into documentation-set; N10 into license-file and notice-file; N12 into code-owners; the N19 subsystem explanations into architecture-overview. The crawl4ai function table from N19 stays a lead for folder-readme. The changelog file stays folded into release-notes (FE3). N18 and N23 stay excluded; N22 and N24 stay outside the types.

Tally: 54 rows. 20 declared types cover 20 rows; 8 rows fold into declared types; 22 rows stay candidates (14 Medium, 8 Low); 4 rows stay excluded or outside the types.

## Stage 3: Elements, Compositions and Relations

Stage 3 declares the elements of the code-repository universe spec, fills the composition of each declared document type and declares the relations, all in `universes/code-repository/universe.kbp.yaml`. Each element question is written in this preset's words from the stage 1 element evidence ([Element Grades That Moved](#element-grades-that-moved) and the corpus counts) and the stage 3 reads below. The 2026-10-03 drafts gave the starting wording. The maintainer reviews the stage 3 answers at the end of the preset work.

### Rules Applied

- Element grades follow [Grades](#grades). High: an A/B source sets the element, and the corpus shows the element in 2 or more repositories. Medium: one of the two conditions holds. Low: neither condition holds.
- The universe spec declares every High and Medium element. Low elements stay leads in [Refusals](#refusals).
- An element without a stage 1 row keeps its 2026-10-03 grade. Its counts come from the stage 1 rerun and the stage 3 reads.
- An element is core when the actor of a document type needs the element to take the type's action. Every other element is situational.
- Every element carried the placeholder ordering value `unordered` at stage 3. [Stage 4](#ordering-frame) gives each element a step.
- One type owns each element, and every other type that composes the element links to the owner. The owner is chosen in this order:
  1. The type named by the strongest source for the element.
  2. The type where the element is core. When agent-instructions and a type written for people both need the element, the type written for people owns the element: agent files restate the project's rules for an agent, and the rabbitmq and archify agent files point to CONTRIBUTING.
  3. The type that holds the element in the most repositories.

### Stage 3 Reads

Stage 3 read only files already stored in the raw data folder:

- The 10 seeded precision picks (`picks-2026-10-08.json`) for each pattern counted at stage 1 and left unread
- The 10 stored READMEs drawn with seed 20261009 from the sorted README files, read for headings
- The 10 pull request bodies of the C10 confirmation sample (seed 20261009), read in full
- The 36 proposals read at stage 1, counted again for goal and design headings with the stage 1 heading rules
- The 12 roadmap files, read for work the maintainers ask contributors to help build
- The 9 stored heads of DEVELOPMENT, HACKING, BUILD and BUILDING files

| Pattern | Read right |
| --- | --- |
| CONTRIBUTING code style | 8 of 10 |
| CONTRIBUTING help channel | 8 of 10 |
| Agent file test command | 8 of 10; 1 more file points to CONTRIBUTING for the tests |
| Agent file code style | 9 of 10 |
| Agent file commit convention | The 10 files come from 7 repos, and the files of 3 repos state a commit format; the pattern also matches branch and pull request rules |
| Agent file prohibitions | No single element: code style 2, generated files 3, actions left to a person 3, other 2 |
| Issue template observed behaviour | 8 of 10 |
| Issue template reproduction steps | 9 of 10 |
| Issue template environment | 9 of 10 |
| Issue template feature fields | Problem or use case 8 of 10; requested behaviour 9 of 10 |
| Pull request template related issue | 10 of 10 |
| Pull request template change type | 9 of 10 |

### Declared Elements

Count cells give the evidence behind each grade. "Seeded snippets" and "seeded templates" are the precision picks; "seeded heading lists" are the 10 READMEs drawn at stage 3; "seeded pull request bodies" are the C10 confirmation sample. Each row names the owner type and each linking type, with the element's strength in each type.

| # | Element | Question | Owner | Linked from | Corpus | Literature (grade) | Grade | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S3-1 | `project-purpose` | What does the project do? | `readme` (core) | None | 91 by heading pattern; 7 of 10 seeded heading lists | L2, L10 (B) | **High** | Holds the 2026-10-03 grade |
| S3-2 | `install-steps` | Which steps install the software? | `readme` (situational) | `documentation-set` (core on install pages) | 109 by heading pattern; 7 of 10 seeded heading lists; INSTALL documents in 9 repos (N4) | L2, L10; L51 DO-01.01 recommendation (B) | **High** | Holds the 2026-10-03 grade |
| S3-3 | `first-result` | How does a new user get a first working result? | `readme` (situational) | `documentation-set` (core on get-started pages) | 66 by heading pattern; 5 of 10 seeded heading lists; 3 getting-started pages read (N5) | None that sets the element apart from install steps | **Medium** | Holds the 2026-10-03 grade |
| S3-4 | `excluded-uses` | Which uses of the software do the maintainers exclude? | `readme` (situational) | None | 3 by heading (non-goals, out of scope, limitations, who it is for); 0 of 10 seeded heading lists | None | **Medium** | Corpus side only |
| S3-5 | `project-status` | Which status does the project or package have, such as active or no longer maintained? | `readme` (situational) | None | 36 by heading pattern; 0 of 10 seeded heading lists; status lines in 2 package front pages read (hedge_fund, cuabot; EL23) | L9 (B) for package status; CM3 (C) | **High** | Moved from Medium: the EL23 status evidence comes from package front pages, which count as readme instances since stage 2 |
| S3-6 | `help-channel` | Where does a user or contributor get help? | `readme` (situational) | `contributing-guide` (situational) | 70 by heading pattern; 2 of 10 seeded heading lists; CONTRIBUTING help channels 56 by pattern, 8 of 10 seeded files read right | L2 (B) | **High** | Holds the 2026-10-03 grade |
| S3-7 | `docs-location` | Where is the full documentation? | `readme` (situational) | None | 46 by heading pattern; 4 of 10 seeded heading lists | None | **Medium** | Corpus side only |
| S3-8 | `license-id` | Which main licence applies to the code? | `license-file` (core) | `readme` (situational) | 143 license files read by head; README licence sections 73 by heading pattern, 5 of 10 seeded heading lists | L39, L40 (A); L51 LE-03.01 (B) | **High** | Holds the 2026-10-03 grade |
| S3-9 | `copyright-holder` | Who holds the copyright in the code? | `license-file` (situational) | `notice-file` (situational) | 91 of 143 license file heads carry a dated copyright line (EL1) | L40 (A) | **High** | EL1 |
| S3-10 | `part-licences` | Which licence applies to each part of the code outside the main licence? | `license-file` (situational) | None | Both LICENSING.md files read (alloy, cua) map each licence to parts of the code; a `LICENSES/` folder in 1 repo by listing | L40 (A) | **High** | Moved from Medium: the LICENSING.md files joined license-file at stage 2 (Q4) |
| S3-11 | `attribution-notices` | Which attribution notices must every redistributed copy include? | `notice-file` (core) | None | 13 of 18 repos confirmed by reading (N1 with the redistributor-facing THIRD_PARTY files) | L81 (B) | **High** | Both sides |
| S3-12 | `bundled-licences` | Which licence applies to each component from another project that the software includes? | `notice-file` (situational) | None | 6 redistributor-facing THIRD_PARTY files read (V19), each listing components with their licence texts | None | **Medium** | Corpus side only |
| S3-13 | `release-version` | Which version do the release notes describe? | `release-notes` (core) | None | 126 repos with a release body over 200 characters; 62 changelog heads read | L27 (A); L28 (B) | **High** | Holds the 2026-10-03 grade |
| S3-14 | `release-date` | On which date did the maintainers publish the release? | `release-notes` (situational) | None | 29 of 62 changelog heads carry a dated heading; release pages carry a date field | L28 (B) | **High** | Holds the 2026-10-03 grade |
| S3-15 | `breaking-change` | Which existing uses of the software stop working? | `release-notes` (core) | `commit-message` (situational); `change-description` (situational) | Release bodies in 32 repos, 5 of 7 read right; 3 footers in 6,435 commits; 12 pull request templates ask (EL4) | L26, L27 (A); L28 (B) | **High** | EL4 |
| S3-16 | `deprecations` | Which features will a later release remove? | `release-notes` (situational) | None | Release bodies in 49 repos by pattern, 5 of 7 read right | L27 (A); L28 (B) | **High** | Holds the 2026-10-03 grade |
| S3-17 | `upgrade-steps` | Which steps must a user take to upgrade? | `release-notes` (situational) | None | Release bodies in 24 repos by pattern, 5 of 7 read right (EL2) | L28 (B) | **High** | EL2 |
| S3-18 | `security-fixes` | Which vulnerabilities does the release fix? | `release-notes` (situational) | None | Release bodies in 34 repos by pattern, 6 of 7 read right | L28 (B) | **High** | Holds the 2026-10-03 grade |
| S3-19 | `report-channel` | How does someone report a vulnerability privately? | `security-policy` (core) | None | 66 of 75 SECURITY files name a channel, all 77 files read | L43, L51 VM-01.01 to VM-03.01 (B) | **High** | Holds the 2026-10-03 grade |
| S3-20 | `report-contents` | Which facts must a vulnerability report include? | `security-policy` (situational) | None | 31 by pattern, 7 of 7 seeded snippets read right | None | **Medium** | Corpus side only |
| S3-21 | `supported-versions` | Which versions get security fixes? | `security-policy` (situational) | None | 42 by pattern, 7 of 7 seeded snippets read right | L43 (B) | **High** | Holds the 2026-10-03 grade |
| S3-22 | `first-reply-days` | How many days does a reporter wait for a first reply? | `security-policy` (situational) | None | 18 by pattern, 7 of 7 seeded snippets read right | L49 (B) | **High** | Holds the 2026-10-03 grade |
| S3-23 | `disclosure-timing` | When do the maintainers publish details of a fixed vulnerability? | `security-policy` (situational) | None | 34 by pattern, 5 of 7 seeded snippets read right | L49 (B) | **High** | Holds the 2026-10-03 grade |
| S3-24 | `vulnerability-scope` | Which findings count as vulnerabilities? | `security-policy` (situational) | None | 14 by pattern, 8 of 8 seeded snippets read right | None | **Medium** | Corpus side only |
| S3-25 | `contribution-route` | Where does a contributor propose a change first? | `contributing-guide` (core) | None | CONTRIBUTING files in 44 repos say to open an issue or discussion first, 8 of 10 seeded snippets read right; 80 by the broad pattern | L14, L51 GV-03.01 (B) | **High** | Holds the 2026-10-03 grade |
| S3-26 | `change-refusal` | Which changes will the maintainers refuse? | `contributing-guide` (situational) | None | 29 by pattern, 10 of 10 seeded snippets read right (EL5) | None | **Medium** | EL5: L51 GV-03.02 sets requirements a change must meet, and names no refusal rules |
| S3-27 | `required-evidence` | Which evidence must a change include? | `contributing-guide` (situational) | None | 57 by pattern, 8 of 10 seeded snippets read right (EL5) | L51 GV-03.02 (B) | **High** | Moved from Medium: the GV-03.02 recommendation names testing requirements for acceptable contributions |
| S3-28 | `code-style` | Which style rules must the code follow? | `contributing-guide` (situational) | `agent-instructions` (situational) | CONTRIBUTING 55 by pattern, 8 of 10 seeded files read right; agent files 57 by pattern, 9 of 10 read right | L51 GV-03.02 (B) | **High** | Holds the 2026-10-03 grade |
| S3-29 | `commit-format` | Which format must commit messages follow? | `contributing-guide` (situational) | `agent-instructions` (situational) | CONTRIBUTING 33 by pattern, 10 of 10 seeded snippets read right; agent files: the files of 3 of the 7 repos behind the 10 seeded files state a commit format | L26 (A) | **High** | Holds the 2026-10-03 grade |
| S3-30 | `ai-use-rules` | Which uses of AI tools do the maintainers accept in a change? | `contributing-guide` (situational) | None | 9 of 11 AI policy files state a permitted use; AI rules in 31 CONTRIBUTING files, 10 of 10 seeded snippets read right | None that sets the permitted uses | **Medium** | Corpus side only |
| S3-31 | `ai-duties` | Which duties does a contributor have for AI-assisted work? | `contributing-guide` (situational) | None | 10 of 11 AI policy files (EL17) | L83 (B) | **High** | EL17 |
| S3-32 | `change-summary` | What does the change do? | `commit-message` (core) | `change-description` (core) | Every commit carries a subject; 10 of 10 seeded pull request bodies state the change | L29, L30 (A); L31 (B) | **High** | Holds the 2026-10-03 grade |
| S3-33 | `change-reason` | Which problem does the change solve? | `commit-message` (core) | `change-description` (core) | 59% of 4,357 commits carry a body; 7 of 10 seeded pull request bodies give a reason | L29, L30 (A); L31 (B) | **High** | Holds the 2026-10-03 grade |
| S3-34 | `change-kind` | Which kind is the change, such as a bug fix or a new feature? | `commit-message` (situational) | `change-description` (situational); `release-notes` (situational) | 65 repos write mostly Conventional Commits; change-type fields in 34 pull request templates, 9 of 10 seeded templates read right | L26 (A); L28 six change types (B) | **High** | D4 in [Stage 1 Flags Answered](#stage-1-flags-answered) |
| S3-35 | `related-changes` | Which earlier issues or changes does the change refer to? | `commit-message` (situational) | `change-description` (situational) | 59 repos write Closes or Fixes lines in commits; related-issue fields in 50 pull request templates, 10 of 10 seeded templates read right; 4 of 10 seeded pull request bodies link an issue | L30 (A); L31 (B) | **High** | Holds the 2026-10-03 grade |
| S3-36 | `sign-off` | Who certifies having the right to submit the change under the project's licence? | `commit-message` (situational) | None | 52 repos, 535 commits (EL21) | L29, L30 (A); L82, L51 LE-01.01 (B) | **High** | EL21 |
| S3-37 | `unacceptable-behaviour` | Which behaviour is unacceptable? | `code-of-conduct` (core) | None | Contributor Covenant text in 42 of the 60 files read by header | L19 (B) | **High** | EL6 |
| S3-38 | `conduct-report` | Where does someone report unacceptable behaviour? | `code-of-conduct` (core) | None | Contributor Covenant text in 42 of the 60 files read by header | L19 (B) | **High** | EL6 |
| S3-39 | `conduct-consequences` | Which consequences follow unacceptable behaviour? | `code-of-conduct` (situational) | None | Contributor Covenant text in 42 of the 60 files read by header | L19 (B) | **High** | EL6: Covenant 3.0 moves the consequences into a repair ladder |
| S3-40 | `conduct-scope` | Which spaces does the code of conduct apply to, such as forums, events or chats? | `code-of-conduct` (situational) | None | Contributor Covenant text in 42 of the 60 files read by header | L19 (B) | **High** | EL6 |
| S3-41 | `conduct-enforcers` | Who enforces the code of conduct? | `code-of-conduct` (situational) | None | Contributor Covenant text in 42 of the 60 files read by header | L19, version 2.1 (B) | **High** | EL6: rests on Covenant 2.1, the latest version in the corpus |
| S3-42 | `generated-files` | Which files does a tool generate? | `agent-instructions` (situational) | None | Agent files 22 by pattern, 5 of 8 seeded snippets read right | None | **Medium** | Corpus side only |
| S3-43 | `commit-checks` | Which checks must pass before a commit? | `agent-instructions` (situational) | None | Agent files 44 by pattern, 5 of 7 seeded snippets read right | L21 (B) | **High** | Holds the 2026-10-03 grade |
| S3-44 | `approval-needed` | Which actions need approval from a person first? | `agent-instructions` (situational) | None | 9 repos, 4 of 8 seeded snippets read right (EL7) | None | **Medium** | EL7 |
| S3-45 | `verification` | How did the contributor check the change? | `change-description` (situational) | None | 55 pull request templates, 7 of 7 headings read right; 8 of 10 seeded pull request bodies | None | **Medium** | Corpus side only |
| S3-46 | `unchanged-behaviour` | Which behaviour stays the same after the change? | `change-description` (situational) | None | 3 of 10 seeded pull request bodies (harbor, kube-hetzner, textream) | None | **Medium** | Corpus side only |
| S3-47 | `release-note-line` | Which entry in the release notes describes each change? | `change-description` (situational) | `release-notes` (core) | 57 of 92 repos write most release lines as the pull request title (V5); release-note fields in 19 pull request templates, 7 of 7 read right | L32 (B) | **High** | EL3 |
| S3-48 | `ai-use-record` | Which AI tools did the contributor use for the change? | `change-description` (situational) | None | AI fields in 24 pull request templates, 7 of 7 seeded templates read right; 1 of 10 seeded pull request bodies | L83 (B) | **High** | New at stage 3: L83 asks contributors to give notice of AI use |
| S3-49 | `proposal-motivation` | Which problem does the proposal address? | `design-proposal` (core) | None | Problem or motivation heading in 27 of 36 proposals (12 repos) | L34, L35 (B) | **High** | Holds the 2026-10-03 grade |
| S3-50 | `proposed-design` | Which design does the proposal recommend? | `design-proposal` (core) | None | Design, proposal or solution heading in 27 of 36 proposals (11 repos) | L34, L35 (B) | **High** | Holds the 2026-10-03 grade |
| S3-51 | `design-goals` | Which results must the design achieve? | `design-proposal` (situational) | None | Goals heading in 18 of 36 proposals (8 repos) | L20 DESIGN-PROPOSALS.md (B) | **High** | EL13 |
| S3-52 | `design-non-goals` | Which results do the authors leave out of the design on purpose? | `design-proposal` (situational) | None | Non-goals heading in 17 of 36 proposals (8 repos) | L20 DESIGN-PROPOSALS.md (B) | **High** | EL13 |
| S3-53 | `design-alternatives` | Which other designs did the authors consider? | `design-proposal` (situational) | None | Alternatives heading in 17 of 36 proposals (10 repos) | L35 (B) | **High** | Holds the 2026-10-03 grade |
| S3-54 | `undecided-parts` | Which parts of the design are still undecided? | `design-proposal` (situational) | None | Open questions in 5 of 36 proposals (3 repos) | L35 (B); L20 key questions (B) | **High** | EL13 |
| S3-55 | `proposal-status` | Which status does the proposal have? | `design-proposal` (situational) | None | Status field in 23 of 36 proposals (9 repos) | L34 (B); L20 optional status (B) | **High** | EL13 |
| S3-56 | `release-steps` | Which steps does a maintainer follow to publish a release? | `release-procedure` (core) | None | 17 of 17 procedures (EL18) | L20 RELEASES.md (B) | **High** | EL18 |
| S3-57 | `release-owner` | Who publishes the next release? | `release-procedure` (situational) | None | 5 of 17 procedures (EL18) | L20 RELEASES.md (B) | **High** | EL18 |
| S3-58 | `release-schedule` | When is the next release due? | `release-procedure` (situational) | None | 9 of 17 procedures (EL18) | L20 RELEASES.md (B) | **High** | EL18 |
| S3-59 | `components` | What does each main part of the code do? | `architecture-overview` (core) | `agent-instructions` (situational) | Components named in 18 of 18 confirmed documents; an architecture section in the agent files of 15 of 66 repos (EL15) | L51 SA-01.01 (B) | **High** | EL15 |
| S3-60 | `part-interactions` | How do the main parts of the code interact? | `architecture-overview` (situational) | None | A flow, pipeline, lifecycle or request-path heading in 12 of 18 confirmed documents (EL15) | L51 SA-01 objective: interactions and components (B) | **High** | Moved from Medium: the SA-01 objective names the interactions between components |
| S3-61 | `folder-purpose` | What does each folder hold? | `folder-readme` (core) | `architecture-overview` (situational); `agent-instructions` (situational) | 11 folder notes in 26 sub-folder READMEs read (EL20); architecture documents link into the code or map folders in 11 of 18 confirmed documents; agent files 54 by layout pattern, 6 of 7 read right | L9 (B) | **High** | EL20 |
| S3-62 | `observed-behaviour` | Which behaviour did the reporter observe? | `issue-report` (core for bug reports) | None | 76 by pattern, 8 of 10 seeded templates read right | None that sets the contents | **Medium** | Corpus side only |
| S3-63 | `expected-behaviour` | Which behaviour did the reporter expect? | `issue-report` (situational) | None | 69 by pattern, 6 of 6 seeded snippets read right | None that sets the contents | **Medium** | Corpus side only |
| S3-64 | `repro-steps` | Which steps reproduce the bug? | `issue-report` (core for bug reports) | None | 88 by pattern, 9 of 10 seeded templates read right | None that sets the contents | **Medium** | Corpus side only |
| S3-65 | `reporter-environment` | Which setup does the reporter use, such as the software version and the platform? | `issue-report` (core for bug reports) | None | 93 by pattern, 9 of 10 seeded templates read right | None that sets the contents | **Medium** | Corpus side only |
| S3-66 | `duplicate-search` | Which existing issues did the reporter check? | `issue-report` (situational) | None | 29 by pattern, 6 of 6 seeded snippets read right (EL8) | None | **Medium** | EL8 |
| S3-67 | `feature-need` | Which problem would the requested feature solve? | `issue-report` (situational) | None | Problem or use-case field in 8 of 10 seeded feature-request templates | None | **Medium** | New at stage 3: corpus side only |
| S3-68 | `requested-behaviour` | What should the requested feature do? | `issue-report` (core for feature requests) | None | Requested-behaviour or proposed-solution field in 9 of 10 seeded feature-request templates | None | **Medium** | New at stage 3: corpus side only |
| S3-69 | `path-approvers` | Which people or teams must approve a change to each file or folder? | `code-owners` (core) | None | 51 files parsed; a catch-all line in 27 of 51 (EL9) | Forge docs, syntax only (B) | **Medium** | Corpus side only |
| S3-70 | `settings-reference` | Which settings does the software accept? | `documentation-set` (core on configure pages) | None | 45 repos keep a configuration, settings, options or reference path (file-tree names, unread) | L51 DO-01.01, SA-02.01 (B) | **High** | Holds the 2026-10-03 grade; the corpus count comes from unread file-tree names, as in EL12 |
| S3-71 | `error-fixes` | How does a user fix a known error? | `documentation-set` (core on fix-an-error pages) | None | 3 substantive TROUBLESHOOTING files read; 7 repos by name (N7) | None | **Medium** | Corpus side only |
| S3-72 | `docs-version` | Which release of the software does each documentation page describe? | `documentation-set` (situational) | None | 6 repos keep versioned docs (file-tree names, unread; EL12) | None | **Medium** | EL12 |
| S3-73 | `funding-links` | Where can a sponsor give money to the maintainers? | `funding-file` (core) | None | 53 files parsed | L47, syntax only (B) | **Medium** | Corpus side only |
| S3-74 | `sponsored-accounts` | Which people or organisations does a sponsor pay? | `funding-file` (situational) | None | `github:` accounts in 47 files (EL16) | L47, syntax only (B) | **Medium** | EL16 |
| S3-75 | `planned-work` | Which work do the maintainers plan next? | `roadmap` (core) | None | 12 files read in 11 repos | None | **Medium** | Corpus side only |
| S3-76 | `help-wanted` | Which planned work do the maintainers ask contributors to help with? | `roadmap` (situational) | None | 4 of 12 files (ai-hedge-fund, beads, odysseus, qdrant) | None | **Medium** | New at stage 3: corpus side only |
| S3-77 | `declined-ideas` | Which ideas have the maintainers declined? | `roadmap` (situational) | None | 2 of 12 files (EL19) | None | **Medium** | EL19 |
| S3-78 | `roadmap-date` | When did the maintainers last update the plan for upcoming work? | `roadmap` (situational) | None | 5 of 12 files (EL19) | None | **Medium** | EL19 |
| S3-79 | `dev-setup` | How does a contributor set up a local copy for development? | `development-guide` (core) | `contributing-guide` (situational) | CONTRIBUTING 62 by pattern, 16 of 18 seeded snippets read right; setup or prerequisites in 5 of 9 stored development and build file heads | L51 DO-07.01 (B): the build instructions name the required libraries, frameworks, SDKs and dependencies | **High** | Holds the 2026-10-03 grade |
| S3-80 | `build-command` | Which commands build the software? | `development-guide` (core) | `agent-instructions` (core) | Agent files 56 by pattern, 7 of 7 headings read right; build steps in 4 of 9 stored development and build file heads | L51 DO-07.01 (B); L21 (B) | **High** | Holds the 2026-10-03 grade |
| S3-81 | `test-command` | Which commands run the tests? | `development-guide` (core) | `agent-instructions` (core); `contributing-guide` (situational) | CONTRIBUTING 44 by pattern, 8 of 8 read right; agent files 53 by pattern, 8 of 10 seeded files hold a command and 1 points to CONTRIBUTING; tests in 2 of 9 stored development and build file heads | L21 (B) | **High** | Holds the 2026-10-03 grade |
| S3-82 | `maintainers` | Who maintains the project or package? | `readme` (situational) | None | 0 of 10 seeded heading lists; 0 of 26 sub-folder READMEs read (EL23) | L2 (B): who maintains and contributes; L9 (B): contacts in a package README | **Medium** | Literature side only. readme owns the element while maintainers-list stays a candidate. Precedent: commit-message keeps `sign-off` while the DCO and CLA candidate stays a candidate (Q7) |
| S3-83 | `known-shortcomings` | Which known shortcomings does the change have? | `change-description` (situational) | None | Not measured | L31 (B): shortcomings of the approach | **Medium** | Literature side only |

Tally: 83 elements, 53 High and 30 Medium; 22 links from other types.

### Compositions

"(linked)" marks an element owned by another type.

| Type | Core | Situational |
| --- | --- | --- |
| `readme` | `project-purpose` | `install-steps`, `first-result`, `excluded-uses`, `project-status`, `help-channel`, `docs-location`, `maintainers`, `license-id` (linked) |
| `license-file` | `license-id` | `copyright-holder`, `part-licences` |
| `release-notes` | `release-version`, `breaking-change`, `release-note-line` (linked) | `release-date`, `deprecations`, `upgrade-steps`, `security-fixes`, `change-kind` (linked) |
| `security-policy` | `report-channel` | `report-contents`, `supported-versions`, `first-reply-days`, `disclosure-timing`, `vulnerability-scope` |
| `contributing-guide` | `contribution-route` | `change-refusal`, `required-evidence`, `code-style`, `commit-format`, `ai-use-rules`, `ai-duties`, `help-channel` (linked), `dev-setup` (linked), `test-command` (linked) |
| `commit-message` | `change-summary`, `change-reason` | `change-kind`, `related-changes`, `sign-off`, `breaking-change` (linked) |
| `code-of-conduct` | `unacceptable-behaviour`, `conduct-report` | `conduct-consequences`, `conduct-scope`, `conduct-enforcers` |
| `agent-instructions` | `build-command` (linked), `test-command` (linked) | `generated-files`, `commit-checks`, `approval-needed`, `code-style` (linked), `commit-format` (linked), `components` (linked), `folder-purpose` (linked) |
| `change-description` | `change-summary` (linked), `change-reason` (linked) | `verification`, `unchanged-behaviour`, `release-note-line`, `ai-use-record`, `known-shortcomings`, `breaking-change` (linked), `change-kind` (linked), `related-changes` (linked) |
| `design-proposal` | `proposal-motivation`, `proposed-design` | `design-goals`, `design-non-goals`, `design-alternatives`, `undecided-parts`, `proposal-status` |
| `release-procedure` | `release-steps` | `release-owner`, `release-schedule` |
| `architecture-overview` | `components` | `part-interactions`, `folder-purpose` (linked) |
| `notice-file` | `attribution-notices` | `bundled-licences`, `copyright-holder` (linked) |
| `folder-readme` | `folder-purpose` | None |
| `issue-report` | `observed-behaviour`, `repro-steps` and `reporter-environment` for bug reports; `requested-behaviour` for feature requests | `expected-behaviour`, `duplicate-search`, `feature-need` |
| `code-owners` | `path-approvers` | None |
| `documentation-set` | `settings-reference` on configure pages; `error-fixes` on fix-an-error pages; `install-steps` (linked) on install pages; `first-result` (linked) on get-started pages | `docs-version` |
| `funding-file` | `funding-links` | `sponsored-accounts` |
| `roadmap` | `planned-work` | `help-wanted`, `declined-ideas`, `roadmap-date` |
| `development-guide` | `dev-setup`, `build-command`, `test-command` | None |

At stage 3, issue-report and documentation-set had no core element. Each element of the two types applies to some cases only: a bug report and a feature request need different elements, and each documentation task needs its own elements. [Stage 4](#wiring) makes those elements core for their issue kind or documentation task; the table shows the core entries with their conditions.

### Relations

The universe spec declares two relation kinds with shared meanings in the protocol: `feeds` (ordered) and `distinct-from` (unordered). Document types joined by a `distinct-from` edge share content and no action; the Basis column cites the stage 1 or stage 2 overlap test.

| From | To | Kind | Basis |
| --- | --- | --- | --- |
| `change-description` | `release-notes` | `feeds` | 57 of 92 repos write most release lines as the pull request title (V5); 46 repos publish generated notes in most releases (F1); L32 (B) |
| `change-description` | `commit-message` | `feeds` | 19 of 80 squash-merging repos copy the pull request body into the commit (V21) |
| `commit-message` | `release-notes` | `feeds` | L26 (A) maps commit types to changelog entries; L63 (B) builds changelog entries from a commit trailer |
| `issue-report` | `change-description` | `feeds` | Related-issue fields in 50 pull request templates, 10 of 10 seeded templates read right; 4 of 10 seeded pull request bodies link an issue |
| `license-file` | `notice-file` | `distinct-from` | Content only (N1, Q4) |
| `contributing-guide` | `development-guide` | `distinct-from` | Content only (N2) |
| `commit-message` | `change-description` | `distinct-from` | Content only (C10) |
| `agent-instructions` | `architecture-overview` | `distinct-from` | Content only (C8) |
| `change-description` | `design-proposal` | `distinct-from` | Content only (C16) |
| `architecture-overview` | `folder-readme` | `distinct-from` | Content only (C18, C29); scope differs |
| `architecture-overview` | `documentation-set` | `distinct-from` | Content only (C18) |
| `readme` | `documentation-set` | `distinct-from` | Content only (N4, Q6) |
| `change-summary` | `release-note-line` | `distinct-from` | Different readers: a reviewer or maintainer, and a user; the two texts match in 57 of 92 repos (V5) |
| `required-evidence` | `verification` | `distinct-from` | The rule in contributing-guide and the record in each change description |
| `folder-purpose` | `components` | `distinct-from` | EL15 and EL20 record components and folder purpose as separate shared questions |
| `install-steps` | `dev-setup` | `distinct-from` | A user installs the software; a contributor sets up a local copy (Q5) |

12 edges join document types and 4 edges join elements.

### Gate Leads

The protocol keys every element gate, every conditional strength and every edge gate on a frame, and at stage 3 the universe spec held only the placeholder ordering frame. [Stage 4](#leads-answered) answers each gate lead below. Under the frame-or-factor rule, a dimension that gates or composes elements becomes a frame.

| # | Dimension | Elements | Evidence | Stage 4 effect |
| --- | --- | --- | --- | --- |
| G1 | Issue kind: bug report or feature request | Bug report: `observed-behaviour`, `expected-behaviour`, `repro-steps`, `reporter-environment`, `duplicate-search`. Feature request: `feature-need`, `requested-behaviour` | Bug templates in 98 repos and feature-request templates in 77 repos, by file name | A frame that makes each set core for its issue kind |
| G2 | Documentation task: install, configure or fix an error | `install-steps`, `first-result`, `settings-reference`, `error-fixes` | L51 DO-01.01 recommendation names installing, configuring and using | A frame that makes each element core for its task |
| G3 | Sign-off requirement | `sign-off` | 52 repos, 535 commits; the DCO and CLA candidate (N9) | A gate on `sign-off` |
| G4 | Commit convention (F2) | `change-kind` | 65 repos write mostly Conventional Commits | `change-kind` stays situational. F2 stays a factor unless stage 4 gates `change-kind` on the convention |
| G5 | Repository kind (F7) | `install-steps`, `first-result` | 5 collections or themes and 4 research model releases ([Skew](#skew)) | A gate on the two readme elements |

### Stage 1 Flags Answered

| # | Flag | Answer |
| --- | --- | --- |
| EL1 | Copyright holder, a shared question with NOTICE | license-file owns `copyright-holder`; notice-file links the element |
| EL2 | Upgrade steps in release-notes and upgrade-guide | release-notes owns `upgrade-steps`. upgrade-guide stays a candidate (D4) |
| EL3 | Release-note line shared by release-notes and change-description | change-description owns `release-note-line`: L32 builds release notes from pull request titles. release-notes links the element as core |
| EL4 | Breaking changes nearly unused in commits | release-notes owns `breaking-change`; commit-message links the element as situational |
| EL5 | Baseline GV-03.02 may set required evidence or change refusal | The GV-03.02 recommendation names testing requirements, so `required-evidence` goes High. `change-refusal` stays Medium |
| EL6 | Contributor Covenant 3.0 | The five code-of-conduct elements keep High on Covenant 2.1, the latest version in the corpus. `conduct-enforcers` rests on Covenant 2.1 |
| EL7 | Check with a person first | `approval-needed`, Medium |
| EL9 | Default owner | The catch-all line is one instance of `path-approvers`, a question about each file or folder |
| EL10, EL11, EL14, EL22 | Elements of upgrade-guide, governance-document, decision-record and bill-of-materials | The elements stay with the candidates. A later stage rechecks EL22 against the 17 CISA fields once the universe spec declares bill-of-materials |
| EL15 | Data flows as SA-01.01 actions | The SA-01 objective names the interactions between components, so `part-interactions` goes High |
| EL17 | Contributor duties for AI-assisted work | contributing-guide owns `ai-duties` (Q11, Q12) |
| EL20 | Folder purpose shared with architecture-overview | folder-readme owns `folder-purpose`; architecture-overview and agent-instructions link the element |
| EL21 | Sign-off and the DCO and CLA candidate | `sign-off` stays a commit-message element while N9 stays a candidate |
| EL23 | Package status and package owner | The 2 status reads are package front pages, now readme instances, so the status evidence moves to `project-status` and the owner evidence moves to `maintainers` (RF5) |
| D4 | change-kind | An element of commit-message, linked from change-description and release-notes. Change kind stays an element. Under the frame-or-factor rule, a dimension becomes a frame only when the universe spec orders, gates or composes by the dimension, and no order, gate or composition in the universe spec depends on change kind |

### Refusals

| # | Candidate | Evidence | Result | Reason |
| --- | --- | --- | --- | --- |
| RF1 | code-owners: approval required before a merge | No measure in the file | Refused | Maintainers set the requirement in branch protection, outside the file (L17) |
| RF2 | code-owners: default owner (EL9) | 27 of 51 files | Folded | An instance of `path-approvers` |
| RF3 | agent-instructions: repository layout | 54 by pattern, 6 of 7 read right | Folded | The layout answers `folder-purpose` for each folder |
| RF4 | folder-readme: folder status (EL23) | 0 of 11 folder notes | Moved | The 2 status reads are package front pages; the evidence supports `project-status` |
| RF5 | folder-readme: folder owner (EL23) | 0 of 26 reads | Moved | L9 sets contacts for a package README. Package front pages are readme instances, so readme owns `maintainers` (S3-82) |
| RF6 | readme: who maintains the project | 0 of 10 seeded heading lists; L2 (B) | Declared | Declared as `maintainers` (S3-82) |
| RF7 | funding-file: sponsor tiers (EL16) | 0 files | Low lead | The sponsor platform holds the tiers |
| RF8 | documentation-set: known issues | 1 repo by file tree | Low lead | Neither side: no A/B source, and fewer than 2 repos |
| RF9 | security-policy: fixed vulnerabilities | 2026-10-03 shared listing | Not linked | A user deciding on an upgrade reads the list of fixed vulnerabilities, so release-notes keeps `security-fixes` |
| RF10 | agent-instructions: prohibitions | 49 by pattern; 10 seeded files read | Refused | The prohibitions split across code style, generated files and actions left to a person |
| RF11 | AI disclosure (2026-10-03) | 31 CONTRIBUTING files; 24 pull request templates | Split | The rule joins `ai-duties`; the record of tools used becomes `ai-use-record` |
| RF12 | architecture-overview: generated files | 1 of 18 documents (kyverno) | Not linked | One repo |
| RF13 | design-proposal: breaking changes | No count in proposals | Not linked | No corpus evidence |
| RF14 | change-description: approach (L31) | Not measured | Folded | A description of the approach answers `change-summary`; the shortcomings of the approach became `known-shortcomings` (S3-83) |
| RF15 | Issue logs, pull request screenshots, security bounties | 55, 27 and 8 by pattern, unread | Low leads | No A/B source, and no sample read of the matched files |
| RF16 | readme: contributing section | 7 of 10 seeded heading lists | Not an element | A pointer to contributing-guide |
| RF17 | 2026-10-03 questions inherited from another preset (design-proposal, decision-record, architecture-overview) | Not applicable | Rewritten | Every question in this universe spec is written in this preset's words |

## Stage 4: Frames, Factors and the Ordering Frame

Stage 4 declares the frames and factors of the code-repository universe spec, replaces the placeholder ordering frame and the `no_artifact` condition, and wires frames into compositions and gates, all in `universes/code-repository/universe.kbp.yaml`. The maintainer reviews the stage 4 answers at the end of the preset work.

### Stage 4 Rules

- Frame-or-factor rule: a dimension becomes a frame when the universe spec orders, gates or composes elements by the dimension. Every other dimension becomes a factor. A factor changes presentation and focus only.
- Frame and factor grades follow [Grades](#grades). The universe spec declares every High and Medium frame or factor whose values cover the observed cases. Low rows stay leads.
- Every value needs at least one observed case. [Cases by Repository Kind](#cases-by-repository-kind) counts the cases in each of the five repository kinds from [Skew](#skew).
- An issue element is core for an issue kind when maintainers mark the matching form field required in more than half of the issue forms of that kind. Each documentation element is core on the pages for the matching task, such as `install-steps` on install pages.
- Stage 4 counts come from the raw data folder. Stage 4 reads cover stored files and four published guides.

### Stage 4 Reads

| Read | Result |
| --- | --- |
| 10 issue forms drawn with seed 20261009: 5 bug forms, 5 feature forms | Every field maps to the right element in 7 of 10 forms. The 3 misses leave a field unmapped (a description field in backstage and devlake, a pitch field in pocket-id), so the required-field counts are lower bounds |
| 33 issue templates outside the bug, feature, question and documentation names, read by name and title | 13 templates report defects, such as performance problems, build failures, flaky tests and scanner findings, in 9 repos; 8 track maintainer work, such as releases and planning, in 8 repos; 6 are generic templates; 6 hold other requests: a showcase, a conformance test report, marketplace feedback, a refactor proposal, a typo report and an untitled form |
| DCO, sign-off and CLA lines in the CONTRIBUTING files, pull request templates and agent files of the 32 matched repos, all read | 11 repos require a sign-off line on each commit; 17 repos require a signed licence agreement; 4 matches are other text: a maintainer sign-off rule, Apache licence headers in 2 repos, and a statement that the project has no CLA |
| The first 5 commit subjects of the 6 area-prefix repos, and of 4 seeded repos in each of the conventional and free-form classes | 14 of 14 repos read right |
| The latest release body of 17 repos drawn with seed 20261009 across the four pattern classes | Written by hand in 4 repos; generated in 5 repos; generated, then edited by hand in 1 repo; collected from change notes in 2 repos; unclear in 2 repos; empty in 2 repos; a pointer to the changelog file in 1 repo. 7 of the 17 repos sit in the wrong pattern class, so stage 4 cites only the read cases for this dimension |
| The READMEs of the 5 collections or themes and the 4 research model releases, read for headings | Install steps in 3 of 5 collections or themes and in 4 of 4 model releases |
| The READMEs of the 4 archived repos | An end-of-life notice at the top of 3 of the 4 READMEs |
| GitHub Docs on archiving (L84) and the archive section of GitLab Docs on projects (L59), read on 2026-10-09 | Archiving makes a repository read-only for issues, changes and releases |
| Git SubmittingPatches (L29) and the kernel patch guide (L30), reread on 2026-10-09 | Both guides tell authors to open the subject line with the code area: "area: " in Git, "subsystem: summary phrase" in the kernel |

### Ordering Frame

The placeholder frame `order` becomes `step` and keeps the code `fh4x9`. Stage 4 groups the 20 declared document types into six steps by the timing in each enablement ([Declared Document Types](#declared-document-types)). Each element takes the same step as its document type.

| Value | Question | Document types and their timing | Elements |
| --- | --- | --- | --- |
| `choose` | Is the reader deciding whether to use, fund or rely on the project? | `readme` (on the first visit); `license-file` (before using the code); `funding-file` (when choosing whom to fund); `roadmap` (when planning for the next releases) | 17 |
| `use` | Is the reader installing or running the software, or notifying the maintainers of a vulnerability? | `documentation-set` (while setting up or using the software); `security-policy` (before telling anyone else about a vulnerability found in the software) | 9 |
| `propose` | Is the reader taking part in discussions or proposing a change? | `contributing-guide` (before opening an issue or sending a change); `code-of-conduct` (when unacceptable behaviour happens in project spaces); `issue-report` (when a new issue arrives); `design-proposal` (before anyone builds the design) | 26 |
| `build` | Is the reader writing or testing code in a local copy? | `development-guide` (before changing the code for the first time); `architecture-overview` (before working on an unfamiliar part); `folder-readme` (on first entering a folder); `agent-instructions` (at the start of each task) | 9 |
| `review` | Is the reader deciding whether to accept or keep a change, or whom to ask for approval? | `code-owners` (before asking for review); `change-description` (before merging); `commit-message` (when reading the project history) | 11 |
| `release` | Is the reader publishing a release, deciding whether to move to a newer release, or distributing a copy of the software? | `release-procedure` (when preparing each release); `release-notes` (when the maintainers publish a release); `notice-file` (before distributing a copy) | 11 |

Basis for the order of the steps:

- A first-time visitor reads the README before using the code, and a contributor reads the CONTRIBUTING file before opening an issue or sending a change (stage 2 timings). L77 (B) lists the README readers as users, developers and contributors.
- Issues feed change descriptions: related-issue fields in 50 pull request templates, 10 of 10 seeded templates read right.
- Design proposals come before the build (L34, L35, B). The development guide comes before the first change (stage 2 timings). The code-owners file comes before review (L17, B).
- Change descriptions feed commit messages (19 of 80 squash-merging repos copy the pull request body into the commit, V21), and both feed the release notes (V5; L26, A; L32, B).

### Declared Frames

| # | Frame | Role; set by | Values | Corpus | Literature (grade) | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| S4-1 | `step` | Ordering; universe | `choose`, `use`, `propose`, `build`, `review`, `release` | The stage 2 enablement timings of the 20 declared types; the `feeds` edges in [Relations](#relations) | L17, L34, L35, L77 (B); L26 (A) | Derived from the stage 2 declarations; no grade of its own |
| S4-2 | `issue-kind` | Selection; instance | `bug-report`, `feature-request`, `docs-report`, `question`, `maintainer-task` | 258 issue templates in 105 repos, by file name and title: bug 98 repos, feature 78 (77 by file name alone), question 13, documentation 10, maintainer work 8, other defect kinds 9 repos. 10 forms read for stage 4; in the stage 3 reads, 8 of 10 and 9 of 10 seeded templates read right | L51 DO-02.01 (B) requires a defect-reporting guide; L16 (B) sets form syntax only | **Medium**: corpus side only, since no A/B source sets the kinds |
| S4-3 | `docs-task` | Selection; instance | `install`, `get-started`, `configure`, `use`, `look-up`, `fix-an-error`, `upgrade` | Documentation file-tree names in 68 repos: use 42, fix an error 41, look up 41, install 40, get started 35, upgrade 33, configure 32 (unread names). Confirmed by reading: 6 docs folders, and 10 repos from N4, N5 and N7 | L51 DO-01.01 recommendation (B) names installing, configuring and using; L13 (C) | **High**: both sides, 16 repos confirmed by reading |
| S4-4 | `contributor-assertion` | Gating; scope | `sign-off`, `agreement`, `none` | 11 repos require a sign-off line and 17 require a signed agreement, all read; 118 repos state neither rule in the files read. A sign-off line appears in most commits of 8 of the 11 sign-off repos, 3 of the 17 agreement repos and 5 of the other 118 repos | L82 DCO 1.1 (B); L51 LE-01.01 (B) accepts either a sign-off or an agreement | **High**: both sides, 28 repos confirmed by reading |
| S4-5 | `repository-state` | Applicability; scope | `active`, `archived` | 4 archived repos, 142 active, from the repository records; end-of-life notices in 3 of the 4 archived READMEs | L84 (B); L59 (B) | **Medium**: one-side rule, 3 to 5 repos with a B source that sets the read-only state |

### Declared Factors

| # | Factor | Set by | Values | Corpus | Literature (grade) | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| S4-6 | `notes-writing` | Scope | `by-hand`, `generated`, `generated-then-edited`, `from-change-notes` | 12 read release bodies with a value: by hand in 4 repos, generated in 5, generated then edited in 1, collected from change notes in 2 repos. Stage 1: generated notes in most releases of 46 repos; change-note file tools in 13 repos | L28 (B): tools draft and people edit; L32 (B): notes built from merged pull requests | **High**: both sides, 12 repos confirmed by reading |
| S4-7 | `notes-place` | Scope | `release-page`, `changelog-file`, `both` | V3: release pages only in 71 repos, changelog file only in 7, both in 55, neither in 13 repos. Confirmed by reading: 62 changelog heads and 20 release-body repos | L28 (B) keeps the changelog file and the release notes apart; L51 BR-04.01 (B) | **High**: both sides; stage 2 answer D2 named the lead |
| S4-8 | `commit-convention` | Scope | `conventional`, `area-prefix`, `free-form` | Most subjects follow Conventional Commits in 65 repos, open with a code area in 6 repos, and follow neither form in 75 repos; 14 of 14 repos read right | L26 (A) sets the change-type opening; L29, L30 (A) set the code-area opening | **High**: both sides, 14 repos confirmed by reading |
| S4-9 | `version-pattern` | Scope | `major-minor-patch`, `calendar`, `other` | Release tags of the latest 10 releases, by tag pattern: three numbers in 121 repos, a year first in 4, another pattern in 7, no release in 14 repos. Tags read for all 11 calendar and other repos: mermaid and TanStack/router put a package name before three-number versions. After the reads, 123 repos use three numbers and 5 repos use another pattern | L27 (A) sets the three-number pattern | **High**: both sides, 11 repos confirmed by reading |

Every gate, core condition and `no_artifact` condition in the universe spec names frames only, as the protocol requires. Each factor changes how a consumer presents or focuses the answers: a release-notes writer under `generated-then-edited` edits a tool's draft, and a writer under `major-minor-patch` ties each breaking change to a new major version (L27).

### Wiring

| Frame | Universe spec entry | Effect | Basis |
| --- | --- | --- | --- |
| `issue-kind` | `issue-report` core: `observed-behaviour`, `repro-steps`, `reporter-environment` when `bug-report` | A maintainer needs the three answers to decide on a reported bug | Of 70 bug forms, 61 require the observed behaviour, 57 the version or platform, 47 the reproduction steps. Expected behaviour (30 of 70) and duplicate search (2 of 70) stay situational |
| `issue-kind` | `issue-report` core: `requested-behaviour` when `feature-request` | A maintainer needs the requested behaviour to decide on building a feature | Of 58 feature forms, 33 require the requested behaviour. The need behind the feature (29 of 58, exactly half) stays situational |
| `docs-task` | `documentation-set` core: `install-steps` (linked) on `install` pages, `first-result` (linked) on `get-started` pages, `settings-reference` on `configure` pages, `error-fixes` on `fix-an-error` pages | A page written for one task needs the element for that task | L51 DO-01.01 (B); the N4, N5 and N7 reads. The `use`, `look-up` and `upgrade` pages have no core element in the universe spec. `docs-version` stays situational |
| `contributor-assertion` | Gate on `sign-off`: `{ contributor-assertion: [sign-off] }` | The universe spec asks for a sign-off line only in projects that require a sign-off line | L82, L51 LE-01.01 (B); sign-off in most commits of 8 of 11 sign-off repos, against 8 of the other 135 repos |
| `repository-state` | `no_artifact: { when: { repository-state: [archived] } }` | The universe spec suppresses every document type in an archived repository | L84 and L59 (B): an archived repository accepts no issues, changes or releases. L84 tells maintainers to update the README before archiving, and 3 of the 4 archived READMEs carry an end-of-life notice |

A core element with a false condition stays situational. Only the gate on `sign-off` excludes an element. Without an `issue-kind`, `docs-task` or `repository-state` value, the matching entries stay unresolved, as the protocol's evaluation rules require.

### Cases by Repository Kind

Repository kinds: D developer tool, library or framework (74); O operations software (33); E end-user application (30); C collection or theme (5); R research model release (4). One agent assigned the kinds, and no second reader checked the labels.

| Dimension | Value | D | O | E | C | R | All |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `issue-kind` | `bug-report` (template) | 48 | 26 | 21 | 1 | 2 | 98 |
| `issue-kind` | `feature-request` (template) | 34 | 25 | 16 | 1 | 2 | 78 |
| `issue-kind` | `question` (template) | 5 | 6 | 2 | 0 | 0 | 13 |
| `issue-kind` | `docs-report` (template) | 4 | 5 | 1 | 0 | 0 | 10 |
| `issue-kind` | No issue template | 21 | 6 | 9 | 3 | 2 | 41 |
| `docs-task` | `install` | 23 | 11 | 6 | 0 | 0 | 40 |
| `docs-task` | `get-started` | 16 | 13 | 6 | 0 | 0 | 35 |
| `docs-task` | `configure` | 15 | 12 | 5 | 0 | 0 | 32 |
| `docs-task` | `use` | 27 | 11 | 4 | 0 | 0 | 42 |
| `docs-task` | `look-up` | 18 | 14 | 9 | 0 | 0 | 41 |
| `docs-task` | `fix-an-error` | 19 | 16 | 6 | 0 | 0 | 41 |
| `docs-task` | `upgrade` | 17 | 13 | 3 | 0 | 0 | 33 |
| `docs-task` | No documentation page | 39 | 12 | 18 | 5 | 4 | 78 |
| `contributor-assertion` | `sign-off` | 1 | 10 | 0 | 0 | 0 | 11 |
| `contributor-assertion` | `agreement` | 8 | 6 | 3 | 0 | 0 | 17 |
| `contributor-assertion` | `none` (no rule stated) | 65 | 17 | 27 | 5 | 4 | 118 |
| `repository-state` | `active` | 73 | 31 | 29 | 5 | 4 | 142 |
| `repository-state` | `archived` | 1 | 2 | 1 | 0 | 0 | 4 |
| `notes-place` | `release-page` | 33 | 14 | 21 | 2 | 1 | 71 |
| `notes-place` | `changelog-file` | 4 | 2 | 1 | 0 | 0 | 7 |
| `notes-place` | `both` | 32 | 15 | 7 | 1 | 0 | 55 |
| `notes-place` | No release notes | 5 | 2 | 1 | 2 | 3 | 13 |
| `commit-convention` | `conventional` | 34 | 14 | 16 | 1 | 0 | 65 |
| `commit-convention` | `area-prefix` | 4 | 2 | 0 | 0 | 0 | 6 |
| `commit-convention` | `free-form` | 36 | 17 | 14 | 4 | 4 | 75 |
| `version-pattern` | `major-minor-patch` | 61 | 30 | 27 | 3 | 2 | 123 |
| `version-pattern` | `calendar` | 3 | 0 | 1 | 0 | 0 | 4 |
| `version-pattern` | `other` | 3 | 1 | 1 | 0 | 0 | 5 |
| `version-pattern` | No release | 7 | 2 | 1 | 2 | 2 | 14 |

Issue-kind and docs-task rows count repositories with at least one template or page of the value, so one repository can count under several values. In the `version-pattern` rows, mermaid and TanStack/router count under `major-minor-patch`, as read. `maintainer-task` has no row; the 33 templates read show maintainer work in 8 repos. `notes-writing` has no row: 7 of the 17 read repos sit in the wrong pattern class, and the 12 read cases come from 9 D repos, 1 O repo, 1 E repo and 1 C repo.

Gaps:

- Every `docs-task` and `contributor-assertion` case comes from D, O and E repos.
- No archived repo is a collection, theme or model release.
- The showcase template (archify) and the conformance test report (gateway-api) fit no `issue-kind` value. The 6 generic templates accept any kind.

### Leads Answered

| # | Lead | Answer | Basis |
| --- | --- | --- | --- |
| F1 | changelog-production | Factor `notes-writing` (S4-6) | Each value has a read case. The universe spec uses the dimension for presentation only. The lead for a core `release-note-line` under `from-change-notes` stays open (Leads Kept) |
| F2 | commit-convention | Factor `commit-convention` (S4-8) | G4: `change-kind` stays situational under every convention |
| F3 | assurance-level | Lead | No corpus repository states a Baseline level, so no case falls under any value. Scorecard badges (9) and Best Practices badges (12) measure other scales |
| F4 | intake-stance | Folded into `contribution-route` | The values (issue first, closed to outside changes, open) are answers to "Where does a contributor propose a change first?". A factor would repeat the `contribution-route` element |
| F5 | primary-reader | Folded into `agent-instructions` | The coding agent already has its own type, `agent-instructions` (L21, B) |
| F6 | versioning-scheme | Factor `version-pattern` (S4-9) | Tags read; L27 (A) |
| F7 | repository-kind | Lead, Low | The kind labels come from one agent with no second reader. G5 refused: install steps appear in 3 of 5 collections or themes and in 4 of 4 model releases |
| G1 | Issue kind | Frame `issue-kind` (S4-2) | [Wiring](#wiring) |
| G2 | Documentation task | Frame `docs-task` (S4-3) | [Wiring](#wiring) |
| G3 | Sign-off requirement | Frame `contributor-assertion` (S4-4) | [Wiring](#wiring) |
| G4 | Commit convention | Factor (S4-8) | `change-kind` stays situational |
| G5 | Repository kind | Refused | Install steps appear in all five repository kinds; the collections without install steps are lists of links |
| D2 | Release-notes form | Factor `notes-place` (S4-7) | V3; L28 (B) |
| D7 | Placeholder ordering frame | Replaced by `step` (S4-1) | [Ordering Frame](#ordering-frame) |

### Leads Kept

| # | Lead | Evidence | Evidence that would declare the lead |
| --- | --- | --- | --- |
| LK1 | Baseline maturity levels as a frame | L51 (B) applies each requirement at level 1, 2 or 3; level 2 needs at least 2 maintainers and a small number of consistent users, level 3 a large number of consistent users. Level-gated items include build steps (DO-07.01), roles (GV-01.02) and a disclosure policy with a response time (VM-01.01) | Maintainer and user counts per repository, so each case falls under one level |
| LK2 | Release condition as a frame | L51 (B) applies DO-01 to DO-06, SA-01 and SA-02 only after the project has made a release | Read evidence of a published release per repository; package registries sit outside the stored data |
| LK3 | `release-note-line` core in `change-description` under `from-change-notes` | Change-note tools in 13 repos; 22 repos tell contributors to write a change note (FE4) | Reads showing that projects block a merge without a change note |
| LK4 | `upgrade-steps` linked from `documentation-set` on `upgrade` pages | Upgrade pages by name in 33 repos; upgrade-guide stays a candidate (D4) | A stage 2 decision on upgrade-guide |

## Stage 5: Type Guidance

Stage 5 writes the type guidance for the code-repository universe spec in `universes/code-repository/type-guidance.kbp.yaml`. Each guidance entry pairs one claim with one source. The claim helps a writer answer an element or write a document type. The maintainer reviews the stage 5 answers at the end of the preset work.

### Stage 5 Rules

- The guidance file registers 100 sources: one per row of [Graded Sources](#graded-sources), 15 for the 20 cited community rows, and the survey in this document.
- Each entry cites one registered source.
- Advice and placement entries cite an A or B source. Practice and distinction entries cite a source of any grade or the survey. Dispute entries cite a source of any grade.
- An entry carries a `when` condition only when the source limits the claim to one frame or factor value, such as Semantic Versioning advice for three-number versions.
- Each `distinct-from` edge in [Relations](#relations) gets one distinction entry that states how the two declarations differ.
- Placement entries name forges and tools. Declarations stay forge-neutral ([GitHub-Only Hosting](#github-only-hosting)).
- Claims give survey shares in words, such as "about a third". The counts stay in this document.
- This preset defines the five guidance kinds.

### Guidance Kinds

| Kind | Meaning | Sources | Entries |
| --- | --- | --- | --- |
| `advice` | A rule or recommendation for the writer | A or B | 141 |
| `placement` | A forge or tool feature that reads, shows or supports the document | A or B | 42 |
| `practice` | A habit of the surveyed projects, of practitioners or of a studied sample | Any grade, or the survey | 78 |
| `dispute` | A point where sources or practitioners disagree | Any grade | 20 |
| `distinction` | The difference between two declared document types or elements | Any grade, or the survey | 12 |

Tally: 293 entries. The 20 document types carry 126 entries, the 83 elements carry 151 entries and the 4 factors carry 16 entries. Every document type, element and factor carries at least one entry.

### Keyed Entries

| Frame or factor | Values | Entries on | Sources |
| --- | --- | --- | --- |
| `contributor-assertion` | `sign-off` | `contributing-guide`; `sign-off` (3 entries) | L82, L29; L51 LE-01.01 |
| `contributor-assertion` | `agreement` | `contributing-guide` | L51 LE-01.01 |
| `docs-task` | `look-up` | `documentation-set` (2 entries) | L51 SA-02.01 |
| `docs-task` | `upgrade` | `documentation-set` | L28 |
| `docs-task` | `get-started`; `use` | `documentation-set` (practice) | L13 |
| `issue-kind` | `bug-report` | `observed-behaviour`, `expected-behaviour`, `repro-steps`, `reporter-environment` (practice) | Required fields in the bug forms ([Wiring](#wiring)) |
| `issue-kind` | `feature-request` | `feature-need`, `requested-behaviour` (practice) | Required fields in the feature forms ([Wiring](#wiring)) |
| `version-pattern` | `major-minor-patch` | `release-version`, `deprecations`; the factor (2 entries) | L27 |
| `commit-convention` | `conventional` | `breaking-change`, `commit-format`, `change-kind`; the factor (2 entries) | L26; L28 |
| `commit-convention` | `area-prefix` | `commit-format`, `change-summary` | L29, L30 |
| `notes-writing` | `generated`, `generated-then-edited` | `release-note-line`; the factor (2 entries) | L32; L28 |
| `notes-writing` | `from-change-notes` | `release-note-line` (placement); the factor | L63; L28 |
| `notes-place` | `changelog-file`, `both`; `both`; `release-page` | The factor (3 entries) | L28 |

Two frames have no keyed entries:

- `step`: no source ties advice to one step.
- `repository-state`: L84 tells maintainers to update the README before archiving, while the repository is still active. Once the repository is archived, `no_artifact` suppresses every document type. The README advice is an unconditional entry on `project-status`.

### Coverage Gaps

- 22 elements carry no advice entry, since no A or B source covers the element contents: `excluded-uses`, `bundled-licences`, `report-contents`, `vulnerability-scope`, `change-refusal`, `generated-files`, `approval-needed`, `verification`, `unchanged-behaviour`, `observed-behaviour`, `expected-behaviour`, `repro-steps`, `reporter-environment`, `duplicate-search`, `feature-need`, `requested-behaviour`, `error-fixes`, `docs-version`, `planned-work`, `help-wanted`, `declined-ideas` and `roadmap-date`. Each element is Medium on the corpus side ([Declared Elements](#declared-elements)).
- The community-page claims come from a model-written summary of each page ([Community Evidence](#community-evidence)). No reader has checked the claim wording against the pages.
- 11 community rows stay unregistered. CM11 and CM29 sit on personal blog domains. CM21, CM25, CM26, CM27, CM28 and CM30 cover undeclared candidates. CM9, CM12 and CM31 record gaps, with no finding to cite.
- 10 registered sources carry no entry, and the checker lists the 10 sources as uncited: L33, L36 and L37 (decision-record), L41 and L46 (citation-file), L42 (build-provenance), L48, L52 and L58 (bill-of-materials), and L68. Each source except L68 backs an undeclared candidate. L68 covers profile READMEs and template repositories, outside every candidate.
- The survey source has no URL, and the checker lists the source as needing verification. The survey counts and reads are in this document.
- The preset has no marks file, so the Explorer derives a monogram for each concept from the concept's label ([universes/README.md](../universes/README.md)).

### Sources in the Guidance File

| Guidance id | Row | Grade | Entries |
| --- | --- | --- | --- |
| `standard-readme` | L1 | B | dispute 1 |
| `github-readmes` | L2 | B | advice 3, placement 1 |
| `github-community-profile` | L3 | B | placement 1 |
| `github-default-health-files` | L4 | B | placement 3 |
| `github-status-badge` | L5 | B | placement 1 |
| `osg-starting` | L6 | B | advice 2 |
| `wtd-docs-as-code` | L7 | B | advice 1 |
| `wtd-beginners-guide` | L8 | B | advice 1 |
| `google-docguide` | L9 | B | advice 8 |
| `bestpractices-criteria` | L10 | B | advice 2 |
| `badge-study` | L11 | B | advice 2 |
| `readme-content-study` | L12 | B | practice 2 |
| `diataxis` | L13 | C | practice 3 |
| `github-contributing` | L14 | B | placement 2 |
| `osg-conduct-governance` | L15 | B | advice 4 |
| `github-issue-templates` | L16 | B | placement 3 |
| `github-code-owners` | L17 | B | advice 2, placement 1 |
| `github-support` | L18 | B | placement 2 |
| `contributor-covenant` | L19 | B | advice 6 |
| `cncf-project-template` | L20 | B | advice 6 |
| `agents-md` | L21 | B | advice 5 |
| `claude-code-memory` | L22 | B | advice 2 |
| `copilot-instructions` | L23 | B | placement 1 |
| `agent-readmes-study` | L24 | C | practice 1 |
| `agentsmd-eval-study` | L25 | C | dispute 1 |
| `conventional-commits` | L26 | A | advice 4 |
| `semver` | L27 | A | advice 4 |
| `keep-a-changelog` | L28 | B | advice 19, distinction 1 |
| `git-submitting-patches` | L29 | A | advice 4 |
| `kernel-submitting-patches` | L30 | A | advice 3 |
| `google-cl-descriptions` | L31 | B | advice 4 |
| `github-generated-notes` | L32 | B | advice 2 |
| `aws-adr-process` | L33 | B | Uncited |
| `pep-1` | L34 | B | advice 2 |
| `rust-rfc-template` | L35 | B | advice 5 |
| `madr-4` | L36 | B | Uncited |
| `nygard-adr` | L37 | C | Uncited |
| `commit-message-blog` | L38 | C | dispute 1 |
| `spdx-expressions` | L39 | A | advice 1 |
| `reuse-spec` | L40 | A | advice 3 |
| `citation-file-format` | L41 | A | Uncited |
| `slsa-build` | L42 | A | Uncited |
| `github-security-policy` | L43 | B | advice 2 |
| `github-private-reporting` | L44 | B | placement 1 |
| `github-licensing` | L45 | B | placement 1 |
| `github-citation` | L46 | B | Uncited |
| `github-funding` | L47 | B | advice 2, placement 1 |
| `github-sbom-export` | L48 | B | Uncited |
| `openssf-disclosure-guide` | L49 | B | advice 3 |
| `scorecard-checks` | L50 | B | practice 1 |
| `openssf-baseline` | L51 | B | advice 28, distinction 1 |
| `cisa-sbom-2026` | L52 | B | Uncited |
| `choosealicense` | L53 | B | advice 1 |
| `chaoss-metrics` | L54 | B | practice 1 |
| `security-md-study` | L55 | B (paper) | practice 1 |
| `scorecard-outcomes-study` | L56 | C | dispute 1 |
| `npm-security-study` | L57 | C | practice 1 |
| `sbom-survey-2021` | L58 | C | Uncited |
| `gitlab-projects` | L59 | B | placement 1 |
| `gitlab-repository-files` | L60 | B | placement 1 |
| `gitlab-description-templates` | L61 | B | placement 2 |
| `gitlab-code-owners` | L62 | B | placement 2 |
| `gitlab-changelogs` | L63 | B | placement 1 |
| `gitlab-web-editor` | L64 | B | placement 1 |
| `gitlab-agents-md` | L65 | B | placement 1 |
| `gitea-templates` | L66 | B | placement 1 |
| `gitea-code-owners` | L67 | B | placement 1 |
| `gitea-profile-templates` | L68 | B | Uncited |
| `forgejo-templates` | L69 | B | placement 1 |
| `forgejo-repository` | L70 | B | placement 1 |
| `codeberg-licensing` | L71 | B | placement 2 |
| `bitbucket-readme` | L72 | B | placement 1 |
| `bitbucket-code-owners` | L73 | B | placement 2 |
| `bitbucket-pr-templates` | L74 | B | placement 1 |
| `sourcehut-manuals` | L75 | B | placement 1 |
| `azure-pr-templates` | L76 | B | placement 2 |
| `azure-readme` | L77 | B | advice 1 |
| `gitee-templates` | L78 | B | placement 1 |
| `gitee-code-owners` | L79 | B | placement 1 |
| `repository-contents-study` | L80 | C | practice 1 |
| `apache-2` | L81 | B | advice 2, distinction 1 |
| `dco` | L82 | B | advice 2 |
| `lf-generative-ai` | L83 | B | advice 4 |
| `github-archiving` | L84 | B | advice 1 |
| `hn-readme-contents` | CM1, CM2 | C | dispute 1, practice 3 |
| `hn-readme-status` | CM3 | C | dispute 2 |
| `hn-commit-messages` | CM4, CM5 | C | dispute 2, practice 2 |
| `hn-conventional-commits` | CM6 | C | dispute 1, practice 1 |
| `hn-pr-descriptions` | CM7, CM8 | C | dispute 1, practice 1 |
| `redhat-security-policies` | CM10 | C | practice 2 |
| `hn-issue-templates` | CM13 | C | dispute 1, practice 1 |
| `hn-ai-disclosure` | CM14 | C | dispute 1 |
| `hn-agent-files` | CM15, CM16 | C | dispute 2, practice 2 |
| `hn-release-notes` | CM17, CM18 | C | dispute 1, practice 2 |
| `hn-release-checklists` | CM19 | C | practice 2 |
| `hn-semver` | CM20 | C | dispute 1, practice 1 |
| `hn-design-docs` | CM22 | C | dispute 1, practice 1 |
| `hn-docs-drift` | CM23 | C | dispute 1, practice 1 |
| `hn-codes-of-conduct` | CM24 | C | dispute 1 |
| `survey` | Counts and reads in this document | Survey | distinction 9, practice 48 |

## Stage 6: Grading and Fixes

Stage 6 adds recognition situations for the code-repository universe spec, grades the universe spec and its type guidance against the evals rules, and fixes the texts that fail. The maintainer reviews the stage 6 answers at the end of the preset work.

### Stage 6 Rules

- A writer model restated one public file of a corpus repository in each situation, following the intake steps in [Evals](../evals/README.md#adding-situations-for-a-universe). The sources and their provenance stay in `.evidence/2026-10-09/situations/code-repository/`.
- Claude models fill every model role except the decision model: the two judges, the light model and the writer of the sort passages. The decision model answers the decision tier and files sort passages and situations beside the Claude models. The maintainer skipped the OpenAI models for this run.
- Dollar figures are API prices, without a Claude or ChatGPT subscription.
- Stage 6 rewords each failing text and keeps its facts and its source. A guidance claim with two points becomes two entries with the same kind, source and condition.
- Run 1 grades the files from stage 5. Run 2 grades the fixed files once, with run 1's sort passages.

### Situations

Stage 6 picked 216 sources. Stored files, release bodies, release tags, commit subjects and repository records came from the frozen raw data. 41 documentation pages and 1 design proposal came from corpus repositories by direct download on 2026-10-09, since the raw data holds only the page names. A writer model saw only the value meanings and restated each pick. A first labeller placed 215 of the 216 situations under the written value. Stage 6 dropped 1 more situation at selection. A second labeller, a Claude model in place of an OpenAI model, placed 209 of the remaining 214 situations under the written value.

| Set | Values | Written | Kept | Fewest cases per value |
| --- | --- | --- | --- | --- |
| `step` | 6 | 36 | 34 | 4 (`use`) |
| `issue-kind` | 5 | 27 | 27 | 5 |
| `docs-task` | 7 | 42 | 39 | 4 (`configure`) |
| `contributor-assertion` | 3 | 18 | 18 | 6 |
| `repository-state` | 2 | 13 | 13 | 4 (`archived`) |
| `notes-writing` | 4 | 27 | 26 | 5 (`from-change-notes`) |
| `notes-place` | 3 | 18 | 18 | 6 |
| `commit-convention` | 3 | 18 | 18 | 6 |
| `version-pattern` | 3 | 17 | 16 | 4 (`calendar`, `other`) |

- `archived` holds all 4 archived corpus repositories, the fewest cases a value may have.
- The second labeller placed the minio case, with tags made of a word and a date and time, under `calendar`, so the intake dropped the case. `other` keeps tmux, ghostty, NetNewsWire and jq. The [Cases by Repository Kind](#cases-by-repository-kind) table still counts minio under `other`.
- The jq case joined after the minio case dropped. Its tags mix two and three numbers, and both labellers placed the case under `other`.
- Stage 6 reworded one meaning after the red-flag check (row M1). Both labellers relabelled the `contributor-assertion` set against the new meaning, and the set kept all 18 cases.
- A review after run 2 reworded the `area-prefix` meaning (row M2). Both labellers relabelled the `commit-convention` set against the new meaning, and the set kept all 18 cases.

### Grades Before and After Fixes

Run 1 is `universe-20261009T142648330815Z` for the grade and sorting and `universe-20261009T145144252900Z` for recognition. Run 2 is `universe-20261009T151853022707Z`, all tiers in one run. The evaluation report shows run 2.

| Measure | Run 1 | Run 2 |
| --- | --- | --- |
| Universe grade | 3856 cases: 3530 pass, 150 fail, 176 undecided | 4278 cases: 4037 pass, 71 fail, 170 undecided |
| Recognition | 26 of 36 values pass; 10 values fail with every reader, 3 values with the two judges alone | 26 of 36 values pass; 10 values fail with every reader, 0 values with the two judges alone |
| Sorting | 105 members: 74 pass, 27 fail, 4 undecided | 105 members: 74 pass, 27 fail, 4 undecided |
| Cost at API prices | judges $44.07; sorting $9.53; recognition $12.11 | judges $47.13; sorting and recognition $14.40 |

The guidance file grew from 263 to 294 entries between the runs, so run 2 grades more cases.

| Rule | Run 1 pass / fail / undecided | Run 2 pass / fail / undecided |
| --- | --- | --- |
| `one-question` | 80 / 3 / 0 | 82 / 1 / 0 |
| `named-referents` | 407 / 0 / 8 | 426 / 4 / 16 |
| `direct-statement` | 406 / 3 / 6 | 428 / 4 / 14 |
| `plain-words` | 295 / 53 / 67 | 354 / 20 / 72 |
| `one-point-terse` | 324 / 50 / 41 | 395 / 21 / 30 |
| `point-first` | 262 / 2 / 2 | 295 / 0 / 2 |
| `holds-across-scope` | 377 / 20 / 18 | 423 / 8 / 15 |
| `one-term-per-concept` | 432 / 9 / 19 | 480 / 2 / 9 |
| `present-state` | 266 / 0 / 0 | 297 / 0 / 0 |
| `siblings-differ` | 476 / 2 / 0 | 651 / 0 / 1 |
| `action-names-an-action` | 20 / 0 / 0 | 20 / 0 / 0 |
| `questions-distinct` | 77 / 2 / 4 | 76 / 3 / 4 |
| `enablements-distinct` | 18 / 2 / 0 | 20 / 0 / 0 |
| `strength-follows-the-action` | 90 / 4 / 11 | 90 / 8 / 7 |
| `sorts-reliably` | 74 / 27 / 4 | 74 / 27 / 4 |
| `values-recognised` | 26 / 10 / 0 | 26 / 10 / 0 |

| Set | Run 1 | Run 2 |
| --- | --- | --- |
| `step` | Fail: `use`, `build`, `review`, `release` | Fail: `propose`, `build`, `review`; the two judges place 33 of 34 cases right |
| `issue-kind` | Pass | Pass |
| `docs-task` | Fail: `install`, `get-started`, `use`, `look-up` | Fail: `install`, `get-started`, `use`, `look-up`, `fix-an-error` |
| `contributor-assertion` | Pass | Pass |
| `repository-state` | Pass | Pass |
| `notes-writing` | Pass | Pass |
| `notes-place` | Pass | Pass |
| `commit-convention` | Pass | Pass |
| `version-pattern` | Fail: `major-minor-patch`, `calendar` | Fail: `major-minor-patch`, `calendar` |

In run 2, the 10 values fail only on the decision model's answers: with the two judges and the light model alone, every value passes. In run 1, all four readers filed the private vulnerability report under `propose`, and three readers filed the cases of reading release notes before an upgrade under `use`.

### Changes to the Universe Spec

| # | Declaration | Before | After | Run 1 evidence |
| --- | --- | --- | --- | --- |
| U1 | `step` value `use` | Is the reader installing or running the software? | Is the reader installing or running the software, or notifying the maintainers of a vulnerability? | Recognition run 1: all 4 readers filed the private vulnerability report under `propose` |
| U2 | `step` value `review` | Is the reader deciding whether to accept or keep a change? | Is the reader deciding whether to accept or keep a change, or whose approval the change needs? | Recognition run 1: 3 of 4 readers filed the code-owners case under `propose` |
| U3 | `step` value `release` | Is a maintainer publishing a release or is someone distributing a copy of the software? | Is the reader publishing a release, deciding whether to move to a newer release, or distributing a copy of the software? | Recognition run 1: 3 readers filed 3 cases of reading release notes before upgrading under `use`, 1 reader under `choose` |
| U4 | `project-status` question | Which status does the project or package have, such as active or deprecated? | Which status does the project or package have, such as active or no longer maintained? | Run 1: plain-words (both judges: "deprecated" is jargon) |
| U5 | `license-id` question | Which licence covers the code? | Which main licence applies to the code? | Run 1: plain-words ("covers" figurative), questions-distinct with `part-licences` |
| U6 | `part-licences` question | Which licence covers each part of the code? | Which licence applies to each part of the code outside the main licence? | Run 1: plain-words, questions-distinct with `license-id` |
| U7 | `bundled-licences` question | Which licence covers each third-party component that the software includes? | Which licence applies to each component from another project that the software includes? | Run 1: plain-words ("covers", "third-party component") |
| U8 | `change-kind` question | Which kind of change does the contributor make, such as a bug fix or a new feature? | Which kind is the change, such as a bug fix or a new feature? | Run 1: strength-follows-the-action in `release-notes` (the question named one contributor's change); sort misfilings in `commit-message` and `change-description` |
| U9 | `related-changes` question | Which issues and earlier changes does the change refer to? | Which earlier issues or changes does the change refer to? | Run 1: one-question (decision model: two asks, 0.91) |
| U10 | `conduct-scope` question | Which places and activities does the code of conduct apply to? | Which spaces does the code of conduct apply to, such as forums, events or chats? | Run 1: one-question (decision model, 0.87) |
| U11 | `release-note-line` question | Which line describes the change in the release notes? | Which entry in the release notes describes each change? | Run 1: strength-follows-the-action in `release-notes` (judges could not tell the purpose of one line) |
| U12 | `reporter-environment` question | Which software version and platform does the reporter use? | Which setup does the reporter use, such as the software version and the platform? | Run 1: one-question (decision model, 0.95) |
| U13 | `help-wanted` question | Which planned work do the maintainers ask contributors to help build? | Which planned work do the maintainers ask contributors to help with? | Run 1: holds-across-scope ("build" leaves out documentation and other work) |
| U14 | `roadmap-date` question | When did the maintainers last update the roadmap? | When did the maintainers last update the plan for upcoming work? | Run 1: plain-words ("roadmap" figurative) |
| U15 | `agent-instructions` action | follow the project's rules and its build and test commands while working on the code | follow the project's rules for building, testing and changing the code | Run 1: one-point-terse (two stacked instructions and a trailing qualifier) |
| U16 | `documentation-set` action | complete a task with the software, such as installing the software or fixing an error | complete a task with the software, such as installing it or fixing an error | Run 1: one-point-terse (repeated "the software") |
| U17 | `change-description` actor | a reviewer | a maintainer | Run 1: one-term-per-concept ("reviewer" is a second term for the maintainer role) |
| U18 | `notice-file` actor | anyone who redistributes the software or a work built from the software | anyone who redistributes the software, alone or inside another work | Run 1: one-point-terse (repeated "the software") |
| U19 | `architecture-overview` action | find the parts of the code to read before making or reviewing a change | learn how the main parts of the code work together before making or reviewing a change | Run 1: enablements-distinct with `folder-readme` (both "find" code to read) |
| M1 | `contributor-assertion` meaning of `none` (situations answers file) | The project asks contributors for neither a sign-off line nor a signed agreement. | The project accepts changes without a sign-off line or a signed agreement. | Red-flag check: negated obligation (decision model, 0.64) |

### Changes to the Guidance

101 claims changed: 69 reworded, 31 split into separate entries and 1 removed as a near-duplicate of its sibling. The tallies in [Guidance Kinds](#guidance-kinds) and [Sources in the Guidance File](#sources-in-the-guidance-file) give the counts after the changes. A split entry keeps the original entry's kind, source and condition.

| # | Entry | Before | After | Run 1 rules failed |
| --- | --- | --- | --- | --- |
| G1 | `artifacts.agent-instructions[0]` | Write the agent file in plain Markdown with any headings; a coding agent reads the agent file nearest to the code under edit. | Write the agent file in plain Markdown with any headings. / A coding agent reads the agent file nearest to the code it edits. | one-point-terse |
| G2 | `artifacts.agent-instructions[2]` | Treat the agent file as context for the agent, and enforce rules with hooks or checks. | Treat the agent file as context for the agent, and enforce rules with scripts or checks that run automatically. | plain-words |
| G3 | `artifacts.agent-instructions[4]` | GitLab Duo reads AGENTS.md at user, root and sub-folder level, nearest file first. | GitLab Duo reads AGENTS.md from the developer's personal settings, the repository root and sub-folders, nearest file first. | one-term-per-concept |
| G4 | `artifacts.agent-instructions[6]` | A study of 2,303 agent files finds test procedures in about three quarters of the files and architecture notes in about two thirds of the files. | In a study of 2,303 agent files, about three quarters of the files give test procedures and about two thirds give architecture notes. | one-point-terse |
| G5 | `artifacts.agent-instructions[7]` | Practitioners record facts missing from the code, such as commands, conventions and past failures, and update the agent file after agent failures. | Practitioners record in the agent file the facts missing from the code, such as commands, conventions and past failures. / Practitioners update the agent file after agent failures. | one-point-terse |
| G6 | `artifacts.agent-instructions[8]` | Commenters object to agent files that repeat the README and CONTRIBUTING, and find that file paths and component names go stale first. | Commenters object to agent files that repeat the README and CONTRIBUTING. / Commenters find that file paths and component names in agent files go out of date first. | one-point-terse, plain-words |
| G7 | `artifacts.architecture-overview[0]` | In the architecture overview, document every action and actor in the system, and update the overview for each new feature or breaking change. | In the architecture overview, document each action and actor in the system. / Update the architecture overview for each new feature or breaking change. | holds-across-scope, one-point-terse |
| G8 | `artifacts.change-description[4]` | Azure Repos offers default, branch-specific and additional pull request templates, and treats each template as a suggestion. | Azure Repos offers default, branch-specific and additional pull request templates. / Azure Repos treats each pull request template as a suggestion. | one-point-terse |
| G9 | `artifacts.code-of-conduct[0]` | Adopt a code of conduct early, explain the enforcement steps before any incident, and give a private reporting route. | Adopt a code of conduct early. / Explain the enforcement steps of the code of conduct before any incident. / Give a private way to report a breach of the code of conduct. | one-point-terse, plain-words |
| G10 | `artifacts.code-owners[2]` | GitLab reads CODEOWNERS from the root, the docs folder or the .gitlab folder, and can require owner approval on protected branches. | GitLab reads CODEOWNERS from the root, the docs folder or the .gitlab folder. / GitLab can require approval from code owners on protected branches. | one-point-terse |
| G11 | `artifacts.code-owners[5]` | Bitbucket Cloud reads .bitbucket/CODEOWNERS and offers several strategies for picking reviewers. | Bitbucket Cloud reads .bitbucket/CODEOWNERS. / Bitbucket Cloud offers several ways to pick reviewers from the code owners. | one-point-terse |
| G12 | `artifacts.commit-message[0]` | Commenters find that commit messages survive moves between tools more often than pull request threads or issue tracker entries. | Commenters find that commit messages stay with a project through a move to other tools more often than pull request threads or issue tracker entries. | plain-words |
| G13 | `artifacts.contributing-guide[0]` | Explain the steps for sending a change and reaching the maintainers, or state that the project takes no changes from the public. | Explain the steps for sending a change and reaching the maintainers, or state that the project accepts changes only from its maintainers. | direct-statement |
| G14 | `artifacts.contributing-guide[2]` | In the contributing guide, cover reporting a bug, suggesting a feature, setting up the environment and running the tests. | In the contributing guide, explain how to report a bug, suggest a feature, set up the environment and run the tests. | plain-words |
| G15 | `artifacts.contributing-guide[5]` | GitHub reads CONTRIBUTING from the .github folder, the root or the docs folder, and links the file when someone opens an issue or pull request. | GitHub reads CONTRIBUTING from the .github folder, the root or the docs folder. / GitHub links the CONTRIBUTING file when someone opens an issue or pull request. | one-point-terse |
| G16 | `artifacts.design-proposal[1]` | Teams write proposals for changes that span teams, are hard to reverse or have unclear requirements. | Teams write design proposals for work that involves several teams, is hard to undo or has unclear requirements. | one-term-per-concept, plain-words |
| G17 | `artifacts.design-proposal[2]` | Commenters complain of months-long consensus, proposals written as a formality and design documents outdated once finished. | Commenters complain that agreement on a design proposal takes months, that authors write proposals as a formality and that proposals are out of date once finished. | one-term-per-concept |
| G18 | `artifacts.design-proposal[3]` | The maintainers approve a design proposal before anyone builds the design; a reviewer merges a change after reading the change description. | The maintainers decide on a design proposal before anyone builds the design, and on a change description before merging the change. | one-point-terse, one-term-per-concept |
| G19 | `artifacts.development-guide[0]` | Publish the build steps with the contributor documentation, or as Makefile targets or other scripts. | Publish the build steps in the contributor documentation or as build scripts. | plain-words |
| G20 | `artifacts.documentation-set[0]` | Cover installing, configuring and using every basic feature, with clear warnings on dangerous or destructive actions. | Explain how to install, configure and use every basic feature. / Add clear warnings to actions that can cause harm or destroy data. | one-point-terse, plain-words |
| G21 | `artifacts.documentation-set[1]` | Keep the docs in version control, review the docs like code and test the docs automatically. | Manage the documentation like code: keep it in version control, review its changes and test it automatically. | one-point-terse, plain-words |
| G22 | `artifacts.documentation-set[9]` | Commenters find that docs kept apart from the repository go stale, while docs generated from code or tied to tests stay accurate. | Commenters find that documentation kept outside the repository goes out of date, while documentation generated from code or checked by tests stays accurate. | plain-words |
| G23 | `artifacts.folder-readme[0]` | Write the minimum documentation a reader needs, and delete documentation for code that the project removed. | Write the minimum documentation a reader needs. / Delete the documentation for code that the project removed. | one-point-terse |
| G24 | `artifacts.folder-readme[1]` | The architecture overview covers the whole system or one subsystem; a folder README covers one folder. | The architecture overview describes the whole system or one large part of the system; a folder README describes one folder. | plain-words |
| G25 | `artifacts.funding-file[1]` | Most surveyed funding files name accounts under the github key. | Most surveyed funding files list accounts on GitHub Sponsors. | plain-words |
| G26 | `artifacts.issue-report[0]` | Give the defect-reporting steps, and set expectations for triage and resolution. | Explain how to report a defect. / Tell reporters how the maintainers handle new defect reports and what response to expect. | direct-statement, one-point-terse, plain-words |
| G27 | `artifacts.issue-report[1]` | GitHub reads issue templates and forms from .github/ISSUE_TEMPLATE, and a form can mark fields as required. | GitHub reads issue templates and forms from .github/ISSUE_TEMPLATE. / A GitHub issue form can mark fields as required. | one-point-terse |
| G28 | `artifacts.issue-report[5]` | Gitee reads issue templates from .gitee/ISSUE_TEMPLATE, then from .github and a namespace-level repository. | Gitee reads issue templates from .gitee/ISSUE_TEMPLATE, then from .github, then from a repository shared by every project in the account. | plain-words |
| G29 | `artifacts.issue-report[7]` | Some maintainers let bots close issues filed without the template; other maintainers label each such issue and leave the issue open. | Some maintainers let bots close issues filed without the template, while other maintainers label such issues and keep them open. | one-point-terse |
| G30 | `artifacts.license-file[6]` | Codeberg accepts the licence text in a root file or a LICENSES folder, and recommends a licence header in each file. | Codeberg accepts the licence text in a root file or a LICENSES folder. / Codeberg recommends a licence header in each file. | one-point-terse |
| G31 | `artifacts.notice-file[0]` | A redistributor of an Apache-2.0 work keeps the NOTICE contents and may add the redistributor's own notices beside the original notices. | A redistributor of an Apache-2.0 work keeps the NOTICE contents and may add their own notices beside the originals. | one-point-terse |
| G32 | `artifacts.readme[1]` | Write the README for users, developers and contributors, and give each group of readers the parts that group needs. | Write the README for users, contributors and developers who build on the software, and give each group the parts it needs. | one-term-per-concept |
| G33 | `artifacts.readme[3]` | Commenters agree on a short core for a README: the project's purpose, the project's use and ways to help. | Commenters agree that every README needs at least the project's purpose, how to use the project and ways to help. | plain-words |
| G34 | `artifacts.release-notes[1]` | Put the changelog under a heading such as '## Changelog', so tools can find the changelog. | Put the changelog under a heading such as '## Changelog' so tools can find the section. | one-point-terse |
| G35 | `artifacts.release-notes[4]` | Readers of release notes check whether each fix applies to their setup, and want breaking changes listed apart. | Readers of release notes check whether each fix applies to their setup. / Readers of release notes want the changes that break existing uses listed apart. | one-point-terse, one-term-per-concept |
| G36 | `artifacts.release-procedure[0]` | In the release procedure, cover creating a release, the release roles, the release cadence, the versioning and the supported versions. | In the release procedure, explain how to create a release, who does each release task, how often releases come out, how versions are numbered and which versions get support. | plain-words |
| G37 | `artifacts.security-policy[1]` | Keep a coordinated disclosure policy in SECURITY.md at the root, with a reporting method and a response timeframe. | Keep a policy in SECURITY.md at the root that tells reporters how to report a vulnerability privately and how soon to expect a response. | plain-words |
| G38 | `artifacts.security-policy[2]` | GitHub reads SECURITY.md from the .github folder, the root or the docs folder, and an organisation can supply a default file. | GitHub reads SECURITY.md from the .github folder, the root or the docs folder. / On GitHub, an organisation can supply a default SECURITY.md for its repositories. | one-point-terse |
| G39 | `elements.ai-use-record[0]` | Name the AI tools used, and attribute any third-party material found in the output. | Name the AI tools used for the change. / Attribute any third-party material found in AI output. | one-point-terse |
| G40 | `elements.breaking-change[0]` | Mark each breaking entry with a short 'Breaking:' label, and keep the entry under its change type. | Mark each changelog entry that breaks existing uses with a short 'Breaking:' label, and keep the entry under its usual section, such as Changed or Removed. | plain-words |
| G41 | `elements.breaking-change[2]` | Under Conventional Commits, mark a breaking change with ! after the type or with a BREAKING CHANGE footer. | Under Conventional Commits, mark a breaking change with ! after the type word, as in feat!, or with a BREAKING CHANGE line at the end of the message. | plain-words |
| G42 | `elements.change-kind[0]` | Use fix for a bug fix and feat for a new feature; tools map fix to a patch release and feat to a minor release. | Use fix for a bug fix and feat for a new feature; release tools then raise the last version number for a fix and the middle number for a feature. | holds-across-scope, one-point-terse, plain-words |
| G43 | `elements.change-kind[1]` | Sort release entries into six types: Added, Changed, Deprecated, Removed, Fixed and Security. | Sort changelog entries under six headings: Added, Changed, Deprecated (marked for later removal), Removed, Fixed and Security. | plain-words |
| G44 | `elements.change-reason[0]` | In the commit body, explain the problem and why the change fixes the problem. | In the commit body, state the problem, then explain why the change solves that problem. | one-point-terse |
| G45 | `elements.change-reason[1]` | Describe the problem and the user-visible impact, and give numbers for a performance change. | Describe the problem and any effect users notice, and give measurements for a change to speed. | holds-across-scope |
| G46 | `elements.change-reason[2]` | Commenters put the reason for a change in the commit body: the code shows the edit, and readers find the message through blame, log, bisect and revert. | Commenters put the reason for a change in the commit body, since the code shows only the edit and readers reach the message through Git's history tools. | plain-words |
| G47 | `elements.change-summary[0]` | Write the commit subject in the imperative mood, in about 50 characters. | Write the commit subject as a command, such as 'Fix crash on empty input', in about 50 characters. | plain-words |
| G48 | `elements.change-summary[2]` | Open the commit subject with the code area, a colon and a short summary phrase. | Open the commit subject with the area of the repository, a colon and a short summary phrase. | holds-across-scope |
| G49 | `elements.commit-format[1]` | Open each commit subject with the code area and a colon, such as 'parser: '. | Open each commit subject with the area of the repository and a colon, such as 'parser: '. | holds-across-scope |
| G50 | `elements.components[0]` | Treat any subsystem or entity that can influence another part of the system as an actor. | Count as an actor any part of the system, or any outside party, that can affect another part of the system. | plain-words |
| G51 | `elements.conduct-consequences[1]` | Covenant 3.0 lists the consequences as escalating steps to repair harm. | Contributor Covenant 3.0 lists the consequences as steps of rising severity, aimed at repairing harm. | plain-words |
| G52 | `elements.copyright-holder[1]` | Most surveyed licence files carry a dated copyright line. | Most surveyed licence files include a copyright line with a year. | plain-words |
| G53 | `elements.design-alternatives[0]` | Compare the proposed design with the alternatives the authors considered, and state the cost of leaving the problem unsolved. | Compare the proposed design with the alternatives the authors considered. / State the cost of leaving the problem unsolved. | one-point-terse |
| G54 | `elements.docs-location[0]` | Link the full documentation from every package README. | In a repository with several packages, link the full documentation from every package README. | holds-across-scope |
| G55 | `elements.docs-version[0]` | A few surveyed projects keep separate documentation for each release, in one folder per release. | A few surveyed projects keep one documentation folder for each release. | one-point-terse |
| G56 | `elements.duplicate-search[0]` | Some surveyed templates ask reporters to confirm a search of existing issues, and few forms require the search confirmation. | Some surveyed templates ask reporters to confirm a search of existing issues. / A few surveyed issue forms require the search confirmation. | one-point-terse |
| G57 | `elements.first-reply-days[0]` | Give a clear timeframe for the first response to a report. | (entry removed) | siblings-differ |
| G58 | `elements.project-purpose[0]` | Describe the software and the problem the software solves. | Describe the software and the problem it solves. | holds-across-scope, one-point-terse, siblings-differ |
| G59 | `elements.project-purpose[1]` | State why the project is useful, next to the project description. | Next to the project description, list the benefits a user gets from the project. | siblings-differ (pair with `project-purpose[0]`) |
| G60 | `elements.first-result[0]` | Show a basic usage example that a new user can copy and run. | For software, show a basic usage example that a new user can copy and run. | holds-across-scope |
| G61 | `elements.first-result[1]` | Commenters keep usage examples in the README, plus a demo for projects with a user interface. | Commenters keep usage examples in the README. / Commenters add a demo to the README of a project with a user interface. | one-point-terse |
| G62 | `elements.folder-purpose[0]` | State the purpose of the files in the folder, and link to further documentation. | State the purpose of the files in the folder. / Link to further documentation from the folder README. | one-point-terse |
| G63 | `elements.help-channel[1]` | GitHub links a SUPPORT file, kept in the root, the docs folder or the .github folder, when someone opens an issue. | GitHub reads a SUPPORT file, which lists ways to get help, from the root, the docs folder or the .github folder. / GitHub links the SUPPORT file when someone opens an issue. | direct-statement, one-point-terse, plain-words |
| G64 | `elements.help-channel[2]` | About half of surveyed READMEs name a help channel, and few projects keep a SUPPORT file. | About half of surveyed READMEs name a place to ask for help. / Few surveyed projects keep a SUPPORT file that lists ways to get help. | one-point-terse, plain-words |
| G65 | `elements.install-steps[0]` | Tell a new user how to get the software, such as the package to install or the file to download. | Tell a new user how to get the project's files, such as the package to install or the file to download. | holds-across-scope |
| G66 | `elements.install-steps[1]` | Install steps appear in READMEs of every surveyed repository kind, including theme collections and model releases. | Install steps appear in the READMEs of every kind of surveyed repository, including collections of themes and published machine learning models. | one-term-per-concept, plain-words |
| G67 | `elements.license-id[1]` | Half of surveyed READMEs carry a licence section. | Half of surveyed READMEs include a licence section. | plain-words |
| G68 | `elements.maintainers[1]` | Give a package's points of contact in the package README. | In a repository with several packages, name each package's contacts in its README. | holds-across-scope, one-point-terse |
| G69 | `elements.part-licences[0]` | Under REUSE, every file carries a licence and copyright notice, and a LICENSES folder holds the text of each licence. | Under the REUSE specification for licence notices, every file includes a licence and copyright notice. / Under the REUSE specification for licence notices, a LICENSES folder holds the text of each licence. | one-point-terse, plain-words |
| G70 | `elements.part-licences[1]` | Surveyed projects with parts under different licences map each licence to the files or folders under that licence, as in a LICENSING file. | Surveyed projects with parts under different licences list which files or folders fall under each licence, as in a LICENSING file. | plain-words |
| G71 | `elements.path-approvers[1]` | About half of surveyed code-owners files carry a catch-all line that names a default owner. | About half of surveyed code-owners files include a line that names a default owner for every file. | plain-words |
| G72 | `elements.project-purpose[2]` | In a study of 393 READMEs, almost every file describes the project, and about a quarter of the files explain the reason to use the project. | In a study of 393 READMEs, almost every file describes the project. / In a study of 393 READMEs, about a quarter of the files explain the reason to use the project. | one-point-terse |
| G73 | `elements.project-status[0]` | Give each package's status, such as deprecated, in the package README. | In a repository with several packages, give each package's status, such as no longer maintained, in its README. | holds-across-scope |
| G74 | `elements.project-status[2]` | Show status with badges that a service checks, such as build or coverage badges; a study of npm badges finds that only service-checked badges signal quality. | Show status with badges that an outside service updates, such as a badge for passing builds. / A study of npm badges finds that only badges backed by an automatic check go with better code quality. | holds-across-scope, plain-words |
| G75 | `elements.project-status[3]` | A workflow status badge shows whether the latest run on the default branch passed. | A workflow status badge shows whether the most recent automatic build and test run on the main branch passed. | plain-words |
| G76 | `elements.project-status[4]` | Most archived repositories in the survey put an end-of-life notice at the top of the README. | Most archived repositories in the survey put a notice that work has stopped at the top of the README. | plain-words |
| G77 | `elements.project-status[5]` | Users want a status line, such as active, finished or maintenance-only, while maintainers dislike questions about a dead project. | Users want a status line, such as active, finished or fixes only. / Maintainers dislike questions about a project nobody maintains any more. | one-point-terse, plain-words |
| G78 | `elements.proposed-design[0]` | Explain the proposed design twice: once for users, with examples, and once in enough detail to build the design. | Explain the proposed design twice: once for the people who will use the result, with examples, and once in enough detail to carry out the design. | holds-across-scope |
| G79 | `elements.related-changes[0]` | In a Fixes: trailer, name the commit that introduced the bug, with the commit hash and subject. | In a 'Fixes:' line at the end of the commit message, name the commit that introduced the bug by its hash and subject. | plain-words |
| G80 | `elements.related-changes[1]` | Link the bug, the benchmark results and the design documents behind the change. | Link the records behind the change, such as the bug report, benchmark results or design documents. | holds-across-scope |
| G81 | `elements.release-note-line[0]` | Generated release notes list merged pull requests by title, so write each title as a line a user understands. | When a tool builds the release notes from merged pull request titles, write each title as a line a user understands. | holds-across-scope |
| G82 | `elements.release-note-line[1]` | GitLab builds changelog entries from a Changelog trailer in each commit. | GitLab builds changelog entries from a 'Changelog:' line at the end of each commit message. | plain-words |
| G83 | `elements.release-schedule[0]` | State the release cadence. | State how often releases come out. | plain-words |
| G84 | `elements.release-steps[2]` | Teams automate a release step by step, starting from a script that prints each step and waits for a person to finish the step. | Maintainers automate the release steps one at a time, starting from a script that prints each step and waits for a person to finish the step. | holds-across-scope, one-term-per-concept |
| G85 | `elements.report-channel[0]` | Give a private reporting route, such as a security email address, a web form or the forge's private reporting tool. | Give a private way to report a vulnerability, such as a security email address, a web form or the code host's private reporting tool. | plain-words |
| G86 | `elements.report-channel[2]` | Most surveyed security policies name a reporting channel, and a few security policies only point to another page. | Most surveyed security policies name a way to report a vulnerability. / A few surveyed security policies only point to another page. | one-point-terse |
| G87 | `elements.required-evidence[0]` | List the testing requirements that the maintainers set for accepting a change. | List the tests a change needs before the maintainers accept the change. | one-point-terse |
| G88 | `elements.security-fixes[0]` | Lead each security entry with the CVE identifier, and link to the full advisory. | Start each security entry with the vulnerability's CVE identifier, when one exists. / Link each security entry to the full security advisory. | holds-across-scope, one-point-terse, plain-words |
| G89 | `elements.settings-reference[0]` | Explain each setting a user can change to configure the basic features. | Explain each setting of the basic features. | one-point-terse |
| G90 | `elements.sign-off[2]` | Use a status check to confirm that each commit carries the sign-off. | Use an automatic check on each change to confirm that every commit includes the sign-off line. | plain-words |
| G91 | `elements.supported-versions[1]` | For each release, give the end date of security updates. | If releases get security updates for a set time, give the end date for each release. | holds-across-scope |
| G92 | `elements.undecided-parts[0]` | Group open questions by when the authors settle each question: before acceptance, during the build or in later work. | Group open questions by when the authors settle each question: before acceptance, while carrying out the design or in later work. | holds-across-scope |
| G93 | `elements.verification[1]` | Maintainers state the required checks for every change in the contributing guide; each contributor records the checks run on a change in the change description. | The contributing guide states the checks every change needs, and the change description records the checks run on one change. | one-point-terse |
| G94 | `elements.vulnerability-scope[0]` | An article for maintainers finds that useful security policies separate vulnerabilities from hardening issues and state the security boundary. | Useful security policies separate vulnerabilities from general security improvements and state which threats the project defends against, according to an article for maintainers. | one-point-terse, plain-words, point-first |
| G95 | `factors.commit-convention[0]` | The commit type and the breaking marker let tools pick the next version and draft the changelog. | Under Conventional Commits, the type word and the breaking-change mark let tools pick the next version number and draft the changelog. | plain-words |
| G96 | `factors.commit-convention[2]` | Commenters name issue keys, Git trailers and the Linux kernel style as alternatives to Conventional Commits. | Commenters name issue numbers in the subject, key-value lines at the end of the message and the Linux kernel's area prefix as alternatives to Conventional Commits. | plain-words |
| G97 | `factors.commit-convention[3]` | Commenters praise Conventional Commits for tooling and criticise the forced categories and the subject characters spent on the type prefix. | Commenters praise Conventional Commits for the tools that read the format. / Commenters criticise the fixed categories of Conventional Commits and the room the type word takes in a short subject line. | plain-words |
| G98 | `factors.notes-place[0]` | Name the file CHANGELOG.md, list the latest version first and keep an Unreleased section at the top. | In CHANGELOG.md, list the latest version first, below an Unreleased section at the top. | one-point-terse |
| G99 | `factors.notes-place[2]` | The host stores release-page notes in a database, so a project that moves to another host loses the notes. | A project that moves to another host loses the notes on its release pages, because the host stores those notes in a database. | point-first |
| G100 | `factors.version-pattern[0]` | Under Semantic Versioning, declare the public interface; version numbers track changes to the public interface. | Under Semantic Versioning, declare the public interface, such as the commands or functions users rely on; the version number then shows how that interface changed. | one-point-terse, plain-words |
| G101 | `factors.version-pattern[3]` | Practitioners dispute whether semantic versions predict breakage, and agree that release notes stay necessary under any scheme. | Practitioners dispute whether semantic versions predict breakage. / Practitioners agree that release notes stay necessary under any versioning scheme. | one-point-terse |

### Changes After Run 2

A red-flag pass and a review after run 2 changed the texts below. Run 2 graded the earlier wording.

| # | Declaration or entry | Before | After | Reason |
| --- | --- | --- | --- | --- |
| P1 | `step` value `review` | Is the reader deciding whether to accept or keep a change, or whose approval the change needs? | Is the reader deciding whether to accept or keep a change, or whom to ask for approval? | Inside-out clause: "the approval the change needs" |
| P2 | `architecture-overview` action | learn how the main parts of the code work together before making or reviewing a change | learn how the main parts of the code work together | Run 2: one-point-terse (both judges); the timing already names the moment |
| P3 | `notice-file` actor | anyone who redistributes the software, alone or inside another work | anyone who redistributes the software, on its own or inside another work | "alone" read as the person working alone |
| P4 | `artifacts.release-notes[5]` | Readers of release notes want the changes that break existing uses listed apart. | Readers of release notes want a separate list of the changes that break existing uses. | Vague phrase "listed apart" |
| P5 | `artifacts.folder-readme[1]` | Delete the documentation for code that the project removed. | Delete the documentation for removed code. | Inside-out clause: "the project removed" |
| P6 | `artifacts.documentation-set[0]` | Explain how to install, configure and use every basic feature. | Explain how to install the software and how to configure and use every basic feature. | "install" took "every basic feature" as its object |
| P7 | `elements.project-status[3]` | A study of npm badges finds that only badges backed by an automatic check go with better code quality. | A study of npm badges finds that only badges backed by an automatic check are linked to better code quality. | Vague verb phrase "go with" |
| P8 | `elements.project-status[5]` | Most archived repositories in the survey put a notice that work has stopped at the top of the README. | Most archived repositories in the survey open the README with a notice that work has stopped. | "at the top of the README" attached to "work has stopped" |
| P9 | `elements.breaking-change[0]` | Mark each changelog entry that breaks existing uses with a short 'Breaking:' label, and keep the entry under its usual section, such as Changed or Removed. | Mark each changelog entry for a change that breaks existing uses with a short 'Breaking:' label, and keep the entry under its usual section, such as Changed or Removed. | "breaks" had the entry as its subject; the change breaks existing uses |
| P10 | `elements.required-evidence[0]` | List the tests a change needs before the maintainers accept the change. | List the tests the maintainers require before accepting a change. | Inside-out clause: "the tests a change needs" |
| P11 | `elements.change-reason[1]` | Describe the problem and any effect users notice, and give measurements for a change to speed. | Describe the problem and any effect users notice, and give measurements for a change that affects speed. | "a change to speed" reads two ways |
| P12 | `elements.related-changes[0]` | In a 'Fixes:' line at the end of the commit message, name the commit that introduced the bug by its hash and subject. | In a 'Fixes:' line at the end of the commit message, give the hash and subject of the commit that introduced the bug. | "by its hash and subject" attached to "introduced the bug" |
| P13 | `elements.verification[1]` | The contributing guide states the checks every change needs, and the change description records the checks run on one change. | The contributing guide lists the checks required for every change, and the change description lists the checks run on one change. | Inside-out clause: "the checks every change needs" |
| P14 | `elements.proposed-design[0]` | Explain the proposed design twice: once for the people who will use the result, with examples, and once in enough detail to carry out the design. | Explain the proposed design twice: once for the people who will use the changed software, with examples, and once in enough detail to carry out the design. | Placeholder noun "the result" |
| P15 | `elements.duplicate-search[0]` | Some surveyed templates ask reporters to confirm a search of existing issues. | Some surveyed templates ask reporters to confirm that they searched existing issues. | Noun stack "a search of existing issues" |
| P16 | `elements.duplicate-search[1]` | A few surveyed issue forms require the search confirmation. | A few surveyed issue forms require reporters to confirm the search. | Noun stack "the search confirmation" |
| P17 | `factors.commit-convention[2]` | Commenters name issue numbers in the subject, key-value lines at the end of the message and the Linux kernel's area prefix as alternatives to Conventional Commits. | Commenters name three alternatives to Conventional Commits: issue numbers in the subject, key-value lines at the end of the message and the Linux kernel's area prefix. | Main point last, after the list |
| P18 | `factors.commit-convention[4]` | Commenters criticise the fixed categories of Conventional Commits and the room the type word takes in a short subject line. | Commenters criticise the fixed categories of Conventional Commits and the type word, which uses up part of a short subject line. | Inside-out clause: "the room the type word takes" |
| P19 | `artifacts.agent-instructions[5]` | GitLab Duo reads AGENTS.md from the developer's personal settings, the repository root and sub-folders, nearest file first. | GitLab Duo combines the AGENTS.md files in the developer's home configuration folder, the repository root and each sub-folder that holds files for the current task. | The source names a file in a home configuration folder, and GitLab Duo combines the files |
| P20 | `elements.install-steps[1]` | Install steps appear in the READMEs of every kind of surveyed repository, including collections of themes and published machine learning models. | Install steps appear in the READMEs of every kind of surveyed repository, including collections, themes and machine learning model projects. | The 3 collections or themes with install steps hold one theme, one collection of themes and one collection of skills |
| P21 | `elements.duplicate-search[1]` | A few surveyed issue forms require reporters to confirm the search. | Few surveyed bug report forms require reporters to confirm the search. | 2 of 70 bug report forms require the search; G56 had changed "few" to "a few" |
| P22 | `factors.commit-convention[3]` and `[4]` (dispute) | Commenters praise Conventional Commits for the tools that read the format. / Commenters criticise the fixed categories of Conventional Commits and the type word, which uses up part of a short subject line. | Commenters split on Conventional Commits: supporters praise tools that read the format, and critics object to fixed categories and to the type word, which takes room from the subject line. | A dispute entry states a disagreement, and each half of the G97 split states one side alone |
| P23 | `factors.version-pattern[4]` | Kind `dispute` | Kind `practice` | The claim states an agreement; CM20 records the agreement as practice |
| M2 | `commit-convention` meaning of `area-prefix` (situations answers file) | Commit subject lines open with the name of the part of the code that the commit touches, such as a folder, module or subsystem, and a colon. | Commit subject lines open with the name of the edited part of the code, such as a folder, module or subsystem, and a colon. | Inside-out clause: "the part of the code that the commit touches"; both labellers relabelled the set blind, and the set kept all 18 cases |

The same pass reworded 52 situation texts in `cases.yaml`. A pronoun or number at the end of a sentence became the noun it stood for, the six `none` cases of `contributor-assertion` state what the project accepts, and clauses such as "the component it touches" now name the edited part. Each case keeps its facts, its value and both labels.

### Left Open

- Run 2 fails 71 cases: 33 cases on rewritten texts and 38 cases on texts unchanged at stage 6. Of the 38 cases, 2 repeat a run 1 fail kept on purpose, 26 were undecided in run 1 with the two judges split, and 10 passed in run 1. Three of those 10 cases are composition entries under the enablements changed by U15 and U19.
- U15 and U19 each fixed one fail and caused a new fail. After U15, both judges fail `components` and `folder-purpose` in `agent-instructions` on strength: the action names rules, and the two elements describe code. After U19, both judges fail the new action on one-point-terse, fixed by P2 after run 2, and want `part-interactions` core in `architecture-overview`.
- `repro-steps` and `reporter-environment` stay core under `bug-report` on the form counts in [Wiring](#wiring); both judges fail the two elements on strength. The distinction claim on the architecture overview and the documentation set stays as written, because a distinction claim describes both documents.
- After U5 to U7, both judges find that `part-licences` and `bundled-licences` overlap. Both judges also find that `declined-ideas` overlaps `change-refusal`.
- 27 sort members fail in both runs. The light model and the decision model misfile most of the passages, and the two judges file the design-proposal passages under none of the questions.
- In run 2, the readers file sort passages written for the old wording of the 11 changed element questions, as the run notes say.
- No OpenAI model has graded the universe spec or labelled the situations. The intake packets stay in the archive for a blind relabel by an OpenAI model.

## Stage 7: Status and Links

Status on 2026-10-09: the codebase-recordkeeping universe spec 0.1 and its type guidance 0.1 ship in the unreleased version 0.10.0. Both codebase-recordkeeping files pass the checker. The maintainer reviews every stage at the end of the preset work.

- `kb-ingest` and every agent package carry each universe spec in `universes/` with its guidance. The package checks inspect and render each universe spec in the Explorer, and the release check runs the checker on a copy of each universe spec.
- The Explorer refuses a relation kind without phrasing, so the codebase-recordkeeping universe spec declares phrasing for both relation kinds.
  - `feeds`: "May inform" and "May be informed by". In the protocol, `feeds` means that knowledge from the source can inform the target.
  - `distinct-from`: "Serves a different purpose from". Each `distinct-from` edge in [Relations](#relations) joins two definitions that share content but answer different questions or enable different actions.
- The README gallery carries no map of the codebase-recordkeeping universe spec.

Files that still describe a single bundled universe spec: `docs/adapting-the-example.md`, `docs/agent-runtime.md`, `docs/agent-plugins.md`, `docs/how-ingest-works.md`, step 3 of `skills/kb-ingest/SKILL.md` and the placeholder in the universe issue form.

Links:

- [Codebase-recordkeeping universe spec](../universes/codebase-recordkeeping/universe.kbp.yaml)
- [Codebase-recordkeeping type guidance](../universes/codebase-recordkeeping/type-guidance.kbp.yaml)
- [Codebase-recordkeeping situations](../evals/situations/codebase-recordkeeping.yaml)
- [Evaluation Report](../evals/report.md)
- [Universes](../universes/README.md)
- [Universe Contributions](contributing/universe.md)
- [Changelog](../CHANGELOG.md)

## Graded Sources

84 rows: A 8, B 67, C 9. "Read" gives the latest date a person or agent read or checked the source; 2026-10-03 rows were not reread at stage 1. A row joins several pages when the pages make one claim.

### README and Documentation

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | standard-readme specification | standard-readme project | <https://github.com/RichardLitt/standard-readme/blob/main/spec.md> | B (one maintainer) | 2026-10-09 (file present) | README section order; a contents list past 100 lines; licence section last |
| L2 | About READMEs | GitHub Docs | <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes> | B | 2026-10-09 | Five README items: what the project does, why it is useful, how to start, where to get help, who maintains and contributes |
| L3 | About community profiles | GitHub Docs | <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories> | B | 2026-10-09 (link check) | Health files on the community checklist |
| L4 | Creating a default community health file | GitHub Docs | <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file> | B | 2026-10-09 (link check) | Supported health files; lookup order `.github/`, root, `docs/`; organisation fallback |
| L5 | Adding a workflow status badge | GitHub Docs | <https://docs.github.com/en/actions/how-tos/monitor-workflows/add-a-status-badge> | B | 2026-10-09 (link check) | CI badge status |
| L6 | Starting a project | Open Source Guides | <https://opensource.guide/starting-a-project/> | B | 2026-10-09 | README questions; launch files; CONTRIBUTING contents |
| L7 | Docs as Code | Write the Docs | <https://www.writethedocs.org/guide/docs-as-code/> | B | 2026-10-03 | Docs reviewed and tested like code |
| L8 | Beginner's guide to docs | Write the Docs | <https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/> | B | 2026-10-03 | A README template |
| L9 | Documentation best practices; READMEs | Google style guides | <https://google.github.io/styleguide/docguide/best_practices.html>, <https://google.github.io/styleguide/docguide/READMEs.html> | B | 2026-10-09 (READMEs page reread) | Change docs with the code; delete dead docs; a package README holds or points to contents and purpose, contacts, status, usage and documentation links |
| L10 | Best Practices badge criteria (passing) | OpenSSF | <https://www.bestpractices.dev/en/criteria/0> | B | 2026-10-09 | The project describes the software, how to obtain it, and how to report and contribute |
| L11 | Adding Sparkle to Social Coding (ICSE 2018) | ACM | <https://doi.org/10.1145/3180155.3180209> | B | 2026-10-03 | Only assessment badges signal quality; many badges go with lower popularity |
| L12 | Categorizing the content of GitHub README files (Empirical Software Engineering, 2019) | Springer | <https://doi.org/10.1007/s10664-018-9660-3> | B | 2026-10-03 | Section shares across 393 READMEs |
| L13 | Diátaxis | Diátaxis project | <https://diataxis.fr/> | C | 2026-10-09 | Four kinds of documentation: tutorials, how-to guides, reference, explanation |

### Contribution, Governance and Agent Files

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L14 | Setting guidelines for repository contributors | GitHub Docs | <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors> | B | 2026-10-09 (link check) | CONTRIBUTING contents and location |
| L15 | Code of conduct; Leadership and governance | Open Source Guides | <https://opensource.guide/code-of-conduct/>, <https://opensource.guide/leadership-and-governance/> | B | 2026-10-03 | Code of conduct contents and timing; governance models |
| L16 | About issue and pull request templates; issue form syntax | GitHub Docs | <https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates> | B | 2026-10-09 (link check) | Template paths and formats; form keys; required fields |
| L17 | About code owners | GitHub Docs | <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners> | B | 2026-10-09 (link check) | CODEOWNERS syntax; review requests; required approval with branch protection |
| L18 | Adding support resources | GitHub Docs | <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-support-resources-to-your-project> | B | 2026-10-09 (link check) | SUPPORT file location |
| L19 | Contributor Covenant 3.0, with 2.1 as the earlier line | Organization for Ethical Source | <https://www.contributor-covenant.org/version/3/0/code_of_conduct/>, <https://www.contributor-covenant.org/version/2/1/code_of_conduct/> | B | 2026-10-08 | 3.0, current since 2025-07-28: pledge, encouraged and restricted behaviours, reporting, a repair ladder. 2.1: standards, enforcement responsibilities, four enforcement levels |
| L20 | CNCF project template: GOVERNANCE.md, MAINTAINERS.md, ADOPTERS.md, RELEASES.md, REVIEWING.md, DESIGN-PROPOSALS.md, CONTRIBUTOR_LADDER.md | CNCF | <https://github.com/cncf/project-template> | B | 2026-10-09 (headings read) | Governance by maturity; maintainer fields; adopter list; release cadence, roles and supported versions; reviewer process; proposal sections with an optional status |
| L21 | AGENTS.md | Agentic AI Foundation (Linux Foundation) | <https://agents.md/> | B | 2026-10-09 | Purpose of an agent file; the nearest file wins; plain Markdown with any headings |
| L22 | Claude Code memory | Anthropic | <https://code.claude.com/docs/en/memory> | B | 2026-10-09 | Load order; a target under 200 lines; files act as context, and hooks enforce rules; AGENTS.md read in place of CLAUDE.md |
| L23 | Adding repository custom instructions | GitHub Docs | <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions> | B | 2026-10-09 | Five instruction files, including AGENTS.md, CLAUDE.md and GEMINI.md |
| L24 | Agent READMEs (arXiv 2511.12884, v2) | Preprint | <https://arxiv.org/abs/2511.12884> | C | 2026-10-09 | Contents of 2,303 agent files: test procedures 75.9%, architecture 68.1% |
| L25 | Evaluating AGENTS.md (arXiv 2602.11988, v3) | Preprint | <https://arxiv.org/abs/2602.11988> | C | 2026-10-09 | No general task gain from context files; over 20% added inference cost |

### Change History

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L26 | Conventional Commits 1.0.0 | Conventional Commits | <https://www.conventionalcommits.org/en/v1.0.0/> | A | 2026-10-08 | `type(scope): description`; breaking-change marker and footer; mapping to version bumps |
| L27 | Semantic Versioning 2.0.0 | semver.org | <https://semver.org/spec/v2.0.0.html> | A | 2026-10-09 | MAJOR.MINOR.PATCH; declare a public API; deprecate before removing |
| L28 | Keep a Changelog 2.0.0, with 1.1.0 as the earlier line | Keep a Changelog | <https://keepachangelog.com/en/2.0.0/>, <https://keepachangelog.com/en/1.1.0/> | B | 2026-10-08 | Changelog and release notes kept apart; six change types; an inline breaking marker; long upgrade steps in a separate guide; machines draft, humans curate; commit-log diffs a bad practice |
| L29 | SubmittingPatches | Git project | <https://git-scm.com/docs/SubmittingPatches> | A (one project keeps the guide, and adoption outside Git is unmeasured; the scale allows A or B, so the approved A holds) | 2026-10-09 | Imperative subject of about 50 characters, opened with the code area ("area: "); a body with the problem and the reason |
| L30 | Submitting patches | Linux kernel | <https://www.kernel.org/doc/html/latest/process/submitting-patches.html> | A (one project keeps the guide, and commits in 52 corpus repos carry the sign-off line; the scale allows A or B, so the approved A holds) | 2026-10-09 | Problem and user impact; a `subsystem: summary phrase` subject; `Fixes:` trailer; one change per patch; sign-off |
| L31 | Writing good CL descriptions | Google Engineering Practices | <https://google.github.io/eng-practices/review/developer/cl-descriptions.html> | B | 2026-10-09 (checked against the source Markdown) | Standalone summary line; problem, approach, shortcomings, background |
| L32 | Automatically generated release notes | GitHub Docs | <https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes> | B | 2026-10-09 (link check) | Notes built from merged pull requests, grouped by label |
| L33 | ADR process | AWS Prescriptive Guidance | <https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html> | B | 2026-10-03 | Context, decision, consequences; statuses; reviewers cite records |
| L34 | PEP 1 | Python | <https://peps.python.org/pep-0001/> | B | 2026-10-03 | Proposal sections and statuses; the deciders |
| L35 | RFC template | Rust project | <https://github.com/rust-lang/rfcs/blob/master/0000-template.md> | B | 2026-10-09 (file present) | Motivation, drawbacks, alternatives, unresolved questions |
| L36 | MADR 4.0.0 | ADR GitHub organisation | <https://adr.github.io/madr/> | B (one project's template) | 2026-10-09 | Decision record template with considered options required |
| L37 | Documenting Architecture Decisions (2011) | Cognitect blog | <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions> | C | 2026-10-03 | The original record: title, context, decision, status, consequences |
| L38 | How to Write a Git Commit Message | Practitioner blog | <https://cbea.ms/git-commit/> | C | 2026-10-03 | Seven subject and body rules |

### Trust, Security and Supply Chain

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L39 | SPDX license expressions 2.3.1; SPDX overview | SPDX (ISO/IEC 5962:2021) | <https://spdx.github.io/spdx-spec/v2.3.1/SPDX-license-expressions/>, <https://spdx.dev/about/overview/> | A | 2026-10-09 | Licence identifiers and expression grammar; 3.0.1 is the current line |
| L40 | REUSE Specification 3.3 | FSFE | <https://reuse.software/spec-3.3/> | A | 2026-10-09 | Licence and copyright on every file; `LICENSES/` folder; copyright notice format |
| L41 | Citation File Format 1.2.0 schema | CFF project | <https://raw.githubusercontent.com/citation-file-format/citation-file-format/main/schema.json> | A | 2026-10-09 | Four required CITATION.cff fields |
| L42 | SLSA v1.2 build requirements | OpenSSF | <https://slsa.dev/spec/v1.2/build-requirements> | A | 2026-10-09 | Build levels L1 to L3; provenance duties |
| L43 | Adding a security policy | GitHub Docs | <https://raw.githubusercontent.com/github/docs/main/content/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/add-security-policy.md> | B | 2026-10-09 (link check) | SECURITY.md minimum: supported versions and how to report |
| L44 | Privately reporting a security vulnerability | GitHub Docs | <https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability> | B | 2026-10-03 | A private reporting channel on the platform |
| L45 | Licensing a repository | GitHub Docs | <https://raw.githubusercontent.com/github/docs/main/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository.md> | B | 2026-10-09 (link check) | LICENSE detection and placement |
| L46 | About CITATION files | GitHub Docs | <https://raw.githubusercontent.com/github/docs/main/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files.md> | B | 2026-10-09 (link check) | CITATION.cff display on the repository page |
| L47 | Displaying a sponsor button | GitHub Docs | <https://raw.githubusercontent.com/github/docs/main/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository.md> | B | 2026-10-09 (link check) | FUNDING.yml keys |
| L48 | Exporting dependencies as an SBOM | GitHub Docs | <https://raw.githubusercontent.com/github/docs/main/content/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/export-dependencies-as-sbom.md> | B | 2026-10-09 (link check) | SBOM export from the dependency graph |
| L49 | Vulnerability disclosure guide for maintainers | OpenSSF | <https://github.com/ossf/oss-vulnerability-guide/blob/main/maintainer-guide.md> | B | 2026-10-09 (file present) | Contact, private handling, response and disclosure times |
| L50 | Scorecard checks | OpenSSF | <https://github.com/ossf/scorecard/blob/main/docs/checks.md> | B | 2026-10-09 | 20 automated checks and risk levels |
| L51 | OpenSSF Baseline v2026.08.28, with the Best Practices badge wording | OpenSSF | <https://baseline.openssf.org/versions/2026-08-28.html>, <https://raw.githubusercontent.com/coreinfrastructure/best-practices-badge/main/config/locales/en.yml> | B | 2026-10-09 (lexicon) | 41 controls and 65 requirements at three levels; the items on written documents in V17; a lexicon with meanings for user, contributor, maintainer, change, release and version identifier |
| L52 | 2026 Minimum Elements for a Software Bill of Materials, version 2.1 | CISA and partner agencies | <https://www.cisa.gov/resources-tools/resources/2026-minimum-elements-software-bill-materials-sbom> | B | 2026-10-08 | 17 data fields and 6 practices; replaces the 2025 draft and the 2021 NTIA minimum elements |
| L53 | About choosealicense | GitHub | <https://choosealicense.com/about/> | B | 2026-10-03 | A decision aid for picking a licence |
| L54 | Metrics list; Licenses Declared | CHAOSS (Linux Foundation) | <https://chaoss.community/kbtopic/all-metrics/> | B | 2026-10-03 | Health metric questions and their users |
| L55 | Security by documentation? Characterizing GitHub SECURITY.md policies and their adoption in Python libraries (Empirical Software Engineering 31(3), 2026) | Springer | <https://link.springer.com/article/10.1007/s10664-025-10794-z>; preprint <https://arxiv.org/abs/2502.07395>; dataset <https://github.com/sswpka/Characterizing-Security-Policy-Python-Libraries> | B (paper); C (preprint) | 2026-10-08 | Projects with a SECURITY.md show stronger practices (association). Dataset: 772 classified segments in 8 categories |
| L56 | Scorecard and security outcomes (arXiv 2210.14884) | Preprint | <https://arxiv.org/html/2210.14884v2> | C | 2026-10-03 | Scores explain 4% to 12% of the variance in vulnerabilities |
| L57 | Security practices across npm (arXiv 2504.14026) | Preprint | <https://arxiv.org/html/2504.14026> | C | 2026-10-03 | Security-Policy above 0 in 6.8% of 145,817 packages |
| L58 | SBOM readiness survey (2021) | Linux Foundation Research | <https://www.linuxfoundation.org/press/press-release/the-linux-foundation-releases-the-state-of-software-bill-of-materials-sbom-and-cybersecurity-readiness-research> | C | 2026-10-03 | 47% of 412 organisations used SBOMs |

### Forges Other Than GitHub

Each forge page sets the file names and paths the forge recognises; none sets file contents.

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L59 | Working with projects | GitLab Docs | <https://docs.gitlab.com/user/project/working_with_projects/> | B | 2026-10-09 | Optional overview items: README, licence, changelog, contributing guidelines; archiving makes a project read-only |
| L60 | Repository files | GitLab Docs | <https://docs.gitlab.com/user/project/repository/files/> | B | 2026-10-08 | README and index file names GitLab renders |
| L61 | Description templates | GitLab Docs | <https://docs.gitlab.com/user/project/description_templates/> | B | 2026-10-08 | `.gitlab/issue_templates/` and `.gitlab/merge_request_templates/` |
| L62 | Code owners | GitLab Docs | <https://docs.gitlab.com/user/project/codeowners/> | B | 2026-10-09 | `CODEOWNERS` in the root, `docs/` or `.gitlab/`; approval on protected branches |
| L63 | Changelogs | GitLab Docs | <https://docs.gitlab.com/user/project/changelogs/> | B | 2026-10-09 | Entries generated from a `Changelog` Git trailer |
| L64 | Web editor | GitLab Docs | <https://docs.gitlab.com/user/project/repository/web_editor/> | B | 2026-10-08 | File templates for LICENSE and CI files; none for README, CONTRIBUTING or CHANGELOG |
| L65 | AGENTS.md and Duo customization files | GitLab Docs | <https://docs.gitlab.com/user/duo_agent_platform/customize/agents_md/>, <https://docs.gitlab.com/user/duo_agent_platform/customize/>, <https://docs.gitlab.com/user/duo_agent_platform/customize/review_instructions/> | B | 2026-10-08 | AGENTS.md at user, root and sub-folder level, nearest first; review instructions are guidance |
| L66 | Issue and pull request templates | Gitea Docs | <https://docs.gitea.com/usage/issue-pull-request-templates> | B | 2026-10-08 | Template names and folders in the root, `.gitea/` or `.github/` |
| L67 | Code owners | Gitea Docs | <https://docs.gitea.com/usage/code-owners> | B | 2026-10-08 | `CODEOWNERS` in the root, `docs/` or `.gitea/` |
| L68 | Profile README; template repositories | Gitea Docs | <https://docs.gitea.com/usage/profile-readme>, <https://docs.gitea.com/usage/repository/template-repositories>, <https://docs.gitea.com/usage/repository> | B | 2026-10-08 | Profile README in a `.profile` repository; template variables |
| L69 | Issue and pull request templates | Forgejo Docs | <https://forgejo.org/docs/latest/user/issue-pull-request-templates/> | B | 2026-10-08 | Template folders `.forgejo`, `.gitea`, `.github`, `docs` |
| L70 | First repository; profile; pull requests and Git flow | Forgejo Docs | <https://forgejo.org/docs/latest/user/first-repository/>, <https://forgejo.org/docs/latest/user/profile/>, <https://forgejo.org/docs/latest/user/pull-requests-and-git-flow/>, <https://forgejo.org/docs/latest/user/> | B | 2026-10-09 | LICENSE and README at creation; `CODEOWNERS` in the root, `docs` or `.forgejo` |
| L71 | First repository; licensing | Codeberg Docs | <https://docs.codeberg.org/getting-started/first-repository/>, <https://docs.codeberg.org/getting-started/licensing/>, <https://docs.codeberg.org/> | B | 2026-10-08 | Licence text in a root file or a REUSE `LICENSES` folder; per-file headers recommended |
| L72 | README content | Bitbucket Cloud (Atlassian) | <https://support.atlassian.com/bitbucket-cloud/docs/readme-content/> | B | 2026-10-09 | README formats shown on the Source page |
| L73 | Set up and use code owners | Bitbucket Cloud (Atlassian) | <https://support.atlassian.com/bitbucket-cloud/docs/set-up-and-use-code-owners/> | B | 2026-10-09 | `.bitbucket/CODEOWNERS`; reviewer selection strategies |
| L74 | Pull request templates | Bitbucket Cloud (Atlassian) | <https://support.atlassian.com/bitbucket-cloud/kb/pull-request-templates-in-bitbucket-cloud/> | B | 2026-10-09 | One `.bitbucket/pull_request_template.md` |
| L75 | git.sr.ht and hg.sr.ht manuals | SourceHut | <https://man.sr.ht/git.sr.ht/>, <https://man.sr.ht/hg.sr.ht/> | B (smaller platform) | 2026-10-09 | README and licence file names, including REUSE-style `LICENSES/` |
| L76 | Pull request templates | Azure Repos (Microsoft Learn) | <https://learn.microsoft.com/en-us/azure/devops/repos/git/pull-request-templates?view=azure-devops> | B | 2026-10-09 | Default, branch-specific and additional templates; advisory only |
| L77 | Create a README | Azure Repos (Microsoft Learn) | <https://learn.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops> | B | 2026-10-09 | Three README audiences (users, developers, contributors) and README parts |
| L78 | Issue and pull request templates | Gitee Help | <https://help.gitee.com/issue/templates> | B | 2026-10-09 | `.gitee/ISSUE_TEMPLATE/`; lookup order across `.gitee`, `.github` and a namespace repository |
| L79 | CodeOwners | Gitee Help | <https://help.gitee.com/repository/extend/%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A8CodeOwners%E5%8A%9F%E8%83%BD/> | B | 2026-10-09 | `CODEOWNERS` in the root, `.gitee/` or `docs/`; the last matching rule wins |

### Outside Study and Sources Added at Stage 1

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L80 | What's Inside a GitHub Repository? (arXiv 2605.16701, v2) | Preprint; the authors state acceptance at ICSME 2026 | <https://arxiv.org/abs/2605.16701>, <https://arxiv.org/html/2605.16701v2> | C (preprint); B once the ICSME 2026 proceedings entry appears | 2026-10-09 | File presence in 10,000 repositories with 100+ stars; figures in [Skew](#skew), unchecked against the paper |
| L81 | Apache License 2.0 | Apache Software Foundation | <https://www.apache.org/licenses/LICENSE-2.0> | B | 2026-10-09 | Section 4(d): a NOTICE file holds attribution notices, and anyone who distributes a derivative work must include the notices |
| L82 | Developer Certificate of Origin 1.1 | Linux Foundation | <https://developercertificate.org/> | B | 2026-10-09 | The statement a contributor certifies with a Signed-off-by line |
| L83 | Generative AI policy | Linux Foundation | <https://www.linuxfoundation.org/legal/generative-ai> | B | 2026-10-09 | Contributors check the tool's terms, check AI output for third-party material, and give notice and attribution; projects may publish their own guidance |

### Sources Added at Stage 4

| # | Source | Publisher | URL | Grade | Read | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| L84 | Archiving repositories | GitHub Docs | <https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories> | B | 2026-10-09 | An archived repository is read-only: issues, pull requests, code, releases and comments. Maintainers close open issues and update the README before archiving |

## Community Pages

31 rows from 29 pages, all grade C and all read on 2026-10-08. Kinds: dispute 15, practice 7, practice and dispute 5, gap 2, practice and gap 1, not applicable 1. Findings are paraphrased from a model-written summary of each page.

| # | Topic | Finding | Kind | Source |
| --- | --- | --- | --- | --- |
| CM1 | readme | Commenters keep a statement of the project and its problem, install or build steps, usage examples, demos for UI projects, and text readable without rendering. Shortest agreed form: the project's purpose, its use, and ways to help | Practice | <https://news.ycombinator.com/item?id=36773022> |
| CM2 | readme | Disputed: images without text, Markdown-only rendering, and a contributors section. Tracking pixels in a README raise a privacy concern | Dispute | <https://news.ycombinator.com/item?id=36773022> |
| CM3 | readme | Users want a statement of project status (active, finished, maintenance-only or abandoned); maintainers dislike questions about a project being dead. Commenters propose a README status section. Evidence for a readme element, no new type | Practice and dispute | <https://news.ycombinator.com/item?id=38265884> |
| CM4 | commit-message | A subject plus a body with the reason; the code shows the change itself. Messages outlast tool migrations better than pull request threads or trackers. Readers use blame, log, bisect and revert | Practice | <https://news.ycombinator.com/item?id=32194538>, <https://news.ycombinator.com/item?id=43468637> |
| CM5 | commit-message | Disputed: whether anyone reads the log; formatting rules as wasted effort; whether the reason for a change belongs in the commit or the pull request description | Dispute | <https://news.ycombinator.com/item?id=36820938>, <https://news.ycombinator.com/item?id=32194538>, <https://news.ycombinator.com/item?id=43468637> |
| CM6 | commit-message (Conventional Commits) | Defended for tooling: version bumps, changelog grouping, release automation, scopes in monorepos. Criticised for forced categories, lost subject space and no gain in content. Alternatives: issue keys, Git trailers, kernel style | Dispute | <https://news.ycombinator.com/item?id=48414027> |
| CM7 | change-description | Descriptions keep the issue link, the rationale and design decisions, links to discussion, and screenshots. Squash-merging teams treat the description as the record and the squashed commit as a copy | Practice | <https://news.ycombinator.com/item?id=31173708>, <https://dev.to/erikmelone/pull-request-descriptions-should-not-be-optional-53n1> |
| CM8 | change-description | Disputed: history kept in the repository against the pull request page as the record; squash merges hide bisect-level history. One blog post favours a short description over an empty description | Dispute | <https://news.ycombinator.com/item?id=31173708>, <https://dev.to/erikmelone/pull-request-descriptions-should-not-be-optional-53n1> |
| CM9 | change-description | No page in the pass measured template use | Not applicable | None |
| CM10 | security-policy | A maintainer-facing article: most projects use the file only to point to the reporting procedure. Useful files add a threat model, a security boundary, and the line between a vulnerability and a hardening issue | Practice | <https://developers.redhat.com/articles/2024/02/06/security-policies-open-source-software> |
| CM11 | security-policy | A maintainer reports security intake overloaded by low-quality AI-generated reports, each costing hours of triage. Reporter-facing rules are contested | Dispute | <https://daniel.haxx.se/blog/2025/07/14/death-by-a-thousand-slops/> |
| CM12 | security-policy | No thread about the file itself surfaced; an index search returned only project announcements mentioning the file | Gap | Hacker News index search, 2026-10-08 |
| CM13 | contributing-guide, issue-report | Some maintainers let bots close issues filed without the template; other maintainers label each such issue and leave the issue open. Stale bots draw dislike. Reports need steps, expected and actual results, version and logs | Dispute | <https://news.ycombinator.com/item?id=25100810> |
| CM14 | ai-use-policy | Disclosure policies split commenters: supporters say disclosure changes the review; critics say only the contributor's understanding matters. The problems predate language models | Dispute | <https://news.ycombinator.com/item?id=46730504> |
| CM15 | agent-instructions | Keep content the code cannot show: build and test commands, conventions, reasons, past failures. Keep the file short, update the file after agent failures, nest files by folder | Practice | <https://news.ycombinator.com/item?id=47034087>, <https://news.ycombinator.com/item?id=44957443> |
| CM16 | agent-instructions | Disputed: duplication of README and CONTRIBUTING; generated files as useless or harmful; agents ignoring written rules, so teams enforce with hooks and checks. File paths, component names and workarounds go stale first | Dispute | <https://news.ycombinator.com/item?id=47034087>, <https://news.ycombinator.com/item?id=44957443> |
| CM17 | release-notes | A changelog file serves users and the commit history serves developers. Readers want to know whether a fix applies to their setup; breaking changes get their own place. Boilerplate entries draw complaints | Practice and dispute | <https://news.ycombinator.com/item?id=17631326>, <https://news.ycombinator.com/item?id=46590623> |
| CM18 | release-notes | Disputed: notes generated from commits or pull requests against notes written by hand for the consumer | Dispute | <https://news.ycombinator.com/item?id=46590623>, <https://news.ycombinator.com/item?id=17631326> |
| CM19 | release-procedure | Individuals keep written release checklists. Failures come from forgotten steps and tag typos. Teams automate step by step, starting from a script that prints each step and waits | Practice | <https://news.ycombinator.com/item?id=21244352> |
| CM20 | compatibility-policy, upgrade-guide | Disputed: whether semantic versions predict breakage. Agreed: a version number alone falls short, and changelogs or release notes stay necessary under any scheme | Practice and dispute | <https://news.ycombinator.com/item?id=13378637> |
| CM21 | decision-record | One article: decision records capture one point in time, yet teams expect the records to stay current, so the records go unread and stale. History and post-mortem context stay useful. The article recommends pairing records with build-breaking checks and revisit notes | Dispute | <https://www.javacodegeeks.com/2026/05/the-reason-most-architecture-decision-records-get-written-and-never-read-is-architectural-not-cultural.html> |
| CM22 | design-proposal | Teams use proposals for cross-team, hard-to-reverse or ambiguous changes. Disputed: uneven effort, months-long consensus, performative proposals, design documents out of date once finished. Teams blend proposal and decision-record formats | Practice and dispute | <https://news.ycombinator.com/item?id=46221016> |
| CM23 | documentation-set, architecture-overview | Docs go stale when kept apart from the repository and stay accurate when generated or tied to tests. Commenters credit organising docs by reader need, yet READMEs, home pages and index pages fit none of the four Diátaxis kinds | Practice and dispute | <https://news.ycombinator.com/item?id=40317113>, <https://news.ycombinator.com/item?id=42340740> |
| CM24 | code-of-conduct | Critics call the file unenforceable and open to misuse; supporters say the file sets expectations and grounds for removal. Short rule sets preferred | Dispute | <https://news.ycombinator.com/item?id=45423014> |
| CM25 | governance-document, maintainers-list | Infrastructure projects need written governance and succession plans; many maintainers reject governance demands from users. Hobby and infrastructure projects differ | Dispute | <https://news.ycombinator.com/item?id=45979232> |
| CM26 | code-owners, review-guide | A written review standard gets support. The thread skips ownership files, and no page on CODEOWNERS surfaced | Practice and gap | <https://news.ycombinator.com/item?id=20890682> |
| CM27 | bill-of-materials | Skeptics: few people read SBOMs, inaccurate SBOMs give false confidence, and SBOMs miss build-time attacks. Named uses: incident response and buyer leverage. The thread dates from 2021 | Dispute | <https://news.ycombinator.com/item?id=26529619> |
| CM28 | build-provenance | Disputed: attestations as optional today and mandatory later; a tilt toward one forge; trust in a platform differs from trust in a publisher | Dispute | <https://news.ycombinator.com/item?id=42147000> |
| CM29 | funding-file | One blog audit of 42 repositories: 12 repositories show a working button; the file alone shows no button without a separate setting; per-repository files went stale in 8 repositories | Practice | <https://kenimoto.dev/blog/funding-yml-sponsor-button-42-repo-audit/> |
| CM30 | citation-file | Disputed: another citation format beside BibTeX and CSL-JSON; lock-in to one platform; reference manager support | Dispute | <https://news.ycombinator.com/item?id=28246899> |
| CM31 | roadmap | Seen only through a search summary, never as a page; no finding recorded | Gap | None |

## Repository List

One row per repository, 146 rows, written by `corpus_counts.py --repo-list`. Stars are the counts at the freeze. An agent assigned each kind label, and no second reader checked the labels. Document files found: file names matching a 2026-10-03 pattern, at the root, in `.github/` or in `docs/`; a trailing slash marks a folder. Workflow folders, dependency-bot configuration, dev container folders and example folders stay out of the column.

| Repository | Archived | Stars at freeze | Primary language | Kind label | Document files found |
| --- | --- | --- | --- | --- | --- |
| AGWA/git-crypt | no | 9,944 | C++ | developer tool, library or framework | `AUTHORS`, `CONTRIBUTING.md`, `COPYING`, `doc/`, `NEWS.md`, `README.md` |
| aidenybai/react-scan | no | 21,868 | TypeScript | developer tool, library or framework | `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| altic-dev/FluidVoice | no | 11,965 | Swift | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| amacneil/dbmate | no | 7,444 | Go | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `LICENSE`, `README.md` |
| amoffat/sh | no | 7,245 | Python | developer tool, library or framework | `.github/FUNDING.yml`, `CHANGELOG.md`, `CODEOWNERS`, `docs/`, `LICENSE.txt`, `README.rst`, `SECURITY.md` |
| antvis/G6 | no | 12,323 | TypeScript | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `LICENSE`, `README.md`, `README.zh-CN.md`, `SECURITY.md` |
| apache/apisix | no | 17,206 | Lua | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md`, `THREAT_MODEL.md` |
| apache/devlake | no | 3,161 | Go | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `LICENSE`, `README.md` |
| apple/container | no | 50,587 | Swift | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `MAINTAINERS.txt`, `README.md` |
| argoproj/argo-workflows | no | 17,026 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `docs/architecture.md`, `docs/CONTRIBUTING.md`, `docs/deprecations.md`, `docs/README.md`, `docs/roadmap.md`, `docs/security.md`, `docs/upgrading.md`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `OWNERS`, `README.md`, `SECURITY.md` |
| AutoHotkey/AutoHotkey | no | 13,257 | C++ | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `license.txt`, `README.md` |
| Automattic/harper | no | 16,243 | Rust | end-user application | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| awesome-selfhosted/awesome-selfhosted | no | 324,739 | none | collection or theme | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `LICENSE`, `README.md` |
| backstage/backstage | no | 34,577 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/architecture.drawio`, `LICENSE`, `OWNERS.md`, `README.md`, `SECURITY.md` |
| blacksmithgu/obsidian-dataview | no | 9,383 | TypeScript | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `docs/`, `docs/docs/`, `LICENSE.txt`, `README.md` |
| bookorbit/bookorbit | no | 5,286 | TypeScript | end-user application | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `.github/SECURITY.md`, `AGENTS.md`, `CLAUDE.md`, `docs/`, `docs/CODE_OF_CONDUCT.md`, `docs/CONTRIBUTING.md`, `LICENSE`, `README.md` |
| BurntSushi/ripgrep | no | 68,937 | Rust | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `CONTRIBUTING.md`, `COPYING`, `README.md` |
| caronc/apprise | no | 17,551 | Python | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| casey/just | no | 36,170 | Rust | developer tool, library or framework | `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `README.中文.md` |
| cathrynlavery/diagram-design | no | 46,633 | HTML | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/adr/`, `LICENSE`, `README.md`, `SECURITY.md` |
| cjpais/Handy | no | 33,290 | Rust | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| ClickHouse/ClickHouse | no | 50,305 | C++ | operations software | `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `AUTHORS`, `CHANGELOG.md`, `CITATION.cff`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `docs/LICENSE`, `docs/README.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| cline/cline | no | 70,038 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| cloudnative-pg/cloudnative-pg | no | 9,420 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `docs/`, `docs/LICENSE`, `docs/README.md`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `README.md`, `ROADMAP.md`, `SECURITY.md`, `SUPPORT.md` |
| coollabsio/coolify | no | 62,747 | PHP | operations software | `.github/FUNDING.yaml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `DESIGN.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| CorentinTh/it-tools | no | 40,790 | Vue | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE/`, `CHANGELOG.md`, `LICENSE`, `README.md` |
| d2lang/d2 | no | 25,581 | Go | developer tool, library or framework | `.github/pull_request_template.md`, `CODE_OF_CONDUCT.md`, `docs/`, `docs/CONTRIBUTING.md`, `LICENSE.txt`, `README.md` |
| datamodel-code-generator/datamodel-code-generator | no | 4,032 | Python | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yaml`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `docs/`, `docs/architecture.md`, `docs/deprecations.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| deepseek-ai/DeepSeek-OCR | no | 23,926 | Python | research model release | `LICENSE`, `README.md` |
| deepseek-ai/DeepSeek-V3 | no | 104,509 | Python | research model release | `.github/ISSUE_TEMPLATE/`, `README.md` |
| deuxfleurs-org/garage | no | 4,662 | Rust | operations software | `CONTRIBUTING.md`, `doc/`, `GOVERNANCE.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| dmmulroy/anti-slop | no | 5,332 | TypeScript | developer tool, library or framework | `AGENTS.md`, `LICENSE`, `README.md` |
| docmost/docmost | no | 21,903 | TypeScript | end-user application | `LICENSE`, `README.md` |
| dograh-hq/dograh | no | 5,831 | Python | end-user application | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `docs/CLAUDE.md`, `docs/README.md`, `LICENSE`, `README.ja-JP.md`, `README.md`, `README.zh-CN.md`, `SECURITY.md` |
| dolthub/dolt | no | 24,603 | Go | operations software | `.github/FUNDING.yml`, `CODEOWNERS`, `LICENSE`, `README.md`, `SECURITY.md` |
| drumih/turbo-fieldfare | no | 6,872 | Swift | research model release | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| Egonex-AI/Understand-Anything | no | 85,691 | TypeScript | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| EnterpriseDB/barman | no | 3,258 | Python | operations software | `.github/CODEOWNERS`, `AUTHORS`, `docs/`, `docs/license/`, `docs/README.md`, `LICENSE`, `README.rst` |
| excalidraw/excalidraw | no | 133,518 | TypeScript | end-user application | `.github/copilot-instructions.md`, `.github/FUNDING.yml`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| ExistentialAudio/BlackHole | no | 19,888 | C | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `LICENSE`, `README.md` |
| exo-explore/exo | no | 47,791 | Python | end-user application | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| f/textream | no | 3,983 | Swift | end-user application | `.github/FUNDING.yml`, `docs/`, `docs/docs/`, `docs/support.html`, `LICENSE`, `README.md`, `SECURITY.md` |
| fastapi/fastapi | no | 102,886 | Python | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `CITATION.cff`, `docs/`, `LICENSE`, `README.md` |
| FlareSolverr/FlareSolverr | no | 15,809 | Python | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| frappe/books | yes | 4,998 | TypeScript | end-user application | `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `LICENSE`, `README.md` |
| gastownhall/beads | no | 27,749 | Go | developer tool, library or framework | `.github/CODEOWNERS`, `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `docs/architecture/`, `LICENSE`, `README.md`, `ROADMAP.md`, `SECURITY.md` |
| gastownhall/gastown | no | 18,311 | Go | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/design/`, `LICENSE`, `README.md`, `SECURITY.md` |
| ghostty-org/ghostty | no | 61,987 | Zig | developer tool, library or framework | `AGENTS.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| giscus/giscus | no | 12,144 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.ar.md`, `README.be.md`, `README.bg.md`, `README.ca.md`, `README.cs.md`, `README.da.md`, `README.de.md`, `README.eo.md`, `README.es.md`, `README.eu.md`, `README.fa.md`, `README.fr.md`, `README.gr.md`, `README.hbs.md`, `README.he.md`, `README.hu.md`, `README.id.md`, `README.it.md`, `README.ja.md`, `README.kh.md`, `README.ko.md`, `README.md`, `README.nl.md`, `README.pl.md`, `README.pt.md`, `README.ro.md`, `README.ru.md`, `README.th.md`, `README.tr.md`, `README.uk.md`, `README.uz.md`, `README.vi.md`, `README.zh-CN.md`, `README.zh-HK.md`, `README.zh-TW.md` |
| golang-migrate/migrate | no | 18,960 | Go | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `CONTRIBUTING.md`, `LICENSE`, `MIGRATIONS.md`, `README.md`, `SECURITY.md` |
| gotify/server | no | 16,040 | Go | operations software | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| grafana/alloy | no | 3,587 | Go | operations software | `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `docs/`, `docs/design/`, `docs/README.md`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `README.md` |
| Hammerspoon/hammerspoon | no | 16,245 | Objective-C | end-user application | `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CREDITS.md`, `LICENSE`, `README.md` |
| harbor-framework/harbor | no | 5,935 | Python | developer tool, library or framework | `AGENTS.md`, `CHANGELOG.md`, `CITATION.cff`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `docs/CLAUDE.md`, `docs/README.md`, `LICENSE`, `README.md`, `rfcs/` |
| hoppscotch/hoppscotch | no | 80,589 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| InvoicePlane/InvoicePlane | no | 3,152 | PHP | end-user application | `.github/CHANGELOG.md`, `.github/CONTRIBUTING.md`, `.github/copilot-instructions.md`, `.github/docs/`, `.github/ISSUE_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/security/`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `LICENSE.txt`, `README.md`, `SECURITY.md` |
| istio/istio | no | 38,427 | Go | operations software | `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `.github/SECURITY.md`, `architecture/`, `CODEOWNERS`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `security/`, `SUPPORT.md` |
| jamiepine/voicebox | no | 56,684 | Python | end-user application | `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/`, `docs/README.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| javascript-obfuscator/javascript-obfuscator | no | 16,289 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE.BSD`, `README.md` |
| jerrykuku/luci-theme-argon | no | 5,517 | Less | collection or theme | `.github/ISSUE_TEMPLATE/`, `LICENSE`, `README.md` |
| jonschlinkert/gray-matter | no | 4,491 | JavaScript | developer tool, library or framework | `CHANGELOG.md`, `LICENSE`, `README.md` |
| jqlang/jq | no | 35,765 | C | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `AUTHORS`, `ChangeLog`, `COPYING`, `docs/`, `docs/README.md`, `NEWS.md`, `README.md`, `SECURITY.md` |
| json-schema-faker/json-schema-faker | no | 3,450 | JavaScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CONTRIBUTING.md`, `LICENSE`, `MIGRATION.md`, `README.md` |
| juanfont/headscale | no | 44,457 | Go | operations software | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| junegunn/fzf | no | 83,459 | Go | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `doc/`, `LICENSE`, `README.md`, `SECURITY.md` |
| keras-team/keras | no | 64,355 | Python | developer tool, library or framework | `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, `CITATION.cff`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| kgateway-dev/kgateway | no | 5,701 | Go | operations software | `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CLAUDE.md`, `CODE-OF-CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `design/`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md`, `THREAT_MODEL.md` |
| kubernetes-sigs/external-dns | no | 9,109 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `code-of-conduct.md`, `CONTRIBUTING.md`, `docs/`, `docs/contributing/`, `docs/deprecation.md`, `docs/OWNERS`, `LICENSE.md`, `OWNERS`, `README.md` |
| kubernetes-sigs/gateway-api | no | 3,016 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `CHANGELOG/`, `code-of-conduct.md`, `CONTRIBUTING.md`, `LICENSE`, `OWNERS`, `README.md`, `site/` |
| kubernetes/ingress-nginx | yes | 19,454 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `Changelog.md`, `changelog/`, `code-of-conduct.md`, `CONTRIBUTING.md`, `docs/`, `docs/enhancements/`, `docs/OWNERS`, `LICENSE`, `OWNERS`, `README.md`, `SECURITY.md` |
| kyverno/kyverno | no | 8,231 | Go | operations software | `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `CONTRIBUTORS.md`, `docs/`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `OWNERS.md`, `README.md`, `ROADMAP.md`, `SECURITY.md` |
| langfuse/langfuse | no | 35,543 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`, `README.cn.md`, `README.ja.md`, `README.kr.md`, `README.md`, `SECURITY.md` |
| latitude-dev/latitude-llm | no | 4,716 | TypeScript | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `design.md`, `docs/`, `docs/security/`, `LICENSE`, `README.md`, `SECURITY.md` |
| leafac/kill-the-newsletter | no | 3,110 | TypeScript | end-user application | `.github/FUNDING.yml`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `LICENSE.md`, `README.md` |
| lint-staged/lint-staged | no | 14,743 | JavaScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `MIGRATION.md`, `README.md` |
| lysyi3m/macos-terminal-themes | no | 6,546 | Swift | collection or theme | `CONTRIBUTING.md`, `README.md` |
| makeplane/plane | no | 60,557 | TypeScript | end-user application | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `docs/`, `LICENSE.txt`, `README.md`, `SECURITY.md` |
| mermaid-js/mermaid | no | 90,586 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CHANGELOG.md`, `CITATION.cff`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/news/`, `LICENSE`, `README.md`, `README.zh-CN.md` |
| microsoft/fara | no | 6,216 | Python | research model release | `CODE_OF_CONDUCT.md`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| mikefarah/yq | no | 16,068 | Go | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| minio/minio | yes | 61,335 | Go | operations software | `.github/ISSUE_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `code_of_conduct.md`, `CONTRIBUTING.md`, `CREDITS`, `docs/`, `docs/LICENSE`, `docs/security/`, `LICENSE`, `README.md`, `SECURITY.md` |
| mountain-loop/yaak | no | 19,303 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| mysticaltech/terraform-hcloud-kube-hetzner | no | 3,937 | HCL | operations software | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/`, `docs/upgrades.md`, `LICENSE`, `MIGRATION.md`, `README.md`, `SECURITY.md` |
| n8n-io/n8n | no | 206,748 | TypeScript | end-user application | `.github/CLAUDE.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/adr/`, `LICENSE.md`, `OWNERS`, `README.md`, `SECURITY.md`, `security/` |
| newren/git-filter-repo | no | 13,370 | Python | developer tool, library or framework | `COPYING`, `COPYING.gpl`, `COPYING.mit`, `Documentation/`, `README.md` |
| NousResearch/hermes-agent | no | 252,078 | Python | end-user application | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CONTRIBUTING.es.md`, `CONTRIBUTING.md`, `contributors/`, `LICENSE`, `README.es.md`, `README.md`, `README.ur-pk.md`, `README.zh-CN.md`, `SECURITY.es.md`, `SECURITY.md`, `website/` |
| OAI/OpenAPI-Specification | no | 31,236 | Markdown | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `proposals/`, `README.md` |
| oauth2-proxy/oauth2-proxy | no | 15,070 | Go | operations software | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/docs/`, `docs/README.md`, `LICENSE`, `MAINTAINERS`, `MAINTAINERS.md`, `OWNERS`, `README.md`, `SECURITY.md` |
| obsidian-tasks-group/obsidian-tasks | no | 4,046 | TypeScript | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `contributing/`, `docs/`, `docs/migration.md`, `docs/README.md`, `LICENSE`, `README.md` |
| odysseus-dev/odysseus | no | 92,220 | Python | end-user application | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md`, `ROADMAP.md`, `SECURITY.md`, `THREAT_MODEL.md`, `website/` |
| openai/evals | no | 19,579 | Python | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/`, `LICENSE.md`, `README.md`, `SECURITY.md` |
| OpenAPITools/openapi-generator | no | 26,779 | Java | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/contributing.md`, `docs/roadmap.adoc`, `docs/roadmap.md`, `LICENSE`, `README.md`, `website/` |
| opencost/opencost | no | 6,769 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/README.md`, `docs/ROADMAP.md`, `GOVERNANCE.md`, `LICENSE`, `MAINTAINERS.md`, `README.md`, `ROADMAP.md`, `SECURITY.md` |
| outline/outline | no | 40,847 | TypeScript | end-user application | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `docs/`, `docs/ARCHITECTURE.md`, `docs/CODE_OF_CONDUCT.md`, `docs/SECURITY.md`, `LICENSE`, `README.md` |
| oxc-project/oxc | no | 22,979 | Rust | developer tool, library or framework | `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `.github/copilot-instructions.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/SECURITY.md`, `AGENTS.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| passteque/gluetun | no | 15,739 | Go | operations software | `.github/CODEOWNERS`, `.github/CONTRIBUTING.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `doc/`, `LICENSE`, `README.md` |
| pdm-project/pdm | no | 8,664 | Python | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `news/`, `README.md`, `SECURITY.md` |
| pgvector/pgvector | no | 23,281 | C | operations software | `CHANGELOG.md`, `LICENSE`, `README.md` |
| phuryn/pm-skills | no | 26,844 | none | collection or theme | `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| pi-hole/pi-hole | no | 61,211 | Shell | operations software | `.github/CODEOWNERS`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| pnpm/pnpm | no | 36,763 | Rust | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| pocket-id/pocket-id | no | 9,467 | Go | operations software | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| PostHog/posthog | no | 40,197 | Python | end-user application | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/owners.yaml`, `.github/pull_request_template.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `docs/README.md`, `LICENSE`, `owners.yaml`, `README.md` |
| pre-commit/pre-commit-hooks | no | 6,709 | Python | developer tool, library or framework | `CHANGELOG.md`, `LICENSE`, `README.md` |
| prometheus-community/helm-charts | no | 6,216 | Mustache | operations software | `.github/CODEOWNERS`, `.github/copilot-instructions.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `changelog/`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `MAINTAINERS.md`, `README.md`, `SECURITY.md` |
| prometheus-operator/kube-prometheus | no | 7,742 | Jsonnet | operations software | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `code-of-conduct.md`, `CONTRIBUTING.md`, `docs/`, `docs/security.md`, `LICENSE`, `README.md` |
| prometheus-operator/prometheus-operator | no | 9,988 | Go | operations software | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `code-of-conduct.md`, `CONTRIBUTING.md`, `Documentation/`, `governance.md`, `LICENSE`, `MAINTAINERS.md`, `README.md`, `SECURITY.md` |
| prometheus/prometheus | no | 66,432 | Go | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, `CONTRIBUTING.md`, `docs/`, `docs/migration.md`, `docs/stability.md`, `documentation/`, `LICENSE`, `MAINTAINERS.md`, `README.md`, `SECURITY.md` |
| pypa/pipx | no | 12,979 | Python | developer tool, library or framework | `.github/CONTRIBUTING.md`, `.github/FUNDING.yaml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/SECURITY.md`, `changelog.d/`, `docs/`, `docs/changelog.rst`, `docs/contributing.rst`, `docs/README.md`, `LICENSE` |
| qdrant/fastembed | no | 3,240 | Python | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| qdrant/qdrant | no | 34,982 | Rust | operations software | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/`, `docs/CODE_OF_CONDUCT.md`, `docs/CONTRIBUTING.md`, `docs/roadmap/`, `LICENSE`, `README.md` |
| rabbitmq/rabbitmq-server | no | 13,911 | JavaScript | operations software | `.github/ISSUE_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/SECURITY.md`, `AGENTS.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| Ranchero-Software/NetNewsWire | no | 10,456 | Swift | end-user application | `.github/CODEOWNERS`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| remarkjs/react-markdown | no | 15,907 | JavaScript | developer tool, library or framework | `changelog.md`, `license`, `readme.md` |
| renovatebot/renovate | no | 22,711 | TypeScript | developer tool, library or framework | `.github/contributing.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `docs/`, `license`, `readme.md`, `SECURITY.md` |
| RooCodeInc/Roo-Code | yes | 24,285 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `CHANGELOG.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| router-for-me/CLIProxyAPI | no | 54,542 | Go | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `CLAUDE.md`, `docs/`, `LICENSE`, `README.md` |
| rubenv/sql-migrate | no | 3,415 | Go | developer tool, library or framework | `LICENSE`, `README.md` |
| shikijs/shiki | no | 13,854 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| siderolabs/talos | no | 11,330 | Go | operations software | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md`, `website/` |
| sindresorhus/pure | no | 14,438 | Shell | developer tool, library or framework | `.github/issue_template.md`, `license`, `readme.md` |
| speaches-ai/speaches | no | 3,706 | Python | developer tool, library or framework | `CLAUDE.md`, `contributing.md`, `docs/`, `LICENSE`, `README.md` |
| spf13/cobra | no | 44,701 | Go | developer tool, library or framework | `CONTRIBUTING.md`, `doc/`, `LICENSE.txt`, `MAINTAINERS`, `README.md`, `SECURITY.md`, `site/` |
| starship/starship | no | 60,189 | Rust | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/README.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| stoplightio/prism | no | 5,051 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/pull_request_template.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `LICENSE`, `README.md` |
| strapi/strapi | no | 73,292 | TypeScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `architecture/`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `docs/CLAUDE.md`, `docs/docs/`, `docs/README.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| swagger-api/swagger-editor | no | 9,471 | JavaScript | developer tool, library or framework | `CHANGELOG.md`, `CLAUDE.md`, `docs/`, `docs/architecture.md`, `docs/migration.md`, `README.md` |
| tailwindlabs/tailwindcss-typography | no | 6,476 | JavaScript | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `CHANGELOG.md`, `LICENSE`, `README.md` |
| TanStack/router | no | 15,160 | TypeScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `LICENSE`, `README.md` |
| timescale/pgvectorscale | no | 3,137 | Rust | operations software | `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| tmux/tmux | no | 49,848 | C | developer tool, library or framework | `.github/CONTRIBUTING.md`, `.github/copilot-instructions.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/README.md`, `CHANGES`, `COPYING`, `README`, `SECURITY.md` |
| trycua/cua | no | 29,069 | Rust | developer tool, library or framework | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `changelog/`, `CITATION.cff`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `docs/README.md`, `LICENSE.md`, `MAINTAINERS.md`, `README.md`, `rfcs/`, `SECURITY.md` |
| TryGhost/Ghost | no | 55,501 | TypeScript | end-user application | `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `.github/CONTRIBUTING.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/SUPPORT.md`, `AGENTS.md`, `docs/`, `docs/contributing/`, `docs/README.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| tt-a1i/archify | no | 80,312 | JavaScript | developer tool, library or framework | `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `DESIGN.md`, `docs/`, `LICENSE`, `README.md`, `ROADMAP.md`, `SECURITY.md`, `website/` |
| tw93/Mole | no | 69,690 | Shell | end-user application | `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `CONTRIBUTORS.svg`, `docs/`, `LICENSE`, `README.md`, `SECURITY.md` |
| twentyhq/twenty | no | 58,108 | TypeScript | end-user application | `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `.github/SECURITY.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md` |
| twpayne/chezmoi | no | 21,865 | Go | developer tool, library or framework | `.github/CODE_OF_CONDUCT.md`, `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/SECURITY.md`, `LICENSE`, `README.md` |
| typicode/husky | no | 35,346 | JavaScript | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/README.md`, `docs/`, `LICENSE`, `README.md` |
| unclecode/crawl4ai | no | 85,039 | Python | developer tool, library or framework | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CONTRIBUTORS.md`, `docs/`, `docs/security/`, `LICENSE`, `README.md`, `ROADMAP.md`, `SECURITY.md` |
| vale-cli/vale | no | 6,217 | Go | developer tool, library or framework | `.github/CODE_OF_CONDUCT.md`, `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `LICENSE`, `README.md`, `SECURITY.md` |
| virattt/ai-hedge-fund | no | 63,909 | Python | end-user application | `.github/ISSUE_TEMPLATE/`, `LICENSE`, `README.md`, `ROADMAP.md` |
| vitest-dev/vitest | no | 17,191 | TypeScript | developer tool, library or framework | `.github/copilot-instructions.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `docs/`, `docs/AGENTS.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| VoltAgent/awesome-design-md | no | 119,937 | none | collection or theme | `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/`, `CONTRIBUTING.md`, `LICENSE`, `README.md` |
| withastro/astro | no | 63,124 | TypeScript | developer tool, library or framework | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md` |
| zsh-users/zsh-syntax-highlighting | no | 23,024 | Shell | developer tool, library or framework | `changelog.md`, `COPYING.md`, `docs/`, `README.md` |
| zsviczian/obsidian-excalidraw-plugin | no | 7,696 | TypeScript | end-user application | `.github/ISSUE_TEMPLATE/`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`, `docs/readme.md`, `LICENSE`, `README.md` |
