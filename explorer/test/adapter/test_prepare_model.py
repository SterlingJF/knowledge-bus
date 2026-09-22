"""Adapter contract tests using the authored reference universe."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "prepare_model", ROOT / "tools/explorer/prepare_model.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = yaml.safe_load(
            (ROOT / "universes/product-development/universe.kbp.yaml").read_text()
        )
        cls.protocol = yaml.safe_load(
            (ROOT / "protocol/knowledge-bus-protocol.yaml").read_text()
        )
        cls.guidance = yaml.safe_load(
            (ROOT / "universes/product-development/type-guidance.kbp.yaml").read_text()
        )
        cls.marks = yaml.safe_load(
            (ROOT / "universes/product-development/marks.explorer.yaml").read_text()
        )
        cls.entities = MODULE.prepare_model(cls.source, cls.protocol)["entities"]

    def some_declared_mark(self, marks):
        for section in MODULE.MARK_SECTIONS:
            for subject in marks.get(section) or {}:
                return section, subject
        raise AssertionError("the marks document must declare something to be patched")

    def test_marks_naming_a_concept_the_universe_does_not_declare_are_refused(self):
        universe_has = {
            section: set(self.marks.get(section) or {})
            for section in MODULE.MARK_SECTIONS
        }
        self.assertTrue(
            any(universe_has.values()), "the document must declare a mark somewhere"
        )
        for section in MODULE.MARK_SECTIONS:
            marks = copy.deepcopy(self.marks)
            declared = marks.setdefault(section, {})
            declared["not-a-concept-of-this-universe"] = (
                {"monogram": "Zz"}
                if section != "options"
                else {"also-not-a-concept": {"monogram": "Zz"}}
            )
            with self.assertRaises(ValueError):
                MODULE.prepare_marks(self.source, marks, self.entities)
        wrong_section = copy.deepcopy(self.marks)
        section, subject = self.some_declared_mark(wrong_section)
        moved = "factors" if section == "frames" else "frames"
        wrong_section.setdefault(moved, {})[subject] = wrong_section[section].pop(
            subject
        )
        with self.assertRaises(ValueError):
            MODULE.prepare_marks(self.source, wrong_section, self.entities)
        unknown_section = copy.deepcopy(self.marks)
        unknown_section["elements"] = {
            next(iter(self.marks["frames"])): {"monogram": "Zz"}
        }
        with self.assertRaises(ValueError):
            MODULE.prepare_marks(self.source, unknown_section, self.entities)
        for_another_universe = copy.deepcopy(self.marks)
        for_another_universe["marks"]["marks_for"] = "some-other-universe"
        with self.assertRaises(ValueError):
            MODULE.prepare_marks(self.source, for_another_universe, self.entities)

    def test_two_concepts_declaring_one_mark_are_refused(self):
        marks = copy.deepcopy(self.marks)
        section, subject = self.some_declared_mark(marks)
        others = [name for name in marks[section] if name != subject]
        self.assertTrue(others, "the document must declare two marks in one section")
        marks[section][others[0]] = copy.deepcopy(marks[section][subject])
        with self.assertRaises(ValueError):
            MODULE.prepare_marks(self.source, marks, self.entities)

    def test_a_mark_that_is_neither_a_drawable_pictogram_nor_a_monogram_is_refused(
        self,
    ):
        malformed = [
            {},
            {"monogram": "Ph", "glyph": "M4 4h16v16H4Z"},
            {"pictogram": "M4 4h16v16H4Z"},
            {"monogram": ""},
            {"monogram": "Phase"},
            {"monogram": "P h"},
            {"glyph": ""},
            {"glyph": "frame"},
            {"glyph": "url(#phase)"},
            {"glyph": "https://example.com/phase.svg"},
            {"glyph": "#phase"},
            {"glyph": "../icons/phase.svg"},
            {"glyph": "M4 4h16v16H4Z<script>"},
            {"glyph": "h16v16"},
            "M4 4h16v16H4Z",
            ["M4 4h16v16H4Z"],
            None,
        ]
        _, subject = self.some_declared_mark(self.marks)
        for candidate in malformed:
            marks = copy.deepcopy(self.marks)
            marks["frames"][subject] = candidate
            with self.assertRaises(
                (ValueError, TypeError), msg=f"{candidate!r} was accepted"
            ):
                MODULE.prepare_marks(self.source, marks, self.entities)
        for accepted in (
            {"monogram": "P"},
            {"monogram": "Ph"},
            {"glyph": "M4 4h16v16H4Z"},
        ):
            marks = copy.deepcopy(self.marks)
            marks["frames"][subject] = accepted
            MODULE.prepare_marks(self.source, marks, self.entities)

    def test_a_universe_prepared_without_marks_carries_none(self):
        model = MODULE.prepare_model(self.source, self.protocol)
        self.assertIsNone(model["marks"])

    def test_every_declared_mark_reaches_a_concept_the_model_holds(self):
        model = MODULE.prepare_model(self.source, self.protocol, None, self.marks)
        carried = model["marks"]["declared"]
        ids = {entity["id"] for entity in model["entities"]}
        declared_count = sum(
            len(self.marks.get(section) or {}) for section in ("frames", "factors")
        ) + sum(
            len(values or {}) for values in (self.marks.get("options") or {}).values()
        )
        self.assertTrue(declared_count)
        self.assertEqual(len(carried), declared_count)
        self.assertEqual(len(set(map(json.dumps, carried.values()))), declared_count)
        for subject, mark in carried.items():
            self.assertIn(subject, ids)
            self.assertEqual(len(mark), 1)
            self.assertIn(next(iter(mark)), ("glyph", "monogram"))

    def declared_entries(self, guidance=None):
        document = guidance or self.guidance
        found = []
        for plural, kind in MODULE.guidance_sections(self.protocol):
            for subject_id, entries in (document.get(plural) or {}).items():
                for entry in entries:
                    found.append((f"{kind}:{subject_id}", entry))
        return found

    def test_a_universe_prepared_without_guidance_carries_none_and_stays_valid(self):
        model = MODULE.prepare_model(self.source, self.protocol)
        self.assertIsNone(model["guidance"])

    def test_every_claim_reaches_its_declared_subject_byte_for_byte(self):
        model = MODULE.prepare_model(self.source, self.protocol, self.guidance)
        declared = self.declared_entries()
        carried = model["guidance"]["entries"]
        self.assertTrue(declared)
        self.assertEqual(len(carried), len(declared))
        ids = {entity["id"] for entity in model["entities"]}
        for (subject, entry), held in zip(declared, carried):
            self.assertEqual(held["subject"], subject)
            self.assertIn(subject, ids)
            self.assertEqual(held["claim"], entry["claim"])
            self.assertEqual(held["kind"], entry["kind"])
            self.assertEqual(held["source"], entry["source"])
            self.assertEqual(held["when"], entry.get("when"))
        self.assertEqual(len({held["id"] for held in carried}), len(carried))

    def test_the_kinds_and_sources_the_document_declares_are_carried_whole(self):
        model = MODULE.prepare_model(self.source, self.protocol, self.guidance)
        carried = model["guidance"]
        self.assertEqual(carried["kinds"], self.guidance["guidance_kinds"])
        self.assertEqual(set(carried["sources"]), set(self.guidance["sources"]))
        for name, declared in self.guidance["sources"].items():
            self.assertEqual(carried["sources"][name]["cite"], declared["cite"])
        declared_kinds = {kind["id"] for kind in carried["kinds"]}
        for entry in carried["entries"]:
            self.assertIn(entry["kind"], declared_kinds)
            self.assertTrue(
                entry["source"] in carried["sources"] or entry["source"] == "asserted"
            )
        serialized = json.dumps(carried)
        urls = [
            declared["url"]
            for declared in self.guidance["sources"].values()
            if "url" in declared
        ]
        self.assertTrue(
            urls, "the document must cite a url for this exclusion to be under test"
        )
        for url in urls:
            self.assertNotIn(url, serialized)
        for declared in carried["sources"].values():
            self.assertNotIn(
                MODULE.SOURCE_FIELD_A_SELF_CONTAINED_ARTIFACT_CANNOT_CARRY, declared
            )

    def test_guidance_for_another_universe_is_refused(self):
        guidance = copy.deepcopy(self.guidance)
        guidance["guidance"]["guides"] = "some-other-universe"
        with self.assertRaises((ValueError, KeyError)):
            MODULE.prepare_model(self.source, self.protocol, guidance)

    def test_guidance_naming_an_undeclared_kind_or_subject_is_refused(self):
        for patch in ("kind", "subject"):
            guidance = copy.deepcopy(self.guidance)
            first = next(iter(guidance["elements"]))
            if patch == "kind":
                guidance["elements"][first][0]["kind"] = "not-a-declared-kind"
            else:
                guidance["elements"]["not-an-element-of-this-universe"] = guidance[
                    "elements"
                ][first]
            with self.assertRaises(ValueError):
                MODULE.prepare_model(self.source, self.protocol, guidance)

    def test_a_universe_document_passed_as_guidance_is_refused(self):
        with self.assertRaises((TypeError, ValueError)):
            MODULE.prepare_model(self.source, self.protocol, self.source)

    def test_cli_round_trip_carries_guidance_only_when_it_is_named(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, argv_extra, expected in (
                ("bare.json", [], None),
                (
                    "guided.json",
                    [
                        "--guidance",
                        str(
                            ROOT
                            / "universes/product-development/type-guidance.kbp.yaml"
                        ),
                    ],
                    len(self.declared_entries()),
                ),
            ):
                output = Path(directory) / name
                self.assertEqual(
                    MODULE.main(
                        [
                            "--input",
                            str(
                                ROOT / "universes/product-development/universe.kbp.yaml"
                            ),
                            "--output",
                            str(output),
                        ]
                        + argv_extra
                    ),
                    0,
                )
                carried = json.loads(output.read_text())["guidance"]
                self.assertEqual(
                    None if carried is None else len(carried["entries"]), expected
                )

    def test_real_universe_retains_identity_phrasing_and_raw_declarations(self):
        model = MODULE.prepare_model(self.source, self.protocol)
        self.assertEqual(model["schema"], "knowledge-bus/explorer-model/1")
        self.assertEqual(model["orderingFrameId"], "frame:phase")
        self.assertEqual(model["source"], self.source)
        self.assertEqual(model["evaluation"], {"status": "unresolved", "context": None})
        ids = [entity["id"] for entity in model["entities"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("option:phase:design", ids)
        self.assertEqual(
            len([e for e in model["entities"] if e["kind"] == "artifact"]),
            len(self.source["artifacts"]),
        )
        for edge in model["connections"]:
            self.assertIn(edge["from"], ids)
            self.assertIn(edge["to"], ids)
            if edge["kind"] != "composition":
                definition = next(
                    d for d in self.source["relation_kinds"] if d["id"] == edge["kind"]
                )
                self.assertEqual(edge["phrasing"], definition["phrasing"])
                self.assertEqual("reverse" in edge["phrasing"], edge["ordered"])

    def test_canonical_fixture_is_fresh_and_projection_is_deterministic(self):
        first = MODULE.prepare_model(
            self.source, self.protocol, self.guidance, self.marks
        )
        fixture = json.loads(
            (ROOT / "explorer/test/fixtures/product-development.json").read_text()
        )
        self.assertEqual(first, fixture)
        second = MODULE.prepare_model(
            copy.deepcopy(self.source), self.protocol, self.guidance, self.marks
        )
        self.assertEqual(first, second)
        changed = copy.deepcopy(self.source)
        changed["universe"]["label"] += " updated"
        self.assertNotEqual(
            first["sourceDigest"],
            MODULE.prepare_model(changed, self.protocol, self.guidance, self.marks)[
                "sourceDigest"
            ],
        )

    def test_invalid_universe_does_not_create_output(self):
        source = copy.deepcopy(self.source)
        source["relations"][0]["to"] = "missing-entity"
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "invalid.yaml"
            output_path = Path(directory) / "model.json"
            input_path.write_text(yaml.safe_dump(source))
            self.assertEqual(
                MODULE.main(["--input", str(input_path), "--output", str(output_path)]),
                1,
            )
            self.assertFalse(output_path.exists())

    def test_mismatched_protocol_fails(self):
        source = copy.deepcopy(self.source)
        source["universe"]["conforms_to"] = "kbp/unknown"
        with self.assertRaisesRegex(ValueError, "conforms_to"):
            MODULE.prepare_model(source, self.protocol)

    def test_missing_phrasing_fails_instead_of_raw_label_fallback(self):
        source = copy.deepcopy(self.source)
        source["relation_kinds"][0].pop("phrasing")
        with self.assertRaises(ValueError):
            MODULE.prepare_model(source, self.protocol)

    def test_wiring_records_every_frame_reference(self):
        model = MODULE.prepare_model(self.source, self.protocol)
        kinds = {entry["kind"] for entry in model["wiring"]}
        self.assertEqual(
            kinds,
            {
                "ordering",
                "gate",
                "disabled_when",
                "composition.when",
                "relation.gate",
                "empty_composition.when",
            },
        )
        for entry in model["wiring"]:
            self.assertTrue(entry["from"].startswith("frame:"))
            self.assertIsInstance(entry["value"], list)
            self.assertTrue(entry["sourcePath"])
        ordering = [e for e in model["wiring"] if e["kind"] == "ordering"]
        elements = [e for e in model["entities"] if e["kind"] == "element"]
        self.assertEqual(len(ordering), len(elements))
        conditional = [e for e in model["wiring"] if e["kind"] == "composition.when"]
        self.assertTrue(conditional)
        for entry in conditional:
            self.assertEqual(len(entry["targetPair"]), 2)
            self.assertIn(entry["to"], entry["targetPair"])
        rule = [e for e in model["wiring"] if e["kind"] == "empty_composition.when"]
        self.assertTrue(rule)
        for entry in rule:
            self.assertEqual(entry["to"], model["rules"][0]["id"])

    def test_wiring_refuses_an_undeclared_frame(self):
        source = copy.deepcopy(self.source)
        source["elements"][0]["gate"] = {"not-a-frame": ["yes"]}
        with self.assertRaises(ValueError):
            MODULE.prepare_model(source, self.protocol)

    def test_cli_output_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "model.json"
            self.assertEqual(
                MODULE.main(
                    [
                        "--input",
                        str(ROOT / "universes/product-development/universe.kbp.yaml"),
                        "--output",
                        str(output),
                    ]
                ),
                0,
            )
            self.assertEqual(
                json.loads(output.read_text()),
                MODULE.prepare_model(self.source, self.protocol),
            )


if __name__ == "__main__":
    unittest.main()
