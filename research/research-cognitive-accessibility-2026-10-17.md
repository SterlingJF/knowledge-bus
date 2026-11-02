# Cognitive Accessibility Research

Corpus frozen: 2026-10-17 (America/Toronto)

## Purpose

This document holds the evidence behind the cognitive-accessibility universe spec, a factor-only universe spec for presenting a document to a reader. The owner defines cognitive accessibility as "barriers and design choices affecting people's ability to use information". Stage S1 covers the corpus, the method, the counts, the grades, the leads and the sources. Each later stage adds a section: S2 the header and the factors, S3 the guidance, S4 the grades and the fixes, S5 the wiring and the docs.

The owner refined the scope in earlier conversations, drawing on the preliminary research of 2026-10-03. Neither the conversations nor the research counts as a source here: every lead below comes from evidence captured on 2026-10-17.

Readers:

- A person adopting the preset beside their own universe spec checks each factor lead's question, values, grade, `set_by` evidence and refusals.
- An agent adapting a document for a reader takes advice from the guidance file once S3 writes the file. This document lists a grade for every source the advice can cite.
- A maintainer evolving the preset finds the counts, the graded sources, the refusals with reasons and the situation candidates per value.
- A fork reruns every count with `tools/research/accessibility_counts.py` and `tools/research/accessibility_leads.py`, from the fixtures dated 2026-10-17.

## Corpus

Corpus rule: "Corpus A: pairs of one public original document and a published edition of the same document adapted for a different reader, listed by the index sources named in these rules. Corpus B: reading options that the named products document on their makers' own help pages. Both as captured on 2026-10-17 (America/Toronto)."

- Freeze: 2026-10-17, America/Toronto (UTC−4). The capture window runs from 2026-10-17T04:00:00Z to 2026-10-18T03:59:59Z. 2,736 of 2,736 capture records fall inside the window, from 2026-10-17T22:23:46Z to 2026-10-18T01:01:36Z. Dates in the tables are UTC, so a read dated 2026-10-18 before 04:00 UTC falls on the freeze day.
- Corpus A holds four lists of original-and-adaptation pairs, counted apart: Easy Read editions, plain-language summaries, bottom-line-up-front summaries and layered notices. Readers confirmed 45 pairs by reading. Two lists hold fewer than 10 pairs and are short.
- Corpus B holds 165 reading options from 16 products of 5 makers, each read on the maker's own help page. Readers read and excluded 26 more options.
- Situation candidates: 106 cases from 85 public sources, each kept because its source states the reader's need or condition. The source of each case stays private.
- Literature: 136 graded source rows from two reading passes and the Corpus B usage search.

## Rerunning the Counts

The offline tools in `tools/research/` reproduce the seeded draws and recount the frozen coding metadata. Each command lists its options with `--help`. No page text is stored in the fixtures.

| Script | Repeats |
| --- | --- |
| `corpus_sample.py --adaptations` | Sorts each index source's candidates by URL, shuffles with seed 20261017 and draws confirmed pairs round-robin across sources, keeping the skip log and second-reader subsample |
| `accessibility_counts.py` | Counts Corpus A per list, Corpus B per category and dimension, situations per code, value, tag, grade, source type and change scale, and graded source rows |
| `accessibility_leads.py` | Computes value and factor grades from those counts and the recorded reader evidence labels |

Settings: seed 20261017; target 20 confirmed pairs per list; at most 5 pairs per publishing organisation; fewer than 10 confirmed pairs makes a list short; second-reader subsample 5 pairs per list. The four draws contain 19, 15, 5 and 6 pairs. The counts reproduce 45 confirmed pairs, 165 included and 26 excluded options, 106 situation candidates from 85 sources, and 136 graded source rows, along with the detailed tables below.

Run from the repository root using the existing development environment. `OUT` stays under `tools/research/`:

```sh
export PYTHONDONTWRITEBYTECODE=1
R=tools/research
F=$R/fixtures
OUT=$R/recount-2026-10-17
mkdir -p "$OUT"
uv run --locked python "$R/corpus_sample.py" \
  --adaptations "$F/adaptations-2026-10-17.jsonl" \
  --labels "$F/labels-2026-10-17.json" --seed 20261017 \
  --out "$OUT/draws.json"
uv run --locked python "$R/accessibility_counts.py" \
  --fixtures "$F" --out "$OUT"
uv run --locked python "$R/accessibility_leads.py" \
  --counts "$OUT/counts.json" --fixtures "$F" --out "$OUT"
uv run --locked pytest -q -p no:cacheprovider tools/research
```

Compare `OUT/draws.json` with `F/draws-2026-10-17.json`. The counting commands write `counts.json`, `leads.json` and TSV tables. Tests check the published tables, every frozen nested count and grade, all four draws, and the sampling and grading boundaries.

Flat fixtures in `tools/research/fixtures/`, each dated `2026-10-17`:

- `adaptations-2026-10-17.jsonl`: the four frozen candidate lists merged into one file; each row names its list and index source.
- `labels-2026-10-17.json`: eligibility labels keyed by list, including skip reasons and whether a candidate was read or screened by pattern.
- `draws-2026-10-17.json`: the four recorded draws, keyed by list, with picks, skips and second-reader subsamples.
- `pairs-2026-10-17.tsv` and `policies-2026-10-17.tsv`: coded pair and publisher-policy metadata, with quoted evidence removed.
- `options-2026-10-17.tsv`: coded reading options with each help page's URL, SHA-256 hash and capture time; quoted evidence removed.
- `situations-2026-10-17.tsv`: de-identified codes, tags, grades, source types, opaque source groups and change scales; no source text or paraphrases.
- `sources-2026-10-17.json`: grade and read-scope metadata from the two literature passes and the usage search, kept apart by source table.
- `leads-2026-10-17.json`: the reader's value and factor evidence labels.
- `maintainer-counts-2026-10-17.json`: recorded capture totals and the W3C COGA pattern-file count, taken from the maintainers' raw captures.

Rerun limits:

