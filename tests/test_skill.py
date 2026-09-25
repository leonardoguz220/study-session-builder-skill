"""Pruebas de comportamiento; ejecutar: python -m unittest discover -s tests -v."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".codex/skills/study-session-builder"
sys.path.insert(0, str(SKILL / "scripts"))
from build_schedule import build_schedule, render_plan
from validate_input import InputError, load_rules, read_json, validate_data


class StudySkillTests(unittest.TestCase):
    def setUp(self):
        self.today = date.today()
        self.data = {"subject": "Redes", "exam_date": (self.today + timedelta(days=5)).isoformat(),
                     "topics": ["TLS", "DNS", "HTTP", "Balanceo"],
                     "priority_topics": ["TLS", "Balanceo"],
                     "availability": {(self.today + timedelta(days=i)).isoformat(): m
                                      for i, m in enumerate([120, 90, 180, 120, 120])},
                     "max_session_minutes": 50}

    def invalid(self, **changes):
        with self.assertRaises(InputError):
            validate_data({**self.data, **changes})

    def test_valid_input(self):
        self.assertEqual(validate_data(self.data), self.data)

    def test_unknown_priority(self):
        self.invalid(priority_topics=["Otro"])

    def test_negative_availability(self):
        self.invalid(availability={self.today.isoformat(): -10})

    def test_time_conservation(self):
        plan = build_schedule(self.data)
        self.assertEqual(plan["content_minutes"] + plan["review_minutes"] + plan["break_minutes"], 630)
        for day in plan["days"]:
            self.assertEqual(sum(s["minutes"] for s in day["sessions"]) + day["break_minutes"],
                             self.data["availability"][day["date"]])
            for session in day["sessions"]:
                self.assertEqual(sum(a["minutes"] for a in session["activities"]), session["minutes"])

    def test_priority_receives_more_time(self):
        plan = build_schedule(self.data)
        self.assertGreater(plan["topic_minutes"]["TLS"], plan["topic_minutes"]["DNS"])

    def test_session_limit_across_budgets(self):
        for budget in range(1, 1441):
            for maximum in (20, 50, 120):
                with self.subTest(budget=budget, maximum=maximum):
                    plan = build_schedule({**self.data, "availability": {self.today.isoformat(): budget},
                                           "max_session_minutes": maximum})
                    sessions = plan["days"][0]["sessions"]
                    self.assertTrue(all(0 < s["minutes"] <= maximum for s in sessions))
                    self.assertEqual(sum(s["minutes"] for s in sessions) + plan["break_minutes"], budget)

    def test_review_is_in_schedule(self):
        plan = build_schedule(self.data)
        actual = sum(a["minutes"] for d in plan["days"] for s in d["sessions"]
                     for a in s["activities"] if a["kind"] == "review")
        self.assertEqual(actual, 106)

    def test_no_priority_is_balanced(self):
        data = copy.deepcopy(self.data)
        del data["priority_topics"]
        values = list(build_schedule(data)["topic_minutes"].values())
        self.assertLessEqual(max(values) - min(values), 1)

    def test_empty_fields(self):
        for field, value in [("subject", " "), ("topics", []), ("availability", {})]:
            with self.subTest(field=field):
                self.invalid(**{field: value})

    def test_dates_invalid_today_past(self):
        for value in ["2026-02-30", "no-fecha", "20260930", self.today.isoformat(),
                      (self.today - timedelta(days=1)).isoformat()]:
            with self.subTest(value=value):
                self.invalid(exam_date=value)

    def test_duplicate_topics(self):
        self.invalid(topics=["TLS", " tls "])

    def test_availability_dates(self):
        for day in [self.today - timedelta(days=1), self.today + timedelta(days=5),
                    self.today + timedelta(days=6)]:
            with self.subTest(day=day):
                self.invalid(availability={day.isoformat(): 50})

    def test_minutes_types_and_bounds(self):
        for minutes in [0, -1, True, 1.5, "50", 1441]:
            with self.subTest(minutes=minutes):
                self.invalid(availability={self.today.isoformat(): minutes})
        for maximum in [0, 19, 121, True, 50.5, "50"]:
            with self.subTest(maximum=maximum):
                self.invalid(max_session_minutes=maximum)

    def test_maximum_default(self):
        data = copy.deepcopy(self.data)
        del data["max_session_minutes"]
        self.assertEqual(validate_data(data)["max_session_minutes"], 50)

    def test_scarce_time_and_zero_topic_warning(self):
        plan = build_schedule({**self.data, "availability": {self.today.isoformat(): 1}})
        self.assertEqual(plan["content_minutes"], 1)
        self.assertEqual(plan["review_minutes"], 0)
        self.assertEqual(len(plan["warnings"]), 3)

    def test_unknown_and_missing_fields(self):
        self.invalid(extra="no")
        with self.assertRaises(InputError):
            validate_data({})

    def test_wrong_container_types(self):
        for data in [[], None, 2, "texto"]:
            with self.assertRaises(InputError):
                validate_data(data)
        for field, value in [("topics", "TLS"), ("priority_topics", None), ("availability", [])]:
            self.invalid(**{field: value})

    def test_input_not_mutated(self):
        original = copy.deepcopy(self.data)
        build_schedule(self.data)
        self.assertEqual(self.data, original)

    def test_rules_are_used(self):
        rules = load_rules()
        rules.update(review_ratio=0.3, break_minutes=5, priority_weight=3.0)
        plan = build_schedule(self.data, rules)
        self.assertEqual(plan["break_minutes"], 50)
        self.assertEqual(plan["review_minutes"], 174)
        self.assertGreater(plan["topic_minutes"]["TLS"], 2 * plan["topic_minutes"]["DNS"])

    def test_template_really_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "template.md"
            path.write_text("MARCADOR PERSONALIZADO\n" + (SKILL / "assets/study-plan-template.md").read_text(),
                            encoding="utf-8")
            text = render_plan(build_schedule(self.data), path)
            self.assertTrue(text.startswith("MARCADOR PERSONALIZADO"))
            self.assertNotIn("{{", text)
            path.write_text("{{UNKNOWN}}", encoding="utf-8")
            with self.assertRaises(InputError):
                render_plan(build_schedule(self.data), path)

    def test_file_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            with self.assertRaises(InputError):
                read_json(path)
            for text in ['{"subject":', '{"x": 1, "x": 2}']:
                path.write_text(text)
                with self.assertRaises(InputError):
                    read_json(path)

    def test_invalid_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            for changes in [{"review_ratio": 1}, {"break_minutes": 20},
                            {"normal_weight": 3}, {"break_minutes": 1.5}, {"priority_weight": True}]:
                path.write_text(json.dumps({**load_rules(), **changes}))
                with self.assertRaises(InputError):
                    load_rules(path)

    def test_cli_invalid_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "input.json", Path(tmp) / "plan.md"
            source.write_text(json.dumps({**self.data, "priority_topics": ["Otro"]}))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/build_schedule.py"),
                                     str(source), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("[ERROR]", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_success_from_another_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            source.write_text(json.dumps(self.data))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/build_schedule.py"), str(source)],
                                    cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(tmp) / "output/study-plan.md").is_file())

    def test_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(SKILL / "scripts/demo.py")],
                                    cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DEMO COMPLETA", result.stdout)
            self.assertFalse((Path(tmp) / "output/invalid-plan.md").exists())


if __name__ == "__main__":
    unittest.main()