- A fork can repeat the seeded draws, recount the coded metadata and recompute the lead grades offline. This repeats the recorded coding; it does not independently confirm a reader's judgement.
- Pages captured on 2026-10-17 may have changed since. A fork can fetch the listed URLs with its own tools and repeat the reading, but cannot recreate the freeze by fetching today's pages. The frozen index membership cannot be rebuilt or checked against the original pages from these metadata fixtures alone.
- The capture totals (2,736 records, 2,728 distinct URLs, 2,661 readable URLs, 67 unreadable URLs, 32 bot-check pages and 20 fetches without a body) and COGA file counts (59 included, 22 captured, 37 never captured) are recorded figures. A fork can read them but cannot recompute them from these fixtures.
- The situation sources stay private. A fork can recount their de-identified metadata but cannot recheck their wording against a capture.
- Several hosts refused capture on 2026-10-17 ([Sources Refused or Unreadable](#sources-refused-or-unreadable)); a fork may meet the same checks.
- The maintainers keep the raw captures, made on 2026-10-17 and 2026-10-18 UTC, outside the repository.

## Method and Limits

### Capture

- Every page, PDF and API record that this document counts, grades or cites was captured as raw bytes plus extracted text, with its URL, final URL, HTTP status, UTC capture time and SHA-256 hash. Readers worked from the captured text only. A summarising fetch tool helped find pages, and its summaries never counted as a read.
- The captures cover 2,728 distinct URLs. For 2,661 URLs, the latest capture answered with a 2xx status and no bot check. 67 URLs stayed unreadable, 32 of them bot-check pages, and 20 fetches returned no body.
- A capture with an HTTP error status, or a bot-check page served under HTTP 200, counts as unreadable. Readers record each unreadable source with the date and the reason and never work around the check.
- The W3C site refused capture on 2026-10-17, so readers read W3C texts from the working groups' editor's drafts on w3c.github.io and drafts.csswg.org. Each row names the editor's draft.
- Readers read some papers from copies on author sites, university course pages or other hosts when the publisher refused capture. The graded-source tables name the copy read.

### Coding Rule (a): Stated Audience or Reason to a Need or Condition

1. A reader copies, with its location, every sentence from the publication page, the adaptation and the original's front matter that names the audience the adaptation serves or the reason the adaptation exists.
2. With no such sentence, the reader codes `none stated`. The format alone never supplies a reason.
3. A sentence describing the edition (a word list, a shorter version, a link to the full version) names neither an audience nor a reason. The reader labels the sentence a feature, and its code counts as a need the edition serves, beside the presentation changes, never as a stated need.
4. The reader codes an audience named by diagnosis or by group to the need the same publication states. With no need stated, the reader codes `audience named, no need stated` and keeps the audience name in the verbatim column only.
5. A level ("reading age 9") stays in the verbatim column, and the code names the need the level serves.
6. When no code fits, the reader adds a code with its evidence and the date and rechecks earlier rows.

Each code names a need or a condition in plain words, never a diagnosis and never a level. The list holds 17 needs and 10 conditions.

| Code | Need | Sources stating the need |
| --- | --- | --- |
| N1 everyday-wording | Everyday words and short sentences, with any unusual word explained | GOV.UK accessible communication formats; W3C COGA; WCAG Understanding 3.1.5 |
| N2 key-points-first | The key points first, with the full detail kept and reachable | ICO privacy-information guidance (GB8.methods); GOV.UK accessible communication formats |
| N3 short-version | A shorter version holding only the essential points | GOV.UK accessible communication formats; W3C COGA |
| N4 full-detail | The full detail up front, never only a summary | GOV.UK accessible communication formats |
| N5 pictures-with-words | Pictures beside the words that carry the same meaning | GOV.UK accessible communication formats; W3C COGA |
| N6 listen | The content as sound, to listen to instead of read | GOV.UK accessible communication formats; WCAG Understanding 3.1.5 |
| N7 small-chunks | Content in small chunks with clear space between | W3C COGA; ICO privacy-information guidance (GB8.draft) |
| N8 meaning-stated | Meaning stated outright, with nothing left implied | W3C COGA |
| N9 few-distractions | Few distractions, or a way to turn distractions off | W3C COGA |
| N10 familiar-layout | A familiar, consistent layout | W3C COGA |
| N11 choose-a-version | A way to find and pick the version or format that suits the reader | W3C COGA; Corpus A policy rows P-A1-01 and P-A1-03 |
| N12 context-for-outsiders | The subject put in context for a reader outside the field | eLife digests page (GB9); WCAG Understanding 3.1.5 |
| N13 go-over-later | A copy to go over again later, when the reader can take the content in | Kessels 2003 |
| N14 numbers-with-words | Numbers given with everyday words beside each figure | W3C COGA; Inclusion Europe |
| N15 numbers-over-text | Figures or a table in place of long text | W3C COGA |
| N16 find-the-part | A way to find and read only the parts that matter to the reader | Corpus A pairs A1-07 and A1-18 |
| N17 less-motion | Less movement on the page, or a way to stop the movement | WCAG Understanding 2.3.3; W3C COGA; Media Queries Level 5 |

| Code | Condition | Sources stating the condition |
| --- | --- | --- |
| C1 second-language | Reads the document's language as a second language | GOV.UK accessible communication formats |
| C2 slow-channel | Takes in long material slowly or tiringly in the channel the reader uses | GOV.UK accessible communication formats |
| C3 outside-the-field | Comes from outside the field the original was written for | Corpus A policy row P-A2-01 (Cochrane); WCAG Understanding 3.1.5 |
| C4 limited-space | Reads on a small screen or in limited space | ICO privacy-information guidance (GB8.methods) |
| C5 reads-short-only | Reads only a short version unless a point matters to the reader | ICO privacy-information guidance (GB8.draft) |
| C6 reads-with-a-helper | Reads with someone who talks the document through | GOV.UK accessible communication formats |
| C7 worn-out | Mentally tired, or recovering from mental fatigue | W3C COGA |
| C8 loses-track | Gets interrupted or loses track partway through | W3C COGA |
| C9 under-stress | Reads while stressed, anxious or pressed for time | GOV.UK content design; CDC crisis communication manual; W3C COGA |
| C10 attention-split | Reads on the move, or while attending to something else | W3C COGA; Oulasvirta et al. 2005 |

Readers added N13 to N16, C9 and C10 on 2026-10-17 and rechecked every earlier Corpus A row against the new codes. The review pass on 2026-10-17 added N17, because N9 held motion beside other distractions, and moved 5 motion options and one situation candidate from N9 to N17; no Corpus A row carries N9. The same pass applied step 3 to every pair and moved each code from a feature sentence out of the stated codes. Three formats sit outside the cognitive focus and stay recorded for S2: larger print, touch reading (braille, Moon) and sign language. GOV.UK lists these formats beside the cognitive ones.

### Coding Rule (b): Unit Covered to `set_by` Level

`set_by` names the knowledge-base level for setting a factor's value: `universe` once per universe spec, `scope` per folder, `instance` per document. The consumer values the factor. `set_by` leaves aside the person or tool that supplies a value at use time.

| Unit the adaptation covers | Example | `set_by` level |
| --- | --- | --- |
| One document | An Easy Read edition of one leaflet | `instance` |
| A series, a section or a site | One summary edition for each paper in a series | `scope` |
| Everything under one definition | A rule requiring a lay summary for every document of one kind | `universe` |

- A reader records the unit from the pair, with the words that show the reach. A reader records a publisher policy that sets an adaptation for more than one document as one policy row. Pair rows and policy rows count apart.
- Every Corpus A pair covers one document, because the eligibility rule requires one identifiable original. Pair rows therefore map to `instance` by construction and cannot tell the levels apart. Policy rows, and sources that say where a value is set, can tell the levels apart.
- A value that differs from one document to the next for the same reader is evidence for `instance`.
- A value that changes within one reading or between readings fits none of the three levels. Readers recorded such evidence for the candidate protocol item on values that change from moment to moment, never as a `set_by` level. A setting that readers can change, with no reader observed changing the value, counts as a capability only.

### Counting Rule

A count is cited only after a sample of the matched items has been read. Each count names its denominator and its method:

- **Confirmed by reading:** items a person or an agent read in the captured text and confirmed against the list's rule.
- **By pattern:** items matched by an index query, a title rule or a keyword rule.

Counts stay per list for Corpus A, per product category for Corpus B and per value for situation candidates. No table pools across lists. Every Corpus A pair, every Corpus B option and every situation candidate in this document is confirmed by reading. The index sources give candidate totals by pattern. In list A4, readers screened 758 of the 794 GOV.UK privacy notices by headings or keyword hits, a count by pattern, and read 36 in full.

### Sampling

1. Capture every index result page inside the freeze window.
2. Parse the candidates that match the list's pattern into a list file, one JSON line per candidate.
3. For each index source, sort the candidates by URL, then shuffle them with `random.Random(20261017)`.
4. Read the candidates in that order. A reader skips an ineligible candidate and logs the reason.
5. Draw one confirmed pair per index source per turn, up to 20 confirmed pairs per list, with at most 5 pairs per publishing organisation.
6. A list below 10 confirmed pairs is short, and its counts support a lead grade of Medium at most.

### Second Reader

The rules call for a second reader to code a seeded subsample of 5 pairs per list without seeing the first reader's codes. The subsample is drawn with seed 20261017, and no second reader has coded the subsample yet. Agreement per list stays unmeasured, so each coded-need count in Corpus A rests on one reader.

### Grades

Sources:

- **A:** a standards body: W3C Recommendations and Group Notes, ISO, IETF, CEN and national standards bodies.
- **B:** platform documentation from the platform's maker; government and organisational guides; peer-reviewed studies, meta-analyses and systematic reviews.
- **C:** essays, blog posts, talks, preprints, vendor marketing, practitioner pages, community pages and lived-experience pages.

Rules:

- A claim rests on its strongest source. A claim backed only by grade C sources stays a lead, and a grade C source never forms the only basis.
- A body that publishes standards under its own name without a formal standards process gets grade B.
- A sold standard (ISO 24495-1, ISO 9241-112, ISO 9241-11) is graded on its public preview and capped at B.
- A W3C Working Draft gets grade B, so Media Queries Level 5, the draft defining `prefers-reduced-motion`, gets grade B.
- A W3C editor's draft keeps the grade of the published Recommendation or Group Note it tracks, because the published version exists and refused capture. The capture rule's check of the draft text against the published text could not run, so each claim from an editor's draft rests on the draft text alone.
- A number taken from an abstract alone carries "abstract only".
- Each row shows the study design beside the grade, so a meta-analysis and a single experiment never read as equal.

### Lead Grades

Three kinds of evidence count: literature (graded sources), corpus (Corpus A pairs and Corpus B options, confirmed by reading) and situations (candidates whose source states the need or condition).

Factor leads:

| Grade | Evidence needed |
| --- | --- |
| High | All four: (1) an A or B source shows that the presentation suited to one value fails or costs readers with another value; (2) at least 10 pairs confirmed by reading in one Corpus A list, from at least 3 publishers, whose own coded needs fall under two or more of the factor's values or conditions, or, for values set at use time, Corpus B options from at least 3 makers; (3) every proposed value graded Medium or higher; (4) no other lead adjusts the same presentation dimension for the same reason |
| Medium | Condition (1) without condition (2), condition (2) without condition (1), or both with condition (3) or (4) failing |
| Low | Thin support. A source showing a gain for every reader caps a lead without condition (1) at Low, because the gain supports advice for every reader rather than a factor |
| Excluded | The lead is popular but unsupported or contradicted, or its values would assess or label a reader's cognition, name a diagnosis or name a level. The row states the reason |

Some factor questions have a default answer: the answer for the reader the original edition was written for. Such a factor proposes the default answer as a default value, and condition (3) checks the default value with the other values. Neither corpus can show a default value, because both hold only editions and options made for a reader with a need, so a default value grades on literature alone.

Value leads:

| Grade | Evidence needed |
| --- | --- |
| High | All three: an A or B source names the need or condition and the presentation it calls for; in one Corpus A list, at least 5 confirmed pairs from at least 2 publishers state or serve the need, or at least 5 Corpus B options from at least 2 makers serve the need; at least 4 situation candidates whose source states the need or condition |
| Medium | Two of the three kinds of evidence |
| Low | One of the three kinds of evidence, or none |
| Excluded | The value names a diagnosis, a level or a learning style, or graded evidence contradicts the value |

A value whose corpus condition holds only through a short list grades Medium at most.

A pair states a need in its own text or through its publisher's policy row. A pair serves a need through a presentation change:

| Presentation change | Need served |
| --- | --- |
| Wording level | N1 everyday-wording |
| Length | N3 short-version |
| Summary first | N2 key-points-first |
| Images beside text | N5 pictures-with-words |
| Chunking | N7 small-chunks |
| Audio | N6 listen |
| Order | No single need |
| A feature sentence (coding rule (a), step 3) | The need its code names |

`leads.py` computes the corpus and situation conditions from the counts. The literature condition, the overlap test and each exclusion come from a reader's labels, with the evidence named in each label.

### Refusal Wording

Each refusal is worded no more strongly than its sources. The result word comes from this ladder:

| Result | Use when |
| --- | --- |
| contradicted | A study designed to test the claim found no effect or the opposite. The row names the study and its design |
| unsupported | No adequate test was found or reported. The row names the test the claim lacks |
| contested | Graded sources disagree. The row names both sides |
| out of scope | The claim falls outside the subjects the preset covers. The row names scope, not evidence, as the reason |

Words stronger than the ladder ("refuted", "debunked", "myth") appear only when a captured A or B source uses that strength for the same claim. A meta-analysis with a small pooled effect and wide disagreement between studies caps the wording at "unsupported" or "contested".

### Limits

- Every Easy Read pair in Corpus A comes from a UK or Scottish government publisher, and every A3 pair comes from one publisher.
- eLife article pages answered with bot checks, so readers read each original through the eLife API article record. Cochrane full reviews sit behind a subscription, so readers read each original through the review abstract. IPCC full reports exceed the capture size limit, so readers read each original in part: the report page and one chapter.
- Corpus B holds the options products offer, not readers' use of those options. The usage search found studies of readers changing an option during use only for text size, a perceptual option.
- Of 106 situation candidates, 69 come from studies, 18 from user-research write-ups, 10 from lived-experience pages, 5 from public requests, 3 from guides and 1 from a service page. Public requests and service pages, two of the three search kinds, yielded few candidates, so the candidates lean on studies.

## Corpus A: Published Adaptations of One Document

| List | Index sources: candidates | Pairs confirmed by reading | Pairs unreadable | Publishers in the pairs | Pairs stating a coded need | Flag |
| --- | --- | --- | --- | --- | --- | --- |
| A1 Easy Read editions | gov.scot-publications-easy-read 412 by pattern, 6 read; gov.uk-search-easy-read 74 by pattern, 43 read | 19 | 7 | 6 | 13 | - |
| A2 Plain-language summaries | cochrane-library-reviews-p1-4 100 by pattern, 5 read; elife-digests-api 2,261 by pattern, 5 read; ema-medicines-json 1,566 by pattern, 5 read | 15 | 0 | 3 | 0 | - |
| A3 Bottom-line-up-front summaries | ipcc-reports-index 14 by pattern, 7 read; nao-reports-index 10 by pattern, 10 read | 5 | 0 | 1 | 0 | short |
| A4 Layered notices | creative-commons-licence-list 636 by pattern, 6 read; gov.uk-search-privacy-notice 794 by pattern, 36 read, 758 screened by pattern | 6 | 1 | 2 | 0 | short |

Index sources, each captured on 2026-10-17:

- A1: the GOV.UK search API, query "easy read" (one request), with candidates titled Easy Read and linked to a publication page; the Scottish Government publications search, query "easy read" (51 result pages), with candidates whose link text names easy read.
- A2: the eLife digests API (23 pages); the European Medicines Agency medicines report in JSON, limited to authorised human medicines; the first 4 pages of the Cochrane Library review listing, newest first.
- A3: the IPCC reports index; the National Audit Office reports index, first page. The National Academies publications listing showed no summary editions in the captured text, and readers dropped the listing.
- A4: the GOV.UK search API, query "privacy notice" (five requests), with candidates titled privacy notice; the Creative Commons licence list, with each deed paired with its legal code.

Findings:

- Few pairs state a need. In A1, 6 of 19 pairs state no audience or reason. Another 6 name an audience by diagnosis or by group and leave the audience's need unstated, and each of those pairs adds a reason sentence coded N11 or N16. In A2, A3 and A4, every coded need comes from a sentence that describes the edition, and each A3 summary names its audience in its title only. A reader of a sampled Easy Read page often learns the format, never the need.
- Easy Read editions change several things at once: images beside text in 19 of 19 pairs, chunking in 19 pairs, shorter length in 18 pairs and simpler wording in 17 pairs. No Easy Read edition puts a summary first. The format bundles needs N1, N3, N5 and N7, so the edition shows no single need on its own.
- By a keyword rule over the reader's notes, with each note read, 7 of 19 Easy Read pairs drop part of the original's content. Under kbp/0.9 a factor adds and removes no content, so advice drawn from these editions keeps every section and changes the presentation only.
- Plain-language summaries put the summary first in 15 of 15 pairs and change the wording in 15 pairs. Two publishers state the reader outside the field in their policies: Cochrane for every review, eLife for the articles its digests cover.
- A3 is short: 5 pairs from one publisher, each an IPCC Summary for Policymakers. The National Audit Office summaries reproduce their reports' text and name no reader, so the office yields no pair.
- A4 is short. Of 794 GOV.UK privacy notices, readers read 36 in full and screened 758 by headings or keyword hits; 1 notice carries a labelled short layer. The 5 Creative Commons deeds in the sample share one template above their legal codes.
- Every confirmed pair covers one document: 45 of 45 pairs map to `instance`, as the eligibility rule requires, so the pair rows cannot tell the levels apart. Of 10 policy rows that set an adaptation for more than one document, 6 reach a series (`scope`) and 4 reach every document of a kind (`universe`); 4 of the policy rows show their reach by pattern only.

Stated codes, from sentences that name the audience or the reason:

| Coded need (pairs) | A1 | A2 | A3 | A4 |
| --- | --- | --- | --- | --- |
| N2 key-points-first | 1 | 0 | 0 | 0 |
| N3 short-version | 2 | 0 | 0 | 0 |
| N11 choose-a-version | 7 | 0 | 0 | 0 |
| N16 find-the-part | 2 | 0 | 0 | 0 |
| C1 second-language | 1 | 0 | 0 | 0 |
| C6 reads-with-a-helper | 3 | 0 | 0 | 0 |
| audience named, no need stated | 6 | 0 | 5 | 0 |
| none stated | 6 | 15 | 0 | 6 |
| Pairs confirmed by reading | 19 | 15 | 5 | 6 |

Codes from sentences that describe the edition, counted as needs the edition serves and never as stated needs:

| Code from a feature sentence (pairs) | A1 | A2 | A3 | A4 |
| --- | --- | --- | --- | --- |
| N1 everyday-wording | 3 | 0 | 0 | 0 |
| N2 key-points-first | 1 | 0 | 5 | 0 |
| N3 short-version | 1 | 0 | 0 | 1 |
| N5 pictures-with-words | 2 | 0 | 0 | 0 |
| N11 choose-a-version | 3 | 4 | 0 | 1 |
| N16 find-the-part | 0 | 0 | 1 | 0 |

Presentation changes per list, confirmed by reading:

| Change | A1 | A2 | A3 | A4 |
| --- | --- | --- | --- | --- |
| Wording level | yes 17, unclear 2 | yes 15 | no 5 | yes 6 |
| Length | yes 18, no 1 | yes 10, no 5 | yes 5 | yes 6 |
| Order | yes 2, no 14, unclear 3 | yes 10, no 5 | unclear 5 | yes 5, no 1 |
| Summary first | no 19 | yes 15 | yes 5 | yes 6 |
| Images beside text | yes 19 | yes 9, no 6 | yes 5 | no 6 |
| Chunking | yes 19 | yes 10, no 5 | yes 5 | yes 6 |
| Audio | no 19 | no 15 | no 5 | no 6 |
| Content cut (by pattern over the reader's notes) | 7 | 0 | 0 | 0 |

Units covered, by coding rule (b):

| List | Pairs by unit covered | Policy rows by reach | Policy rows with reach by pattern only |
| --- | --- | --- | --- |
| A1 Easy Read editions | instance 19 | scope 4 | 0 |
| A2 Plain-language summaries | instance 15 | scope 1, universe 2 | 1 |
| A3 Bottom-line-up-front summaries | instance 5 | scope 1, universe 1 | 2 |
| A4 Layered notices | instance 6 | universe 1 | 1 |

## Corpus B: Reading Options Products Ship

Selection rule:

- Operating systems: iOS and iPadOS, macOS, Windows, Android, ChromeOS.
- Browsers: the four browsers with the largest worldwide share on StatCounter for September 2026: Chrome, Safari, Edge and Firefox.
- The office suites of the operating system makers: Word, Docs and Pages.
- E-readers and reading apps: Kindle, Kobo and Apple Books.
- Reading tools the same makers ship across products: Immersive Reader and Android's Reading mode.

Readers include an option when the maker's own help page, as captured, documents that the option changes the presentation of a document's content for the reader. Readers exclude options that change input, because those options belong to asking a reader for answers.

| Category | Products | Options included | Options excluded | Set in | Carries across documents | Changed during use: help page | Changed during use: study |
| --- | --- | --- | --- | --- | --- | --- | --- |
| browser | Chrome, Edge, Safari | 34 | 2 | app 18, document 16 | yes 10, no 13, unclear 11 | yes 30, unclear 4 | none found 30, related study only 4 |
| e-reader or reading app | Apple Books, Kindle, Kobo | 26 | 2 | app 26 | yes 11, unclear 15 | yes 25, unclear 1 | none found 22, related study only 4 |
| office suite | Docs (Google Workspace), Pages (Apple iWork), Word (Microsoft 365) | 25 | 1 | app 12, document 13 | yes 2, no 8, unclear 15 | yes 20, unclear 5 | none found 25 |
| operating system | Android, ChromeOS, Windows, iOS and iPadOS, macOS | 74 | 21 | system 64, app 3, document 7 | yes 57, no 7, unclear 10 | yes 43, unclear 31 | none found 67, related study only 7 |
| reading tool across products | Android Reading mode, Immersive Reader | 6 | 0 | system 4, app 2 | unclear 6 | yes 6 | none found 5, related study only 1 |

Options per presentation dimension, all categories, with the makers named:

| Dimension | Options | Makers | Set in | Carries across documents | Changed during use: help page |
| --- | --- | --- | --- | --- | --- |
| typography and spacing | 43 | Amazon, Apple, Google, Microsoft, Rakuten Kobo | system 17, app 26 | yes 24, unclear 19 | yes 36, unclear 7 |
| audio | 26 | Amazon, Apple, Google, Microsoft | system 13, app 6, document 7 | yes 11, no 7, unclear 8 | yes 24, unclear 2 |
| order or layout | 25 | Amazon, Apple, Google, Microsoft | system 3, app 9, document 13 | yes 7, no 7, unclear 11 | yes 21, unclear 4 |
| colour and contrast | 22 | Amazon, Apple, Google, Microsoft | system 18, app 4 | yes 17, unclear 5 | yes 13, unclear 9 |
| other (magnification) | 12 | Apple, Google, Microsoft | system 6, app 4, document 2 | yes 9, no 1, unclear 2 | yes 6, unclear 6 |
| motion | 11 | Apple, Google, Microsoft | system 10, app 1 | yes 10, unclear 1 | yes 1, unclear 10 |
| other (language: translation) | 7 | Apple, Google, Microsoft | document 7 | no 6, unclear 1 | yes 7 |
| length or summary | 6 | Apple, Google | document 6 | no 6 | yes 6 |
| chunking or line focus | 5 | Amazon, Apple, Google, Microsoft | system 1, app 4 | yes 1, unclear 4 | yes 4, unclear 1 |
| images beside text | 3 | Google, Microsoft | app 2, document 1 | yes 1, unclear 2 | yes 2, unclear 1 |
| other (grammar highlighting) | 1 | Microsoft | app 1 | unclear 1 | yes 1 |
| other (links shown or hidden) | 1 | Google | app 1 | unclear 1 | yes 1 |
| other (per-app values for colour, text size and motion) | 1 | Apple | app 1 | no 1 | unclear 1 |
| other (syllable breaks shown) | 1 | Microsoft | app 1 | unclear 1 | yes 1 |
| wording level | 1 | Amazon | app 1 | unclear 1 | yes 1 |

Options a reader coded with a need or condition from coding rule (a), stated on the help page or served by the option's function:

| Code | Options | Makers | Basis |
| --- | --- | --- | --- |
| N1 everyday-wording | 2 | Amazon, Microsoft | by function 1, stated 1 |
| N2 key-points-first | 4 | Apple | by function 4 |
| N3 short-version | 2 | Apple, Google | by function 2 |
| N5 pictures-with-words | 1 | Microsoft | by function 1 |
| N6 listen | 19 | Amazon, Apple, Google, Microsoft | by function 18, stated 1 |
| N7 small-chunks | 1 | Microsoft | by function 1 |
| N9 few-distractions | 23 | Amazon, Apple, Google, Microsoft | by function 7, stated 16 |
| N16 find-the-part | 4 | Apple, Google, Microsoft | by function 3, stated 1 |
| N17 less-motion | 5 | Apple, Google, Microsoft | by function 3, stated 2 |
| C1 second-language | 7 | Apple, Google, Microsoft | by function 7 |
| C4 limited-space | 2 | Apple, Microsoft | by function 2 |
| C10 attention-split | 2 | Google, Microsoft | by function 1, stated 1 |

Findings:

- Most options sit outside the document: 68 options at system level, 61 in an app and 36 per document.
- Help pages say 80 options carry across documents and 28 stay with one document; 57 help pages leave the reach unclear.
- Help pages show that a reader can change 124 options while reading and leave 41 options unclear. The usage search found no study of readers changing a shipped option during use: 149 options have no related study, and 16 text-size and font options relate to two laboratory studies of a prototype; in both studies readers enlarged text as they moved between sitting and walking (Kong et al. 2025; Chen et al. 2026).
- Apple, Google and Microsoft each ship a system setting that reduces motion: 10 of 11 motion options are system settings. Audio options come from 4 makers.
- Corpus B shows where readers supply each value and decides no `set_by` level. A help page that lets a reader change an option during use shows a capability, and a capability alone shows no reader changing a value.

## Situation Candidates

Readers searched three kinds of source: public requests for a document in another form, published user research and studies, and service pages that offer other formats. A candidate stays only when its source states the need or the condition. Composite personas are excluded, because no real reader stands behind a composite persona. Readers wrote each paraphrase as one de-identified line sharing no run of 7 words with its source, and `situation_candidates.py` checks every candidate against its capture.

The 106 candidates come from 85 sources, with 86 candidates at grade B and 20 at grade C. Each candidate carries one draft value, the code its source states most plainly.

| Draft value (code) | Candidates | Grade B | Any mention | Flag |
| --- | --- | --- | --- | --- |
| N1 everyday-wording | 4 | 3 | 15 | - |
| N2 key-points-first | 5 | 5 | 6 | - |
| N3 short-version | 5 | 4 | 10 | - |
| N4 full-detail | 4 | 4 | 6 | - |
| N5 pictures-with-words | 4 | 2 | 9 | - |
| N6 listen | 4 | 2 | 11 | - |
| N7 small-chunks | 5 | 3 | 7 | - |
| N8 meaning-stated | 3 | 3 | 4 | short (fewer than 4 candidates) |
| N9 few-distractions | 2 | 1 | 2 | short (fewer than 4 candidates) |
| N10 familiar-layout | 3 | 3 | 3 | short (fewer than 4 candidates) |
| N11 choose-a-version | 4 | 3 | 5 | - |
| N12 context-for-outsiders | 4 | 4 | 4 | - |
| N13 go-over-later | 7 | 7 | 16 | - |
| N14 numbers-with-words | 4 | 2 | 5 | - |
| N15 numbers-over-text | 4 | 3 | 4 | - |
| N16 find-the-part | 4 | 4 | 7 | - |
| N17 less-motion | 1 | 0 | 2 | short (fewer than 4 candidates) |
| C1 second-language | 4 | 4 | 4 | - |
| C2 slow-channel | 4 | 3 | 11 | - |
| C3 outside-the-field | 4 | 3 | 10 | - |
| C4 limited-space | 4 | 3 | 4 | - |
| C5 reads-short-only | 3 | 3 | 6 | short (fewer than 4 candidates) |
| C6 reads-with-a-helper | 5 | 3 | 7 | - |
| C7 worn-out | 4 | 4 | 7 | - |
| C8 loses-track | 3 | 2 | 8 | short (fewer than 4 candidates) |
| C9 under-stress | 5 | 5 | 11 | - |
| C10 attention-split | 3 | 3 | 3 | short (fewer than 4 candidates) |

Tags, by the S4 tagging rule (`kind` names the output of the work behind the document; `who` names the reader as one person, a group or an organisation):

| Tag | Value | Candidates |
| --- | --- | --- |
| kind | creation | 5 |
| kind | finding | 37 |
| kind | service | 64 |
| who | group | 13 |
| who | one | 91 |
| who | organisation | 2 |

Candidates by grade, source type and change scale. The change scale records the span over which the same reader's need changes, where the paraphrase or the first reader's note shows a change:

| Measure | Value | Candidates |
| --- | --- | --- |
| grade | B | 86 |
| grade | C | 20 |
| source type | guide | 3 |
| source type | lived-experience | 10 |
| source type | request | 5 |
| source type | service-page | 1 |
| source type | study | 69 |
| source type | user-research | 18 |
| change scale | within one reading | 4 |
| change scale | between readings | 5 |
| change scale | per document | 2 |
| change scale | over weeks or months | 2 |

Findings:

- 7 codes hold fewer than 4 candidates and stay flagged before S2 builds on them: N8, N9, N10, N17, C5, C8, C10.
- Tag `kind` is `creation` for 5 candidates, and tag `who` is `organisation` for 2 candidates. S4 needs public sources for each tag value that a draft value lacks.
- 9 candidates show a reader's need changing from moment to moment: 4 within one reading, such as a reader who stops once tiredness builds, and 5 between readings, such as a reader who sets a document aside for a clearer day. 2 candidates switch speech on only for long texts, a value that differs per document, and 2 candidates change over weeks or months.

## Literature

### One Presentation Cannot Serve Every Reader

A and B sources show the presentation suited to one reader failing or costing another:

- Numbers against words (A): W3C COGA says some readers have an impairment affecting numbers and not language, while others have a language impairment and grasp numbers easily. COGA asks for redundant forms and one action to pick a form (SA1.p-o7p02, SA1.p-o3p13).
- Summary against full detail (B): GOV.UK advises a summary of key points in audio and sign-language formats; those formats take longer and tire the reader more than reading does. The same guidance says some audiences need the full detail up front (GB1.formats, section 1.5).
- Prior knowledge (B): in the expertise reversal effect, a design that helps readers new to a subject first loses its benefit, then can harm experienced readers (Sweller et al. 2019; Kalyuga et al. 2003). Added coherence in a text helped readers with little subject knowledge, while readers with more knowledge did best with the original (McNamara et al. 1996, reported by Kalyuga et al.). Explanatory notes built into a text helped readers with low language competence and slowed knowledgeable readers (Yeung, Jin and Sweller 1998, reported by Kalyuga et al.). Signals linking text to pictures helped pupils with low prior knowledge and harmed pupils with high prior knowledge (Richter et al. 2018, abstract only).
- Spoken against written (B): written information is remembered better than spoken, and print troubles readers with low literacy and readers of a second language (Kessels 2003, a narrative review citing single studies).
- Motion against static (A and B): motion animation distracts readers with attention deficits (WCAG Understanding 2.3.3; Media Queries Level 5), while animated transitions between related charts beat static transitions for tracking change in two experiments with 24 adults (Heer and Robertson 2007).
- Audiences per document (B): ISO 24495-1 says one document can have several audiences whose needs conflict, with the primary audience taking priority (public preview only). The 2011 Federal Plain Language Guidelines say to address separate audiences separately.

### Gains for Every Reader

A source reporting a gain for every reader supports advice for every reader (plan question 5), never a factor:

- Plain English: GOV.UK reports that specialists and highly literate readers also prefer plain English and cites unnamed research on legal language (GB1.clear-language).
- Key information first, descriptive headings and short summaries: GOV.UK, Digital.gov and WCAG 2.4.6 apply each to every reader.
- Signals: nearly every signal type improves memory for the information the signal cues (Lorch 1989, abstract only). A preview of the main steps, section headings and pointer words improved transfer in print, speech and narrated animation (Mautone and Mayer 2001, abstract only).
- Segmenting: across 56 investigations, segmenting improved retention (d = 0.32) and transfer (d = 0.36) and lengthened learning time (d = −0.92), with high heterogeneity (Rey et al. 2019). The sources disagree on prior knowledge: Rey et al. found the largest retention gain among learners with high prior knowledge, against the authors' own hypothesis, while Spanjers et al. 2011 found gains for novices only (reported by Sweller et al. 2019).
- Reader view: Firefox Reader View raised reading speed by 5% on average in an online experiment with 391 readers (Li et al. 2019, abstract only).

### Values That Change from Moment to Moment

- Media Queries Level 5 (B, Working Draft): user agents must re-evaluate media queries when the environment changes, so a page follows a preference the reader changes while reading.
- W3C COGA (A): content moves only on the reader's request or with an easy way to switch the change off, and the setting stays reachable from each screen where the reader needs the setting. Both show a setting the reader can change, a capability rather than observed change.
- WCAG 2.2.4 and 2.2.2 (A): readers postpone interruptions and pause moving content while reading.
- Within-person studies (B): for 28 people searching the web on a phone, continuous attention ran over 16 seconds in a laboratory and fell to a few seconds in demanding mobile situations (Oulasvirta et al. 2005). After about 20 minutes of interrupted work, 48 people reported more stress, frustration and workload (Mark et al. 2008).
- The Microsoft cognition guidebook (B): a stressed or anxious person may find a task impossible in the moment and easy at a calmer time.
- Wobbrock 2019 (B, a review): situational impairments mostly last from seconds to hours.
- ISO 24495-1 (B, public preview): authors consider the readers' available time, attention span and emotional state.
- Corpus B and the situation candidates add to the evidence above: help pages show that readers can change most options while reading, a capability, and 9 candidates show a need changing within one reading or between readings.

### `set_by` Level per Value

- Authors fix the audience per document: ISO 24495-1 (B, public preview) and Inclusion Europe (B) tell the writer to find out who will use the information before writing. The finding points to `instance` for values about the reader of one document.
- Every confirmed Corpus A pair covers one document (`instance`) by the eligibility rule, so the pair rows cannot tell the levels apart. Policy rows show publishers setting an adaptation for a series (`scope`) or for every document of a kind (`universe`).
- W3C COGA (A, editor's draft) calls a setting easily available when the reader can set the value one time with as wide a scope as possible, such as the operating system, or save the value for a set of pages. Under coding rule (b), the first reach maps to `universe` and the second to `scope`.
- Two grade C candidates switch speech on only for long texts, so their value differs per document (`instance`). A grade C source never forms the only basis.
- Corpus B shows where readers supply values, mostly in system and app settings that carry across documents, and decides no `set_by` level.
- Prior knowledge is specific to a subject (Richter et al. 2018, abstract only), so one reader's value can differ between folders of one knowledge base, and the value grows as the reader learns (Kalyuga et al. 2003; the Microsoft cognition guidebook).

### Format Evidence for S3

- Content shape and task first: matching the method to the material may override differences in cognitive style (Kozhevnikov et al. 2014). Graphs suit spatial tasks and tables suit symbolic tasks (Vessey 1991, abstract only). A diagram groups information used together and saves search (Larkin and Simon 1987). Still frames suit events that people think of as steps (Tversky et al. 2002).
- Tables for rules with conditions: the 2011 Federal Plain Language Guidelines advise if-then tables (B). Wright and Reid 1973 stayed unreadable, so the experiment behind the owner's lead stays unverified.
- Charts: Cleveland and McGill 1984 rank elementary perceptual tasks with position on a common scale first, base the ranking on one experiment with 55 subjects, and limit the result to the graph types tested.
- Motion: animation beat static pictures overall (d = 0.37) and most for procedural-motor content (d = 1.06) (Höffler and Leutner 2007, abstract only). Comparisons that favoured animation often lacked equivalence (Tversky et al. 2002). An animation the reader controls may help, though in 2002 the decisive experiments were still missing.
- Channel: short narrated pieces beat visual-only presentation, while longer narrated pieces did worse (Leahy and Sweller, reported by Sweller et al. 2019).
- Redundancy: a diagram alone outperformed the same diagram with text restating the diagram, mostly for experienced readers (Sweller et al. 2019; Kalyuga et al. 2003). Advice on pictures beside words names the readers who gain.
- Asking a reader for answers (plan question 2, recorded only): open questions suit quantities, closed lists need complete options, and both order effects and agreement regardless of content grow as respondents tire (Krosnick and Presser 2010). GOV.UK starts a form with one thing per page and merges pages only on user-research evidence. WCAG 3.3.7 and 3.3.8 cover repeated entry and log-in.

## Factor and Value Leads

Leads come from the coded needs and conditions, the counts and the graded claims. The 2026-10-03 leads served as leads only, and every lead below was derived again from the 2026-10-17 evidence. Condition (1) cites the A or B sources named in [Literature](#literature).

| # | Factor lead | Question it asks | Value leads | Conditions | Grade | Value changes from moment to moment |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | subject-familiarity | How much does the reader already know about the document's subject? | V1a Medium, V1b Low | (1) yes (2) no (3) no (4) yes | Medium | no |
| F2 | amount-and-order | How much of the document does the reader need before the detail? | V2a High, V2c Medium | (1) yes (2) no (3) yes (4) yes | Medium | yes |
| F3 | number-form | Which form of numbers does the reader take in most easily? | V3a Medium, V3b Medium | (1) yes (2) no (3) yes (4) yes | Medium | no |
| F4 | listening | Does the reader take the document in by ear? | V4a High, V4b Low | (1) yes (2) yes (3) no (4) yes | Medium | no: the setting can change; no change observed |
| F5 | less-motion | Has the reader asked for less motion? | V5a Medium, V5b Low | (1) yes (2) yes (3) no (4) yes | Medium | no: the setting can change; no change observed |
| F6 | everyday-wording | Does the reader need everyday words and meaning stated outright? | V6a High, V6b Low | (1) no (2) no (3) no (4) yes | Low | no |
| F7 | pictures-with-words | Does the reader need pictures beside the words? | V7a High | (1) no (2) no (3) yes (4) yes | Low | no |
| F8 | distractions-and-layout | Does the reader need few distractions and a familiar layout? | V8a Medium, V8b Low | (1) no (2) yes (3) no (4) yes | Low | no |
| F9 | reads-with-a-helper | Does someone talk the document through with the reader? | K6 Medium | (1) no (2) no (3) yes (4) yes | Low | no |
| F10 | find-the-part | Does the reader need only some parts? | V10a Medium | (1) no (2) no (3) yes (4) yes | Low | no |
| F11 | reading-task | What is the reader doing with the document? | none proposed | (1) no (2) no (3) no (4) yes | Low | no |

Notes:

- F1 subject-familiarity, Medium. The literature condition holds through the expertise reversal effect, the best-supported finding in this research. Corpus support comes only through publisher policies: Cochrane and eLife state the reader outside the field for whole sets of summaries, and no pair states the need in its own text. The default value, a reader who already knows the subject, grades on literature alone.
- F2 amount-and-order, Medium. The GOV.UK passage on a summary against full detail meets condition (1), and corpus support falls short of condition (2). V2a also stands as advice for every reader. V2b, a shorter version holding only the essential points, selects content: kbp/0.9 keeps such advice out of factor guidance, so F2 proposes V2a and V2c, and S3 writes a no-change row for V2b. The value changes within one reading and between readings.
- F3 number-form, Medium. W3C COGA meets condition (1) directly, and readers coded no pair or option in either corpus to N14 or N15. Inclusion Europe advises writing "few" and "many" in place of percentages. The advice fails readers who want the figure, and the factor keys each piece of advice to its value.
- F4 listening, Medium. Kessels 2003 and the narration evidence meet condition (1), and Corpus B shows audio options from 4 makers, which meets condition (2). The default value, reading by eye, grades on literature alone, so condition (3) fails. No Corpus A pair offers audio. Readers can change the setting during use, and no reader was observed changing the value.
- F5 less-motion, Medium. W3C COGA, WCAG and Media Queries Level 5, read against Heer and Robertson 2007, meet condition (1), and Apple, Google and Microsoft each ship a system setting, which meets condition (2). The default value, no motion preference, grades on literature alone, so condition (3) fails, as for F1 and F4. One grade C situation candidate states the need. Beside distraction, the stated reasons include vestibular discomfort, a perceptual reason. Readers can change the setting during use, and no reader was observed changing the value.
- Condition (3) and default values: F1, F4 and F5 each propose a default value, and neither corpus can show a default value, so condition (3) fails for all three factors by the corpus design. F2 and F3 ask which form the reader takes in, and each of their values names a need. With default values left out of condition (3), F4 and F5 would grade High; the rule stays as written until the owner decides.
- F6 to F11, Low: gains for every reader (F6 everyday wording, F8 distractions and layout, F10 find the part), cost evidence that belongs to F1 (F7 pictures), no cost shown (F9 reads with a helper), or no coded task statements (F11 reading task). Their values stay as advice for every reader or as S3 entries.

Admission tests from plan S2.6, as evidence notes:

- One presentation cannot serve every value: condition (1) holds for F1 to F5 and fails for F6 to F11.
- Values name a need the reader states or a condition that holds, never a diagnosis: every value lead names a code from coding rule (a), and leads naming a diagnosis, a level, a style or an ability are excluded.

Value leads:

| # | Value lead | Codes | Literature | Literature evidence | Corpus (best list; Corpus B) | Situations (kinds) | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1a | context for a reader new to the subject | N12 | yes | SA2.u-unusual-words (A); GB7.prior-knowledge (B); GB4.2011 (B); CS2 (B) | no: A2: 5 pairs, 1 publisher; no option | yes: 4 (4 B); finding 4 | Medium |
| V1b | knows the subject already | none | yes | CS2 (B); GB2.structure (B); GB6.cognition (B) | no: no pair; no option | no: 0 (0 B) | Low |
| V2a | key points first, full detail kept | N2 | yes | GB4.2011 (B); SA3 (B, preview); SA1.p-o3p08 (A); SB8 (B) | yes: A2: 15 pairs, 3 publishers; 4 options, 1 maker | yes: 5 (5 B); finding 4, service 1 | High |
| V2b | a shorter version with the essential points | N3 | yes | SA1.p-o3p08 (A); SA1.p-o5p03 (A); GB1.formats (B); SB7 (B) | yes: A1: 18 pairs, 5 publishers; 2 options, 2 makers | yes: 5 (4 B); finding 3, service 2 | High |
| V2c | the full detail up front | N4 | yes | GB1.formats (B) | no: no pair; no option | yes: 4 (4 B); finding 2, service 2 | Medium |
| V3a | numbers with everyday words beside each figure | N14 | yes | SA1.p-o3p13 (A); SA5 (B) | no: no pair; no option | yes: 4 (2 B); finding 3, service 1 | Medium |
| V3b | figures or a table in place of long text | N15 | yes | SA1.p-o3p13 (A); SA1.p-o7p02 (A) | no: no pair; no option | yes: 4 (3 B); finding 4 | Medium |
| V4a | the content as sound | N6 | yes | SA2.u-pronunciation (A); SA2.u-reading-level (A); GB1.formats (B) | yes: no pair; 27 options, 4 makers | yes: 4 (2 B); creation 1, service 3 | High |
| V4b | reads by eye | none | yes | SB8 (B) | no: no pair; no option | no: 0 (0 B) | Low |
| V5a | less motion | N17 | yes | SA2.u-animation-from-interactions (A); SA2.u-pause-stop-hide (A); SA1.p-o8p01 (A); SA6 (B) | yes: no pair; 11 options, 3 makers | no: 1 (0 B); finding 1 | Medium |
| V5b | no motion preference | none | yes | SA6 (B) defines the no-preference value; EV10 (B) shows animated transitions helping 24 adults track change | no: no pair; no option | no: 0 (0 B) | Low |
| V6a | everyday words and short sentences | N1 | yes | SA1.p-o3p01 (A); GB1.clear-language (B); SA5 (B) | yes: A1: 17 pairs, 5 publishers; 2 options, 2 makers | yes: 4 (3 B); finding 2, service 2 | High |
| V6b | meaning stated outright | N8 | yes | SA1.p-o3p12 (A); SA5 (B) | no: no pair; no option | no: 3 (3 B); finding 1, service 2 | Low |
| V7a | pictures beside the words | N5 | yes | GB1.formats (B); GB7.multiple-media (B); SB8 (B) | yes: A1: 19 pairs, 6 publishers; 1 option, 1 maker | yes: 4 (2 B); finding 3, service 1 | High |
| V8a | few distractions | N9 | yes | SA1 (A); SA1.p-o5p01 (A) | yes: no pair; 23 options, 4 makers | no: 2 (1 B); finding 1, service 1 | Medium |
| V8b | a familiar, consistent layout | N10 | yes | SA2.u-consistent-navigation (A); SA1 (A) | no: no pair; no option | no: 3 (3 B); creation 1, service 2 | Low |
| V10a | a way to find and read only the parts that matter | N16 | yes | SA2.u-headings-and-labels (A); GB4.2011 (B) | no: A1: 2 pairs, 2 publishers; 4 options, 3 makers | yes: 4 (4 B); finding 1, service 3 | Medium |
| U1 | small chunks with clear space between | N7 | yes | SA1 (A); SA1.p-o2p05 (A); SA1.p-o3p10 (A); GB8.draft (B) | yes: A1: 19 pairs, 6 publishers; 1 option, 1 maker | yes: 5 (3 B); service 5 | High |
| U2 | a way to find and pick the version that suits the reader | N11 | yes | SA1 (A); SA1.p-o7p02 (A); SA1.p-o8p03 (A); SA5 (B) | yes: A1: 10 pairs, 4 publishers; no option | yes: 4 (3 B); service 4 | High |
| U3 | a copy to go over again later | N13 | yes | SB8 (B) | no: no pair; no option | yes: 7 (7 B); finding 2, service 5 | Medium |

Condition leads, graded the same way, for S2 to name values by condition when a condition reads more plainly than a need:

| # | Condition lead | Code | Literature | Literature evidence | Corpus (best list; Corpus B) | Situations (kinds) | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K1 | reads the language as a second language | C1 | yes | GB1.clear-language (B); GB7.multiple-media (B); SB8 (B) | yes: A1: 1 pair, 1 publisher; 7 options, 3 makers | yes: 4 (4 B); creation 1, service 3 | High |
| K2 | takes in long material slowly | C2 | yes | GB1.formats (B) | no: no pair; no option | yes: 4 (3 B); creation 1, service 3 | Medium |
| K3 | comes from outside the field | C3 | yes | SA2.u-unusual-words (A); GB7.prior-knowledge (B) | yes: A2: 10 pairs, 2 publishers; no option | yes: 4 (3 B); finding 2, service 2 | High |
| K4 | reads on a small screen or in limited space | C4 | yes | GB8.methods (B) | no: no pair; 2 options, 2 makers | yes: 4 (3 B); service 4 | Medium |
| K5 | reads only a short version unless a point matters | C5 | yes | GB1.clear-structure (B); GB8.draft (B) | no: no pair; no option | no: 3 (3 B); finding 1, service 2 | Low |
| K6 | reads with someone who talks the document through | C6 | yes | GB1.formats (B) | no: A1: 3 pairs, 2 publishers; no option | yes: 5 (3 B); finding 1, service 4 | Medium |
| K7 | mentally tired | C7 | yes | SA1 (A) | no: no pair; no option | yes: 4 (4 B); service 4 | Medium |
| K8 | interrupted, or loses track partway | C8 | yes | SA1 (A); SA1.p-o2p05 (A) | no: no pair; no option | no: 3 (2 B); creation 1, service 2 | Low |
| K9 | stressed, anxious or pressed for time | C9 | yes | GB1.clear-structure (B); SB7 (B); SB8 (B); GB3 (B) | no: no pair; no option | yes: 5 (5 B); service 5 | Medium |
| K10 | on the move, or attending to something else | C10 | no | SA1 (A) and SB1.review (B) name the condition; no graded source ties a document presentation to the condition | no: no pair; 2 options, 2 makers | no: 3 (3 B); finding 2, service 1 | Low |

Values outside the factor leads, each with the reason:

- U1 small chunks: segmenting gained for every reader across 56 investigations (Rey et al. 2019, meta-analysis), so the value stands as advice for every reader (plan question 5).
- U2 a way to pick the version: offering several editions and a way to pick one is a publishing choice. In a knowledge base, the reader's factor values pick the presentation.
- U3 a copy to go over again later: a copy to return to is a delivery question, and a knowledge-base document stays available. The presentation part, written beside spoken, sits under F4.
- V2b a shorter version: the value selects content, so S3 writes a no-change row. Without the 7 A1 pairs that cut content, its corpus support still meets the floor.

Leads with fewer than 4 situation candidates: V1b, V4b, V5a, V5b, V6b, V8a, V8b, K5, K8, K10.

`set_by` evidence for the High and Medium factor leads. "Thin" marks a lead resting on one or two rows or sources; "gap" marks a factor with no usable evidence:

| # | Factor lead | Corpus A rows (coding rule b) | Evidence on the level | Lead |
| --- | --- | --- | --- | --- |
| F1 | subject-familiarity | A2: pairs under a policy: instance 10; policy rows: scope 1, universe 1 | Pair rows cannot tell the levels apart, because every pair covers one document by the eligibility rule. Policy rows for C3 or N12: eLife digests for some articles (scope) and Cochrane summaries for every review (universe). Prior knowledge differs by subject (EV5d, abstract only), so one reader's value can differ between folders | scope, thin: 2 policy rows split between scope and universe, plus the per-folder argument |
| F2 | amount-and-order | A1: pairs stating a code: instance 1 | Pair rows cannot tell the levels apart, because every pair covers one document by the eligibility rule. SA3 (B, preview) and SA5 (B) tell the writer to find out who will use one document before writing it (instance) | instance, thin: literature only |
| F3 | number-form | none | No evidence | gap |
| F4 | listening | none | SC-013 and SC-051 switch speech on only for long texts, so the value differs per document (instance); both candidates are grade C, which never forms the only basis | gap: 2 grade C candidates point to instance |
| F5 | less-motion | none | SA1.p-o8p01 (A, editor's draft): an easily available setting is set one time with as wide a scope as possible, such as the operating system (universe), or saved for a set of pages (scope) | universe, thin: one A source |

Earlier leads from 2026-10-03, each mapped to the new lead and the 2026-10-17 evidence that carried the lead, or to the reason the lead dropped:

| 2026-10-03 lead | Grade then | Now | Evidence or reason |
| --- | --- | --- | --- |
| input-sense | High | F4 listening, Medium | Kessels 2003 (B); audio options from 4 makers. Touch reading and sign language sit outside the cognitive focus |
| prior-knowledge | Medium | F1 subject-familiarity, Medium | Expertise reversal (Kalyuga et al. 2003; Sweller et al. 2019); Cochrane and eLife policy rows |
| reading-level | Medium | F6 everyday-wording, Low | A level never names a value (R4), and plain wording helps every reader (GOV.UK) |
| reading-goal | Medium | F11 reading-task, Low | No source coded in the corpus states a reading task; Vessey 1991 abstract only |
| depth | Medium | F2 amount-and-order, Medium | GOV.UK accessible formats, section 1.5 (B); W3C COGA support for simplification (A). The old values summary, summary-then-detail and full map to V2b, V2a and V2c |
| externalization | Medium | dropped | Scaife and Rogers 1996 (B) describe external aids for every reader and list the cognitive value of graphics as untested; no pair, option or candidate states where a reader keeps notes |
| social-spread | Medium | F9 reads-with-a-helper, Low | GOV.UK accessible formats (B) and A1 pairs state C6; no source shows a cost to other readers |
| numeracy | Low | F3 number-form, Medium | W3C COGA patterns on numerical alternatives and alternative content (A); values renamed by need, never by a level |
| chart-reading | Low | dropped | Cleveland and McGill 1984 rank chart tasks for every reader (S3 format evidence); the old values named a level (R4) |
| representation-format | Low | X4, excluded | A value would name a cognitive style or imagery (R5) |
| whole-or-parts | Low | F10 find-the-part, Low | A1 pairs state N16; headings help every reader (WCAG 2.4.6) |
| reply-channel | Low | R13, out of scope | Asking a reader for answers falls outside presenting a document |
| text-layout | Low | dropped | Typography sits outside the cognitive focus (R8); layout consistency moved to V8b |
| abstraction, structure, encoding-form, time-budget | folded on 2026-10-03 | F1, F11, F3 and F7, K9 | Abstraction concerns prior knowledge (F1); structure concerns the task (F11); encoding-form concerns numbers against words (F3) and pictures (F7); time-budget reads as condition C9, pressed for time (K9) |
| thinking-appetite, checking-habit | Low | dropped | No source captured in this pass; a value would name a trait of the reader (R5) |
| learning-style-matching, type-instruments, field-dependence-as-style, neurotype, severity-level, dyslexia-font, grade-level-gate | Excluded | R1, R9, R5, R3, R4, R2, R4 | Each refusal carries its 2026-10-17 sources |
| riding-csa, coloured-overlay, ambiguity-tolerance | Excluded | not derived again | No source captured in this pass; the 2026-10-03 exclusions carry no weight here |

Protocol questions the leads raise:

- Question 1, advice on a document's form: F2 reading order, F3 representation, F4 channel and F5 motion carry advice beyond wording, emphasis and focus.
- Question 3, values per section: content shape stays outside the reader factors, and F11 records the task evidence.
- Question 4, values that change from moment to moment: F2 (Medium) carries evidence of change within one reading and between readings. F4 and F5 settings can change during use, and no reader was observed changing either value. The question runs once the owner approves the run.
- Question 5, advice for every reader: the values of F6, F7, F8 and F10.

## Refusals and Exclusions

| # | Claim | Sources (grade, read) | Source wording | Result | Reason |
| --- | --- | --- | --- | --- | --- |
| R1 | Matching a format to a reader's preferred learning style improves learning | Pashler et al. 2008 (B, review, 2026-10-17); Clinton-Lisell and Litzinger 2024 (B, meta-analysis of 21 studies, 2026-10-17); Kozhevnikov, Evans and Kosslyn 2014 (B, review, 2026-10-17) | "flatly contradict" (Pashler); "too small and too infrequent" (Clinton-Lisell); "premature to conclude" (Kozhevnikov) | contested | Against matching: Pashler et al. found virtually no evidence of the style-by-method crossover the claim needs, and several adequate tests contradicted matching. For a small gain: the meta-analysis pools g = 0.31 to 0.32 with I² = 91% and a crossover in 26% of outcome measures, mostly in studies below quality standards, and one review calls full dismissal of styles premature |
| R2 | A dyslexia font (OpenDyslexic) improves reading | Wery and Diliberto 2017 (B, single-case alternating treatment, 12 students, 2026-10-17) | "no improvement in reading rate or accuracy" | contradicted | The study designed to test the font found no gain, and effect sizes favoured Arial and Times New Roman. The result holds for the design and sample tested |
| R3 | A value named by diagnosis | Microsoft Inclusive Design for Cognition (B, 2026-10-17); Wobbrock et al. 2011 (B, 2026-10-17) | "very different needs" (Microsoft) | out of scope | Values name needs or conditions. People with one diagnosis can need very different things, and the design question asks: what can a person do? |
| R4 | A value naming a level (reading age, education level, confidence online) | WCAG Understanding 3.1.5 (A, 2026-10-17); GOV.UK design notes blog (C, 2026-10-17) | "lower secondary education level" (WCAG) | out of scope | Coding rule (a) keeps a level in the verbatim column and codes the need the level serves |
| R5 | A value naming a cognitive style, imagery vividness or a measured ability | Kozhevnikov 2007 (B); Kozhevnikov et al. 2014 (B); Zeman et al. 2015 (B, letter, 21 self-selected people); Mayer and Moreno 2003 (B); all 2026-10-17 | "environmentally sensitive" (Kozhevnikov et al.) | out of scope; unsupported | A value would assess the reader. Styles adapt to the environment, cognitive-style researchers reject the single visual-verbal dimension, the imagery study tests no presentation, and sorting readers by spatial ability selects readers rather than reducing load |
| R6 | Money worries lower cognitive function, so a value names the reader's income | Mani et al. 2013 (B, experiments and field study); the authors' reply (B); O'Donnell et al. 2021 (B, replication audit of 20 studies); Shah et al. 2023 (B, reply); all 2026-10-17 | "minimal influence" (O'Donnell et al.) against "mischaracterized" (Shah et al.) | contested; out of scope | Mani et al. and their reply defend the effect; the audit found most replicated effects smaller and the scarcity primes of little influence; the reply disputes half of the audited studies. A value naming income labels the reader's circumstances; condition C9 covers stress |
| R7 | Advice for tired readers rests on the sleep-deprivation meta-analysis | Lim and Dinges 2010 (B, meta-analysis of 70 articles, 2026-10-17) | "total sleep deprivation" | unsupported beyond total sleep deprivation | The meta-analysis covers total sleep deprivation up to 48 hours and tests no ordinary tiredness. Condition C7 rests on W3C COGA and situation candidates |
| R8 | Typography rules: never use serif fonts; cream backgrounds; Arial or Comic Sans | Inclusion Europe (B, 2026-10-17); British Dyslexia Association 2014 guide (C, 2026-10-17); Home Office accessibility blog and a reader comment (C, 2026-10-17) | "Never use serif fonts" (Inclusion Europe) | unsupported | No captured source tests the rules: Inclusion Europe gives no source, the 2014 guide cites none, and the blog notes conflicting advice between readers. Typography and colour also sit outside the cognitive focus |
| R9 | A style or type instrument as the basis for a value | Kozhevnikov et al. 2014 (B, 2026-10-17) | "questionable reliability and validity" | unsupported | Style instruments have questionable reliability, and no source tests a presentation keyed to an instrument's result |
| R10 | Static presentation by default for every reader, as a learning-outcome claim | Tversky et al. 2002 (B, review); Höffler and Leutner 2007 (B, meta-analysis, abstract only); both 2026-10-17 | "lack of equivalence" (Tversky); "medium-sized overall advantage" (Höffler) | contested | The review finds animation no better once comparisons are equivalent; the meta-analysis finds animation better overall and most for procedural-motor content. Two practices keep support: still frames for step-wise events, and motion when the change is the content |
| R11 | Assessing a reader's cognition, as the ability-based design principle on monitoring a user's performance does | Wobbrock et al. 2011 (B, 2026-10-17) | "monitoring, measuring, modeling, and predicting" | out of scope | The preset excludes assessing or labelling a reader's cognition |
| R12 | Clinical or compliance claims about a presentation | None captured | none | out of scope | The preset excludes clinical and compliance claims |
| R13 | Advice on asking a reader for answers (bounded or open questions, one question per page) | Krosnick and Presser 2010 (B); GOV.UK question pages and form structure (B); WCAG 3.3.7 and 3.3.8 (A); all 2026-10-17 | none | out of scope | Asking a reader for answers falls outside presenting a document under kbp/0.9; the evidence stays recorded for plan question 2 |

An earlier lead described style matching as "refuted". The adequate tests that Pashler et al. report contradict matching, and the meta-analysis pools a small gain across studies that disagree widely. The cap rule for such a meta-analysis limits the result word to "contested".

## Sources Refused or Unreadable

Each entry gives the host's answer on 2026-10-17 or 2026-10-18 UTC:

- W3C published versions of COGA, WCAG 2.2, Media Queries Level 5 and the WAI page grouping the cognitive criteria: bot check (HTTP 403). Readers read the editor's drafts.
- ISO catalogue pages for ISO 24495-1, ISO 9241-112 and ISO 9241-11, and the ANSI preview of ISO 24495-1: bot check (HTTP 403). Readers graded the standards on public previews. The ISO 9241-112:2025 preview stops at the contents and foreword, and the ISO 9241-11 preview stops before the clause on context of use.
- CDC crisis communication manual: Access Denied (HTTP 403) on every CDC host. Readers read the "Psychology of a Crisis" chapter from a copy whose document number matches the CDC edition.
- British Dyslexia Association Style Guide 2023 (PDF): Access Denied (HTTP 403). The 2026 online booklet held no text. Readers read the 2014 edition instead.
- Sears, Lin, Jacko and Xiao 2003: no DOI, no Crossref record and no full text found. Wobbrock 2019 reports the paper.
- Wicherts and Zand Scholten 2013, the comment on Mani et al.: metadata only.
- Wright and Reid 1973: the publisher page returned no text, and no open copy exists.
- Baddeley and Hitch 1974: bot check at the publisher, and the publisher withholds the abstract.
- Krosnick 1991: the author's scan holds no text layer, so readers read the abstract only.
- Mayer 2009, Paivio 1986 and Tourangeau, Rips and Rasinski 2000: publisher descriptions only; ungraded.
- Richter et al. 2016 and Schneider et al. 2018 (signalling meta-analyses), and the full texts of Höffler and Leutner 2007 and Lowe 2003: closed, read through abstracts or not at all.
- Firefox Reader View help page: bot check served under HTTP 200, twice. Firefox options stay unread.
- Apple's Assistive Access user guide: linked from a captured page and never captured.
- The eLife article pages and several publisher PDFs answered with bot checks, and the Cochrane full reviews sit behind a subscription. Readers used the copies or records named in the tables.
- W3C COGA design-guide pattern files: the editor's draft includes 59 files, and 37 of them were never captured. CAST's research page for each consideration: never captured.

## Open Facts

- No second reader has coded the Corpus A subsample, so agreement per list stays unmeasured.
- A3 and A4 are short, and A3 holds one publisher. A3 and A4 counts support Medium at most.
- No code exists for a default value: a reader who already knows the subject, a reader who reads by eye, a reader with no motion preference. Each default value rests on literature alone.
- Every A and B claim from W3C rests on an editor's draft; the published texts refused capture, so no claim was checked against the published wording.
- Key numbers come from abstracts only: Vessey 1991, Höffler and Leutner 2007, Lowe 2003, Hegarty 1992, Mautone and Mayer 2001, Mayer and Chandler 2001, Lorch 1989, Richter et al. 2018, Krosnick 1991 and Li et al. 2019.
- Readers read several papers from copies on hosts other than the publisher or the authors. The tables name each copy, and the owner decides whether such copies stand.
- Kessels 2003 reports figures from single cited studies, such as a rise in recall from 14% to over 80% with pictographs. A guidance entry resting on those figures needs the original studies captured and graded first.
- The usage search found studies for text size only. No study observes readers changing a motion, speech or reading-mode setting during use.
- The change scales and the N17 recoding come from one reader in the review pass, from the paraphrases and the first reader's notes.
- Four grading calls stand for the owner to confirm: Media Queries Level 5, a Working Draft, graded B; Krosnick and Presser 2010, a chapter in an edited handbook, graded B; W3C editor's drafts graded as the published documents they track; Chen et al. 2026 graded as the published paper from its arXiv author copy.
- The owner has yet to answer plan question 11 on sold ISO standards, so every ISO grade stays capped at B.

## Questions for S2

1. Condition (3): keep default values in the check, which holds F1, F4 and F5 at Medium, or leave default values out, which raises F4 and F5 to High?
2. F1: name its need value by need (N12, Medium) or by condition (C3, High)?
3. F2: carry the need for a shorter version through V2a, key points first with the full detail kept? V2a also stands as advice for every reader.
4. F5: declare one need value beside the default, or take the values from the `prefers-reduced-motion` registry as a source-backed factor?
5. F3, F4 and F5 carry advice on representation, channel and motion: does plan question 1 admit advice on form before S3 writes the entries?
6. Perceptual and language needs (larger print, braille, sign language, translation, the vestibular reason for less motion): inside `covers` or under `excludes`?
7. `set_by`: the leads are thin for F1 (`scope`), F2 (`instance`) and F5 (`universe`), and F3 and F4 are gaps. Declare the thin leads, or record every gap? Plan question 4 stays limited to values that change within one reading or between readings, which only F2 shows.
8. W3C COGA states N9 few distractions and N10 familiar layout for interfaces: do they apply to documents?

## S2: Header and Factors

### Header

The universe spec declares `id: cognitive-accessibility`, `label: Cognitive accessibility`, `version: "0.1"` and `conforms_to: kbp/0.9`. The id and label name the field. The version identifies the first specification; the protocol supplies the header structure and the conformance rules. The universe spec declares factors only, with no ordering frame. Under kbp/0.9, an ordering frame attaches to elements. The required empty declarations are `statuses: []`, `frames: []`, `no_artifact: { when: {} }`, `relation_kinds: []`, `elements: []`, `artifacts: []` and `relations: []`.

The overview sets the scope:

- `covers`: "Conditions that shape how documents or context are presented for knowledge work."
- `for`: "Humans and agents who present documents or context for knowledge work, and the humans who take in that documentation or context."
- `excludes`: "Selecting document sections, asking readers for answers, assessing or labelling cognition, and clinical or compliance claims. Factor values named by diagnosis, level, cognitive style, imagery or measured ability. Perceptual and language adaptations, including larger print, braille, sign language, translation and reduced motion for vestibular discomfort."

The scope includes documents and context for knowledge work by humans and agents. That scope is a specification decision. The frozen research covers presenting a finished document to a human reader. Applying the factors to context, team knowledge work or work between humans and agents has no separate research grade.

The exclusions combine protocol limits and research boundaries. Factors keep every document section available; advice belongs in guidance keyed to values. R13 records the boundary on asking readers for answers. R3, R4, R5 and R9 record the exclusions on diagnosis, levels, cognitive styles, imagery, measured ability and style instruments; R11 and R12 cover assessment and clinical or compliance claims. GB1.formats lists perceptual and language formats beside cognitive adaptations. The universe spec places those adaptations under `excludes`. SA2.u-animation-from-interactions and SA6 distinguish attention and vestibular reasons for reducing motion; the header excludes vestibular discomfort.

The term `reader` means "A human taking in a document or context by eye or by ear." F4, V4a and V4b support reading by eye or by ear; the definition includes context because the universe spec covers context. The term `reading start` means "The amount the reader takes in first, while every section stays available." The term replaces `reading depth`: F2, V2a and V2c concern the starting amount and order, and the protocol keeps every section available.

### Factors

The five factors below are declared in the universe spec. Each value describes a condition or a choice for the present reading. The questions ask which form or starting amount the reader wants for the present reading. A stated choice for one reading is not a learning style or a claim that style matching improves learning (R1; EA1, EA3).

| Id | Question | Values (value grade) | `set_by` | Research lead and sources | Factor grade |
| --- | --- | --- | --- | --- | --- |
| subject-familiarity | How familiar is the reader with the subject of the document or context? | `new-to-the-subject` (V1a, Medium); `knows-the-subject` (V1b, Low) | `scope` | F1; CS2, SA2.u-unusual-words, GB7.prior-knowledge | Medium |
| reading-start | How much does the reader want to take in first? | `key-points-first` (V2a, High); `full-detail-first` (V2c, Medium) | `instance` | F2; GB1.formats §1.5, SA1.p-o3p08 | Medium |
| number-reading | Which form of numbers does the reader want to use for this document or context? | `words-with-figures` (V3a, Medium); `figures-or-tables` (V3b, Medium) | `instance` | F3; SA1.p-o3p13, SA1.p-o7p02 | Medium |
| reading-channel | How is the reader taking in this document or context? | `by-eye` (V4b, Low); `by-ear` (V4a, High); `by-eye-and-ear` (ungraded) | `instance` | F4; SB8, GB1.formats | Medium |
| motion-setting | Which motion setting does the reader use to keep attention on the document or context? | `reduced-motion` (V5a, Medium); `no-preference` (V5b, Low) | `universe` | F5; SA2.u-animation-from-interactions, SA6, EV10 | Medium |

`knows-the-subject` matches V1b's familiarity condition. Employment in the subject would test a narrower condition. `reading-start` distinguishes key points first from full detail first, while later reading can include every section. The number values distinguish quantities explained in words beside figures from figures or tables in place of explanations in words. A reader who can use either number form chooses a form for the present reading.

### Setting Values and Evidence Gaps

`set_by` names the level where a factor value is set: `universe` once per universe spec, `scope` per folder, `instance` per document. The consumer sets the factor value; `set_by` leaves the identity of the person or tool supplying the value unspecified. Every Corpus A pair covers one document by the eligibility rule, so pair rows cannot distinguish the levels.

- `subject-familiarity` uses `scope` with thin evidence. The eLife and Cochrane policies split between `scope` and `universe` (GB9; Corpus A policy row P-A2-01). Prior knowledge differs by subject (EV5d, abstract only). The two policy rows and the subject-specific finding leave the per-folder level weakly supported.
- `reading-start` uses `instance` with thin evidence. SA3 (public preview) and SA5 address the audience for one document. Only literature supports setting the value per document.
- `number-reading` uses `instance` provisionally. F3 has no usable evidence for a `set_by` level.
- `reading-channel` uses `instance` provisionally. SC-013 and SC-051 report speech used only for long texts, which points to a per-document value. Both candidates grade C and supply insufficient evidence alone.
- `motion-setting` uses `universe` with thin evidence. SA1.p-o8p01 supports a setting made once with broad reach, or saved for a set of pages. One source supports setting the value once per universe spec and also describes saving the setting for a set of pages (`scope`).

The reader wants different starting amounts within one reading and between readings; those differences count as situation changes (F2; SA6, SA1, SA3, GB6.cognition). None of the three `set_by` levels covers a value that changes during use. `reading-start` uses `instance` while that protocol gap stays recorded. S2 adds no protocol level for changing values.

### Defaults and Combined Channel

The universe spec keeps three default values. Each grades Low from literature alone, with no corpus or situation support for the value:

- `knows-the-subject` lets adopters state familiarity explicitly (V1b; CS2, GB2.structure, GB6.cognition).
- `by-eye` gives eye-only reading an explicit answer beside listening and combined use (V4b; SB8).
- `no-preference` lets adopters state the absence of an attention-related motion preference (V5b; SA6, EV10). The value supplies no instruction to add motion.

The default values remain in the admission check, so the five factor grades remain Medium. `by-eye-and-ear` covers reading and listening together or in alternation during one reading. The single-channel values mean eye alone and ear alone. The combined value gives one answer for use of both channels. V4a and V4b support the separate channels; the combination has no research grade of its own and claims no learning benefit.

### Motion Boundary and Advice on Form

`motion-setting` asks about keeping attention on the document or context. `reduced-motion` states that movement draws attention away; `no-preference` states the absence of a motion preference for attention. A system flag alone gives no reason for reducing motion. Reduced motion for vestibular discomfort stays excluded by the header (SA2.u-animation-from-interactions, SA6).

The protocol currently describes factor advice as wording, emphasis and focus. The protocol must explicitly allow advice on form before work on the guidance slice begins. Guidance can then advise on reading order, number form, channel and motion (F2, F3, F4, F5; protocol question 1). Every document section stays available.

## Graded Sources

The tables hold 136 rows: 29 at grade A, 81 at grade B, 6 at grade C and 20 ungraded rows. "Read" gives the UTC date of the capture read. A row without a readable capture has no grade. The Corpus B help pages (191 option rows, grade B, platform documentation) sit in the fixtures with URL, hash and capture time. The Corpus A pair and policy pages are the publishers' own pages, grade B as government, intergovernmental or organisational publications, and this document cites each only for what its publisher states about its own editions.

### Standards

| # | Source | Publisher | Link | Grade: design | Read scope | Read |
| --- | --- | --- | --- | --- | --- | --- |
| SA1 | W3C COGA Task Force. Making Content Usable for People with Cognitive and Learning Disabilities (coga-usable), editor's draft | W3C (AG WG, COGA Task Force) | <https://w3c.github.io/coga/content-usable/> | A: W3C Group Note (supplemental guidance) | partial | 2026-10-17 |
| SA1.tr | W3C. Making Content Usable for People with Cognitive and Learning Disabilities, published version | W3C | <https://www.w3.org/TR/coga-usable/> | ungraded: W3C Group Note | unreadable | not read |
| SA1.p-o3p08 | W3C COGA design-guide pattern: Provide Summary of Long Documents and Media, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o3p08-summary-provided.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o3p01 | W3C COGA design-guide pattern: Use Clear Words, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o3p01-clear-words.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o2p04 | W3C COGA design-guide pattern: Make it easy to find the most important actions and information on the page, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o2p04-page-important.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o2p05 | W3C COGA design-guide pattern: Break Media into Chunks, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o2p05-chunked-media.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o3p10 | W3C COGA design-guide pattern: Use White Spacing, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o3p10-whitespace.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o3p12 | W3C COGA design-guide pattern: Explain Implied Content, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o3p12-implicit-explained.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o3p13 | W3C COGA design-guide pattern: Provide Alternatives for Numerical Concepts, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o3p13-numerical-alternatives.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o5p01 | W3C COGA design-guide pattern: Limit Interruptions, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o5p01-minimal-interruptions.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o5p03 | W3C COGA design-guide pattern: Avoid Too Much Content, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o5p03-manageable-quantity.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o7p02 | W3C COGA design-guide pattern: Provide Alternative Content for Complex Information and Tasks, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o7p02-alternative-content.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o8p01 | W3C COGA design-guide pattern: Let Users Control When the Content Moves or Changes, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o8p01-motion.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA1.p-o8p03 | W3C COGA design-guide pattern: Support Simplification, editor's draft | W3C (COGA Task Force) | <https://w3c.github.io/coga/design-guide/o8p03-complexity.html> | A: W3C Group Note pattern (included by the coga-usable editor's draft) | full | 2026-10-17 |
| SA2 | W3C. Web Content Accessibility Guidelines (WCAG) 2.2, editor's draft of 04 October 2026 | W3C (AG WG) | <https://w3c.github.io/wcag/guidelines/22/> | A: W3C Recommendation (normative success criteria) | full | 2026-10-17 |
| SA2.tr | W3C. WCAG 2.2, published Recommendation | W3C | <https://www.w3.org/TR/WCAG22/> | ungraded: W3C Recommendation | unreadable | not read |
| SA2.u-reading-level | W3C. Understanding WCAG 2.2: 3.1.5 Reading Level (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/reading-level.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-unusual-words | W3C. Understanding WCAG 2.2: 3.1.3 Unusual Words (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/unusual-words.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-abbreviations | W3C. Understanding WCAG 2.2: 3.1.4 Abbreviations (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/abbreviations.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-pronunciation | W3C. Understanding WCAG 2.2: 3.1.6 Pronunciation (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/pronunciation.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-headings-and-labels | W3C. Understanding WCAG 2.2: 2.4.6 Headings and Labels (AA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/headings-and-labels.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-section-headings | W3C. Understanding WCAG 2.2: 2.4.10 Section Headings (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/section-headings.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-consistent-navigation | W3C. Understanding WCAG 2.2: 3.2.3 Consistent Navigation (AA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/consistent-navigation.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-consistent-help | W3C. Understanding WCAG 2.2: 3.2.6 Consistent Help (A), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/consistent-help.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-redundant-entry | W3C. Understanding WCAG 2.2: 3.3.7 Redundant Entry (A), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/redundant-entry.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-accessible-authentication-minimum | W3C. Understanding WCAG 2.2: 3.3.8 Accessible Authentication (Minimum) (AA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/accessible-authentication-minimum.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-timing-adjustable | W3C. Understanding WCAG 2.2: 2.2.1 Timing Adjustable (A), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/timing-adjustable.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-interruptions | W3C. Understanding WCAG 2.2: 2.2.4 Interruptions (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/interruptions.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-animation-from-interactions | W3C. Understanding WCAG 2.2: 2.3.3 Animation from Interactions (AAA), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/animation-from-interactions.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.u-pause-stop-hide | W3C. Understanding WCAG 2.2: 2.2.2 Pause, Stop, Hide (A), editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/understanding/pause-stop-hide.html> | A: W3C Group Note (informative) | full | 2026-10-17 |
| SA2.grouping | W3C page that groups the WCAG criteria serving cognitive accessibility | W3C (WAI) | not located: every W3C WAI page refused capture | ungraded | unreadable | not read |
| SA3 | ISO 24495-1:2023 Plain language. Part 1: Governing principles and guidelines, public preview pages | ISO (TC 37), preview hosted by iTeh Standards | <https://cdn.standards.iteh.ai/samples/78907/d194fac21d6a45f38bfcfec9657f7498/ISO-24495-1-2023.pdf> | B: International Standard (sold); public preview only | partial | 2026-10-17 |
| SA3.iso | ISO 24495-1:2023 catalogue page | ISO | <https://www.iso.org/standard/78907.html> | ungraded | unreadable | not read |
| SA3.ansi | ISO 24495-1:2023 preview on the ANSI webstore | ANSI | <https://webstore.ansi.org/preview-pages/ISO/preview_ISO+24495-1-2023.pdf> | ungraded | unreadable | not read |
| SA3.iplf | International Plain Language Federation. ISO plain language standard (web page) | International Plain Language Federation | <https://www.iplfederation.org/iso-standard/> | C: practitioner federation page describing the standard | full | 2026-10-17 |
| SA4 | ISO 9241-112:2017 Ergonomics of human-system interaction. Part 112: Principles for the presentation of information, public preview pages | ISO (TC 159/SC 4), preview hosted by iTeh Standards | <https://cdn.standards.iteh.ai/samples/64840/7c6064e1009c4444a9063d2124b2c0c1/ISO-9241-112-2017.pdf> | B: International Standard (sold); public preview only | partial | 2026-10-17 |
| SA4.2025 | ISO 9241-112:2025 (second edition), public preview pages | ISO (TC 159/SC 4), preview hosted by iTeh Standards | <https://cdn.standards.iteh.ai/samples/iso/iso-9241-112-2025/68591a764aad403ca16aefb74ea62b0c/iso-9241-112-2025.pdf> | B: International Standard (sold); public preview only | partial | 2026-10-17 |
| SA4.iso | ISO 9241-112:2017 catalogue page | ISO | <https://www.iso.org/standard/64840.html> | ungraded | unreadable | not read |
| SA5 | Inclusion Europe. Information for all: European standards for making information easy to read and understand | Inclusion Europe | <https://www.inclusion-europe.eu/wp-content/uploads/2017/06/EN_Information_for_all.pdf> | B: organisational standard written in an EU-funded project with partners from 8 countries (page 5) | full | 2026-10-17 |
| SA5.web | Inclusion Europe. Easy-to-read standards page | Inclusion Europe | <https://www.inclusion-europe.eu/easy-to-read-standards-guidelines/> | B: organisational web page | full | 2026-10-17 |
| SA6 | W3C CSS WG. Media Queries Level 5, section 12.1 prefers-reduced-motion (drafts.csswg.org copy, headed W3C Working Draft 16 October 2026) | W3C (CSS WG) | <https://drafts.csswg.org/mediaqueries-5/> | B: W3C Working Draft | full | 2026-10-17 |
| SA6.tr | W3C. Media Queries Level 5, published version | W3C | <https://www.w3.org/TR/mediaqueries-5/> | ungraded | unreadable | not read |
| SA6.c39 | W3C. Techniques for WCAG 2.2: C39 Using the CSS prefers-reduced-motion query to prevent motion, editor's draft | W3C (AG WG) | <https://w3c.github.io/wcag/techniques/css/C39> | A: W3C Group Note (informative technique) | full | 2026-10-17 |

### Government and Organisational Guides

| # | Source | Publisher | Link | Grade: design | Read scope | Read |
| --- | --- | --- | --- | --- | --- | --- |
| GB1 | GOV.UK. Content design: planning, writing and managing content (topic page) | Government Digital Service (UK) | <https://www.gov.uk/guidance/content-design> | B: government guide | full | 2026-10-17 |
| GB1.meet-user-needs | GOV.UK content and publishing guidance. Write content to meet user needs | Government Digital Service (UK) | <https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/meet-user-needs/> | B: government guide | full | 2026-10-17 |
| GB1.clear-structure | GOV.UK content and publishing guidance. Create a clear structure for your content | Government Digital Service (UK) | <https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-structure/> | B: government guide | full | 2026-10-17 |
| GB1.clear-language | GOV.UK content and publishing guidance. Use clear language | Government Digital Service (UK) | <https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/> | B: government guide | full | 2026-10-17 |
| GB1.summaries | GOV.UK content and publishing guidance. Write clear summaries | Government Digital Service (UK) | <https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/summaries/> | B: government guide | full | 2026-10-17 |
| GB1.formats | UK Government. Inclusive communication: Accessible communication formats | Disability Unit, Cabinet Office (GOV.UK publication) | <https://www.gov.uk/government/publications/inclusive-communication/accessible-communication-formats> | B: government guide | full | 2026-10-17 |
| GB2.questions | GOV.UK Design System. Question pages (pattern) | Government Digital Service (UK) | <https://design-system.service.gov.uk/patterns/question-pages/> | B: government design-system pattern | full | 2026-10-17 |
| GB2.structure | GOV.UK Service Manual. Structuring forms | Government Digital Service (UK) | <https://www.gov.uk/service-manual/design/form-structure> | B: government guide | full | 2026-10-17 |
| GB3 | UK Home Office. Dos and don'ts on designing for accessibility (poster set, English) | Home Office Digital, Data and Technology | <https://raw.githubusercontent.com/UKHomeOffice/posters/master/accessibility/dos-donts/posters_en-UK/accessibility-posters-set.pdf> | B: government guide (posters, no citations) | full | 2026-10-17 |
| GB3.readme | UK Home Office posters repository README | Home Office | <https://raw.githubusercontent.com/UKHomeOffice/posters/master/README.md> | B: repository index | full | 2026-10-17 |
| GB3.blog | Home Office accessibility blog post: Dos and don'ts on designing for accessibility (2016-09-02), with reader comments | accessibility.blog.gov.uk | <https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/> | C: blog post; comments are community pages | full | 2026-10-17 |
| GB4 | Digital.gov (GSA). Plain language guide series | U.S. General Services Administration | <https://digital.gov/guides/plain-language> | B: government guide | full | 2026-10-17 |
| GB4.principles | Digital.gov (GSA). Principles of plain language | U.S. General Services Administration | <https://digital.gov/guides/plain-language/principles> | B: government guide | full | 2026-10-17 |
| GB4.writing | Digital.gov (GSA). Writing for understanding | U.S. General Services Administration | <https://digital.gov/guides/plain-language/writing> | B: government guide | full | 2026-10-17 |
| GB4.design | Digital.gov (GSA). Design for understanding | U.S. General Services Administration | <https://digital.gov/guides/plain-language/design> | B: government guide | full | 2026-10-17 |
| GB4.test | Digital.gov (GSA). Test for understanding | U.S. General Services Administration | <https://digital.gov/guides/plain-language/test> | B: government guide | full | 2026-10-17 |
| GB4.2011 | PLAIN. Federal Plain Language Guidelines, March 2011, Revision 1, May 2011 | Plain Language Action and Information Network (U.S. federal government) | <https://ies.ed.gov/ncee/rel/regions/central/pdf/CE5.3.2-Federal-Plain-Language-Guidelines.pdf> | B: government guide citing handbooks and studies per section | full | 2026-10-17 |
| GB5.2023 | British Dyslexia Association. Dyslexia Style Guide 2023 (PDF) | British Dyslexia Association | <https://cdn.bdadyslexia.org.uk/uploads/documents/Advice/style-guide/BDA-Style-Guide-2023.pdf> | ungraded | unreadable | not read |
| GB5.2026 | British Dyslexia Association. 2026 BDA Style Guide (online booklet) | British Dyslexia Association | <https://simplebooklet.com/2026bdastyleguide> | ungraded | unreadable | not read |
| GB5.2014 | British Dyslexia Association. BDA Dyslexia Style Guide, April 2014 (earlier edition, hosted by the Dyslexia-SpLD Trust) | British Dyslexia Association | <https://www.thedyslexia-spldtrust.org.uk/media/downloads/69-bda-style-guide-april14.pdf> | C: organisational style guide without citations | full | 2026-10-17 |
| GB6 | Microsoft Inclusive Design. Inclusive 101 guidebook (web), including the Persona Spectrum | Microsoft | <https://inclusive.microsoft.design/articles/inclusive-101-guidebook> | B: platform maker's design guide | full | 2026-10-17 |
| GB6.cognition | Microsoft Inclusive Design for Cognition Guidebook (2023) | Microsoft | <https://inclusive.microsoft.design/tools-and-activities/InclusiveDesignForCognitionGuidebook.pdf> | B: platform maker's design guide | full | 2026-10-17 |
| GB6.cards | Microsoft Inclusive Activity Cards (2016) | Microsoft | <https://inclusive.microsoft.design/tools-and-activities/InclusiveActivityCards.pdf> | B: platform maker's design activity cards | full | 2026-10-17 |
| GB7 | CAST. Universal Design for Learning Guidelines version 3.0 (2024), home | CAST | <https://udlguidelines.cast.org/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.customize-display | CAST UDL Guidelines 3.0. Consideration 1.1 Support opportunities to customize the display of information | CAST | <https://udlguidelines.cast.org/representation/perception/customize-display/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.ways-perceive-information | CAST UDL Guidelines 3.0. Consideration 1.2 Support multiple ways to perceive information | CAST | <https://udlguidelines.cast.org/representation/perception/ways-perceive-information/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.vocabulary-symbols-structure | CAST UDL Guidelines 3.0. Consideration 2.1 Clarify vocabulary, symbols, and language structures | CAST | <https://udlguidelines.cast.org/representation/language-symbols/vocabulary-symbols-structure/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.multiple-media | CAST UDL Guidelines 3.0. Consideration 2.5 Illustrate through multiple media | CAST | <https://udlguidelines.cast.org/representation/language-symbols/multiple-media/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.prior-knowledge | CAST UDL Guidelines 3.0. Consideration 3.1 Connect prior knowledge to new learning | CAST | <https://udlguidelines.cast.org/representation/building-knowledge/prior-knowledge/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.research-evidence | CAST UDL Guidelines 3.0. Research Evidence | CAST | <https://udlguidelines.cast.org/more/research-evidence/> | B: organisational guideline framework | full | 2026-10-17 |
| GB7.about-guidelines-3-0 | CAST UDL Guidelines 3.0. About the Guidelines 3.0 Update | CAST | <https://udlguidelines.cast.org/more/about-guidelines-3-0/> | B: organisational guideline framework | full | 2026-10-17 |
| GB8.draft | ICO. How should we draft our privacy information? (UK GDPR guidance, the right to be informed) | Information Commissioner's Office (UK regulator) | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/how-should-we-draft-our-privacy-information/> | B: regulator's guidance | full | 2026-10-17 |
| GB8.methods | ICO. What methods can we use to provide privacy information? (UK GDPR guidance, the right to be informed) | Information Commissioner's Office (UK regulator) | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/what-methods-can-we-use-to-provide-privacy-information/> | B: regulator's guidance | full | 2026-10-17 |
| GB9 | eLife. eLife Science Digests (listing page with the publisher's description of its digests) | eLife Sciences Publications | <https://elifesciences.org/digests> | B: publisher's own description of its editions | full | 2026-10-17 |

### Situational Barriers

| # | Source | Publisher | Link | Grade: design | Read scope | Read |
| --- | --- | --- | --- | --- | --- | --- |
| SB10 | ISO 9241-11:2018 Ergonomics of human-system interaction. Part 11: Usability: Definitions and concepts, public preview pages | ISO (TC 159/SC 4), preview hosted by iTeh Standards | <https://cdn.standards.iteh.ai/samples/63500/33c267a5a7564f298f02bbd65721a181/ISO-9241-11-2018.pdf> | B: International Standard (sold); public preview only | partial | 2026-10-17 |
| SB10.iso | ISO 9241-11:2018 catalogue page | ISO | <https://www.iso.org/standard/63500.html> | ungraded | unreadable | not read |
| SB1 | Sears, Lin, Jacko and Xiao 2003. When computers fade: pervasive computing and situationally-induced impairments and disabilities. HCI International 2003, vol. 2, 1298-1302 | Lawrence Erlbaum (proceedings) | no DOI; no Crossref record | ungraded: conference paper | unreadable | not read |
| SB1.review | Wobbrock 2019. Situationally-Induced Impairments and Disabilities. In Yesilada and Harper (eds), Web Accessibility, 2nd ed., Springer, 59-92. doi:10.1007/978-1-4471-7440-0_5 (author copy) | Springer | <https://faculty.washington.edu/wobbrock/pubs/siids-19.pdf> | B: narrative review (edited scholarly book chapter) | full | 2026-10-17 |
| SB2 | Wobbrock, Kane, Gajos, Harada and Froehlich 2011. Ability-based design: concept, principles and examples. ACM TACCESS 3(3), article 9. doi:10.1145/1952383.1952384 (author copy) | ACM | <https://faculty.washington.edu/wobbrock/pubs/taccess-11.pdf> | B: peer-reviewed conceptual framework with example projects | full | 2026-10-17 |
| SB4 | Oulasvirta, Tamminen, Roto and Kuorelahti 2005. Interaction in 4-second bursts: the fragmented nature of attentional resources in mobile HCI. CHI 2005, 919-928. doi:10.1145/1054972.1055101 | ACM | <https://www.interruptions.net/literature/Oulasvirta-CHI05-p919-oulasvirta.pdf> | B: peer-reviewed semi-naturalistic field study with 28 participants | full | 2026-10-17 |
| SB4.acm | Oulasvirta et al. 2005, publisher PDF | ACM | <https://dl.acm.org/doi/pdf/10.1145/1054972.1055101> | ungraded | unreadable | not read |
| SB5 | Mark, Gudith and Klocke 2008. The cost of interrupted work: more speed and stress. CHI 2008, 107-110. doi:10.1145/1357054.1357072 (author copy) | ACM | <https://ics.uci.edu/~gmark/chi08-mark.pdf> | B: peer-reviewed laboratory experiment with 48 participants (81% university students) | full | 2026-10-17 |
| SB6 | Altmann and Trafton 2002. Memory for goals: an activation-based model. Cognitive Science 26(1), 39-83. doi:10.1207/s15516709cog2601_2 | Cognitive Science Society | <http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/6ema_jgt_2002_a.pdf> | B: peer-reviewed computational model fitted to Tower of Hanoi data | full | 2026-10-17 |
| SB7 | CDC. Crisis and Emergency Risk Communication (CERC): Psychology of a Crisis, 2019 update (CS 290397-E) | U.S. Centers for Disease Control and Prevention | <https://www.susana.org/downloads?documentID=54804> | B: government guide (manual chapter) citing studies | full | 2026-10-17 |
| SB7.cdc | CDC CERC manual index | CDC | <https://www.cdc.gov/cerc/php/cerc-manual/index.html> | ungraded | unreadable | not read |
| SB7.stacks | CDC Stacks record for CERC: Psychology of a Crisis | CDC | <https://stacks.cdc.gov/view/cdc/60292> | ungraded | unreadable | not read |
| SB8 | Kessels 2003. Patients' memory for medical information. J R Soc Med 96(5), 219-222. doi:10.1177/014107680309600504 | Royal Society of Medicine (SAGE) | <https://www.everybodytexas.org/uploads/files/general/2003-05_JRCM_Kessels_PatientMemory.pdf> | B: peer-reviewed narrative review | full | 2026-10-17 |
| SB9 | Lim and Dinges 2010. A meta-analysis of the impact of short-term sleep deprivation on cognitive variables. Psychological Bulletin 136(3), 375-389. doi:10.1037/a0018883 (author institution copy) | American Psychological Association | <https://www.med.upenn.edu/uep/assets/user-content/documents/LimDinges2010MetaAnalysis.pdf> | B: meta-analysis (70 articles, 147 tests; total sleep deprivation up to 48 h) | full | 2026-10-17 |
| SB11 | Mani, Mullainathan, Shafir and Zhao 2013. Poverty impedes cognitive function. Science 341, 976-980. doi:10.1126/science.1238041 (author copy) | AAAS | <https://sendhil.org/wp-content/uploads/2019/08/Publication-24.pdf> | B: peer-reviewed laboratory experiments and a field study | full | 2026-10-17 |
| SB11.reply | Mani, Mullainathan, Shafir and Zhao 2013. Response to Comment on Poverty Impedes Cognitive Function. Science 342, 1169. doi:10.1126/science.1246799 (author lab copy) | AAAS | <http://zhaolab.psych.ubc.ca/pdfs/Zhao_2013_Science_response.pdf> | B: peer-reviewed technical response | full | 2026-10-17 |
| SB11.comment | Wicherts and Zand Scholten 2013. Comment on Poverty Impedes Cognitive Function. Science 342, 1169. doi:10.1126/science.1246680 | AAAS | <https://research.tilburguniversity.edu/en/publications/comment-on-poverty-impedes-cognitive-function/> | ungraded: peer-reviewed technical comment | unreadable | not read |
| SB11.audit | O'Donnell et al. 2021. Empirical audit and review and an assessment of evidentiary value in research on the psychological consequences of scarcity. PNAS 118(44), e2103313118. doi:10.1073/pnas.2103313118 (Europe PMC full text) | National Academy of Sciences | <https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8612349/fullTextXML> | B: peer-reviewed replication audit of 20 studies | full | 2026-10-17 |
| SB11.audit-reply | Shah, Zhao, Mullainathan and Shafir 2023. A scarcity literature mischaracterized with an empirical audit. PNAS 120(26), e2206054120 (Europe PMC full text) | National Academy of Sciences | <https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10293841/fullTextXML> | B: peer-reviewed letter | full | 2026-10-17 |

### Cognitive Science and Format Evidence

| # | Source | Copy read | Link | Grade: design | Read scope | Read |
| --- | --- | --- | --- | --- | --- | --- |
| CS1a | Sweller 1988. Cognitive load during problem solving: effects on learning. Cognitive Science 12:257-285 | third-party mirror of the publisher's free-access PDF (Wiley footer on every page) | doi:10.1207/s15516709cog1202_4 | B: experiments plus computational model | full text | 2026-10-17 |
| CS1b | Sweller, van Merrienboer, Paas 2019. Cognitive architecture and instructional design: 20 years later. Educational Psychology Review 31:261-292 | publisher open access (CC BY) | doi:10.1007/s10648-019-09465-5 | B: narrative review of cognitive load effects | full text | 2026-10-17 |
| CS2 | Kalyuga, Ayres, Chandler, Sweller 2003. The expertise reversal effect. Educational Psychologist 38(1):23-31 | third-party copy of the University of Wollongong Research Online file (repository cover page included) | doi:10.1207/S15326985EP3801_4 | B: narrative review of experiments | full text | 2026-10-17 |
| CS3a | Mayer, Moreno 2003. Nine ways to reduce cognitive load in multimedia learning. Educational Psychologist 38(1):43-52 | third-party course copy (University of Kentucky course page) | doi:10.1207/S15326985EP3801_6 | B: review of the authors' experiments, with effect sizes per method | full text | 2026-10-17 |
| CS3b | Mayer 2009. Multimedia Learning, 2nd edition. Cambridge University Press (book) | publisher book page | doi:10.1017/CBO9780511811678 | ungraded: book | description only | 2026-10-17 |
| CS4a | Clark, Paivio 1991. Dual coding theory and education. Educational Psychology Review 3(3):149-210 | third-party course copy (CSU Chico course page), scan with text layer | doi:10.1007/BF01320076 | B: narrative review | full text | 2026-10-17 |
| CS4b | Paivio 1986 (online 1990). Mental Representations: A Dual Coding Approach. Oxford University Press (book) | bibliographic record (OpenAlex) | doi:10.1093/acprof:oso/9780195066661.001.0001 | ungraded: book | description only | 2026-10-17 |
| CS5 | Baddeley, Hitch 1974. Working memory. Psychology of Learning and Motivation 8:47-89 | publisher page refused (HTTP 403 challenge) | doi:10.1016/S0079-7421(08)60452-1 | ungraded: book chapter (theory and experiments) | unreadable | not read |
| CS6a | Kozhevnikov 2007. Cognitive styles in the context of modern psychology: toward an integrated framework of cognitive style. Psychological Bulletin 133(3):464-481 | author-hosted (author's site) | doi:10.1037/0033-2909.133.3.464 | B: narrative review | full text | 2026-10-17 |
| CS6b | Kozhevnikov, Evans, Kosslyn 2014. Cognitive style as environmentally sensitive individual differences in cognition. Psychological Science in the Public Interest 15(1):3-33 | author-hosted (linked from the author's articles page) | doi:10.1177/1529100614525555 | B: narrative review | full text | 2026-10-17 |
| CS7 | Zeman, Dewar, Della Sala 2015. Lives without imagery: congenital aphantasia. Cortex 73:378-380 | institutional repository (University of Edinburgh) | doi:10.1016/j.cortex.2015.05.019 | B: letter: questionnaire case series, 21 self-selected people, 121 controls | full text | 2026-10-17 |
| CS8 | Scaife, Rogers 1996. External cognition: how do graphical representations work?. International Journal of Human-Computer Studies 45:185-213 | authors' institution (University of Sussex cognitive science research paper CSRP 335) | doi:10.1006/ijhc.1996.0048 | B: critical review and theoretical framework | full text (report version) | 2026-10-17 |
| CS9 | Pirolli, Card 1999. Information foraging. Psychological Review 106(4):643-675 | university archive (CMU ACT-R site) of the authors' UIR technical report | doi:10.1037/0033-295X.106.4.643 | B: theory with a process model fitted to one experiment | full text (report version) | 2026-10-17 |
| EA1 | Pashler, McDaniel, Rohrer, Bjork 2008. Learning styles: concepts and evidence. Psychological Science in the Public Interest 9(3):105-119 | author-hosted (Bjork lab, UCLA) | doi:10.1111/j.1539-6053.2009.01038.x | B: review against a stated test (style-by-method crossover interaction) | full text | 2026-10-17 |
| EA2 | Wery, Diliberto 2017 (online 2016). The effect of a specialized dyslexia font, OpenDyslexic, on reading rate and accuracy. Annals of Dyslexia 67:114-127 | publisher open access (CC BY) | doi:10.1007/s11881-016-0127-1 | B: single-case alternating treatment experiment with 12 elementary students | full text | 2026-10-17 |
| EA3 | Clinton-Lisell, Litzinger 2024. Is it really a neuromyth? A meta-analysis of the learning styles matching hypothesis. Frontiers in Psychology 15:1428732 | publisher open access (CC BY) | doi:10.3389/fpsyg.2024.1428732 | B: meta-analysis (21 studies, 101 effect sizes, 1,712 participants; robust variance estimation) | full text | 2026-10-17 |
| EV1 | Wright, Reid 1973. Written information: some alternatives to prose for expressing the outcomes of complex contingencies. Journal of Applied Psychology 57(2):160-166 | publisher page returned no text (script-only page) | doi:10.1037/h0037045 | ungraded: experiment (per secondary descriptions; unverified) | unreadable | not read |
| EV2 | Vessey 1991. Cognitive fit: a theory-based analysis of the graphs versus tables literature. Decision Sciences 22(2):219-240 | bibliographic record (OpenAlex) carrying the publisher abstract | doi:10.1111/j.1540-5915.1991.tb00344.x | B: theory tested against published studies | abstract only | 2026-10-17 |
| EV3 | Larkin, Simon 1987. Why a diagram is (sometimes) worth ten thousand words. Cognitive Science 11:65-99 | third-party course copy (UCSD course page), scan with text layer | doi:10.1111/j.1551-6708.1987.tb00863.x | B: computational models of informationally equivalent representations | full text | 2026-10-17 |
| EV4 | Cleveland, McGill 1984. Graphical perception: theory, experimentation, and application to the development of graphical methods. Journal of the American Statistical Association 79(387):531-554 | third-party course page hosting a JSTOR download (JSTOR terms page included) | doi:10.1080/01621459.1984.10478080 | B: theory plus experiments (position-length experiment with 55 subjects) | full text | 2026-10-17 |
| EV5a | Mayer, Chandler 2001. When learning is just a click away: does simple user interaction foster deeper understanding of multimedia messages?. Journal of Educational Psychology 93(2):390-397 | bibliographic record (OpenAlex) carrying the publisher abstract; ERIC EJ638751 abstract also captured | doi:10.1037/0022-0663.93.2.390 | B: two experiments | abstract only | 2026-10-17 |
| EV5b | Mautone, Mayer 2001. Signaling as a cognitive guide in multimedia learning. Journal of Educational Psychology 93(2):377-389 | bibliographic record (OpenAlex) carrying the publisher abstract; ERIC EJ638750 abstract also captured | doi:10.1037/0022-0663.93.2.377 | B: three experiments | abstract only | 2026-10-17 |
| EV5c | Rey, Beege, Nebel, Wirzberger, Schmitt, Schneider 2019. A meta-analysis of the segmenting effect. Educational Psychology Review 31:389-419 | author-hosted (co-author's site) | doi:10.1007/s10648-018-9456-4 | B: meta-analysis (56 investigations, 88 pairwise comparisons) | full text | 2026-10-17 |
| EV5d | Richter, Scheiter, Eitel 2018. Signaling text-picture relations in multimedia learning: the influence of prior knowledge. Journal of Educational Psychology 110(4):544-560 | ERIC record (abstract) | doi:10.1037/edu0000220 | B: quasi-experimental field study, 8th graders | abstract only | 2026-10-17 |
| EV6 | Lorch 1989. Text-signaling devices and their effects on reading and memory processes. Educational Psychology Review 1(3):209-234 | publisher landing page (abstract) | doi:10.1007/BF01320135 | B: narrative review | abstract only | 2026-10-17 |
| EV7 | Tversky, Morrison, Betrancourt 2002. Animation: can it facilitate?. International Journal of Human-Computer Studies 57:247-262 | course page at the first author's university at the time (Stanford HCI) | doi:10.1006/ijhc.2002.1017 | B: narrative review | full text | 2026-10-17 |
| EV8 | Hoffler, Leutner 2007. Instructional animation versus static pictures: a meta-analysis. Learning and Instruction 17:722-738 | ERIC record (abstract) | doi:10.1016/j.learninstruc.2007.09.013 | B: meta-analysis (26 studies, 76 comparisons) | abstract only | 2026-10-17 |
| EV9 | Lowe 2003. Animation and learning: selective processing of information in dynamic graphics. Learning and Instruction 13(2):157-176 | ERIC record (abstract written by ERIC) | doi:10.1016/S0959-4752(02)00018-X | B: experiment, 12 animation and 12 control undergraduates | abstract only | 2026-10-17 |
| EV10 | Heer, Robertson 2007. Animated transitions in statistical data graphics. IEEE Transactions on Visualization and Computer Graphics 13(6):1240-1247 | author-hosted (first author's lab) | doi:10.1109/TVCG.2007.70539 | B: two controlled experiments with 24 adults aged 26-62 | full text | 2026-10-17 |
| EV11 | Hegarty 1992. Mental animation: inferring motion from static displays of mechanical systems. Journal of Experimental Psychology: Learning, Memory, and Cognition 18(5):1084-1102 | Europe PMC record (MEDLINE abstract) | doi:10.1037/0278-7393.18.5.1084 | B: experiments (reaction time and eye fixation) | abstract only | 2026-10-17 |
| EV12a | Krosnick 1991. Response strategies for coping with the cognitive demands of attitude measures in surveys. Applied Cognitive Psychology 5:213-236 | bibliographic record (OpenAlex) carrying the publisher abstract | doi:10.1002/acp.2350050305 | B: theory and review | abstract only | 2026-10-17 |
| EV12b | Krosnick, Presser 2010. Question and questionnaire design. Handbook of Survey Research, 2nd edition, chapter 9 (Emerald) | author-hosted (first author's Stanford pages) | <https://web.stanford.edu/dept/communication/faculty/krosnick/docs/2010/2010%20Handbook%20of%20Survey%20Research.pdf> | B: review chapter in an edited handbook | full text | 2026-10-17 |
| EV13 | Tourangeau, Rips, Rasinski 2000. The Psychology of Survey Response. Cambridge University Press (book) | publisher book page | doi:10.1017/CBO9780511819322 | ungraded: book | description only | 2026-10-17 |
| EV14a | Government Digital Service 2016 (updated 2018). Structuring forms (Service Manual). GOV.UK Service Manual | government guide (publisher's own page) | <https://www.gov.uk/service-manual/design/form-structure> | B: government design guidance | full text | 2026-10-17 |
| EV14b | Government Digital Service design notes blog 2015. One thing per page | government blog | <https://designnotes.blog.gov.uk/2015/07/03/one-thing-per-page/> | C: blog post with practitioner comments | full text | 2026-10-17 |

### Corpus B Usage Studies

| # | Source | Copy read | Link | Grade: design | Read |
| --- | --- | --- | --- | --- | --- |
| BV1 | Kong, Wobbrock, Cai and Bylinskii 2025, Supporting Mobile Reading While Walking with Automatic and Customized Font Size Adaptations, CHI 2025 | author-hosted (first author's site) | doi:10.1145/3706598.3713367 | B: lab experiment with 45 participants, prototype reading app on a phone, sitting and walking | 2026-10-18 |
| BV2 | Chen, Nie, Zhang et al. 2026, SituFont: A Just-in-Time Adaptive Intervention Interface for Enhancing Mobile Readability in Situational Visual Impairments, CHI 2026 | arXiv v2 author copy (27 Jan 2026) headed CHI '26 and matching the Crossref title, graded as the published paper | doi:10.1145/3772318.3791020 | B: formative interviews with 15 people; controlled experiment with 18 participants; comparative study with 12 participants; Chinese text | 2026-10-18 |
| BV3 | Kong, Cai and Bylinskii 2023, Improving Mobile Reading Experiences While Walking Through Automatic Adaptations and Prompted Customization, UIST 2023 Adjunct | author-hosted (first author's site) | doi:10.1145/3586182.3616666 | C: 3-page adjunct paper; preliminary user study of a prototype | 2026-10-18 |
| BV4 | Li, Morris, Fourney, Larson and Reinecke 2019, The Impact of Web Browser Reader Views on Reading Speed and User Experience, CHI 2019 | Microsoft Research copy (an author's institution); abstract only | doi:10.1145/3290605.3300754 | B: online experiment with 391 readers (42 self-reported dyslexia); Firefox Reader View against standard pages | 2026-10-18 |
| BV5 | Appt (Q42), Font size statistics page | the publisher's own page | <https://appt.org/en/stats/font-size> | C: industry usage report from apps in the Netherlands; method described on the page only in outline | 2026-10-18 |
