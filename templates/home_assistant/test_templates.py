"""Check template structure, references, regeneration, and exported preprocessing."""

import json
from pathlib import Path
import re
import subprocess
import unittest

import yaml

from build import build, NAME

ROOT = Path(__file__).resolve().parent
FILES = ("home_assistant_entities.yaml",)


class TemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = [yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))["zabbix_export"] for name in FILES]
        cls.entities = cls.exports[0]["templates"][0]

    def test_standalone_api_template(self):
        self.assertNotIn("templates", self.entities)
        for export in self.exports:
            self.assertEqual(export["version"], "8.0")

    def test_unique_identifiers_and_resolved_masters(self):
        items = self.entities["items"]
        groups = [items] + [rule["item_prototypes"] for rule in self.entities["discovery_rules"]]
        keys = [item["key"] for group in groups for item in group]
        self.assertEqual(len(keys), len(set(keys)))
        global_keys = {item["key"] for item in items}
        for group in groups:
            allowed = global_keys | {item["key"] for item in group}
            for item in group:
                if "master_item" in item:
                    self.assertIn(item["master_item"]["key"], allowed)
                    self.assertNotEqual(item["master_item"]["key"], item["key"])
        uuids = []
        def walk(node):
            if isinstance(node, dict):
                if "uuid" in node:
                    self.assertRegex(node["uuid"], r"^[0-9a-f]{32}$")
                    uuids.append(node["uuid"])
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)
        walk(self.exports[0])
        self.assertEqual(len(uuids), len(set(uuids)))
        for rule in self.entities["discovery_rules"]:
            self.assertIn(rule["master_item"]["key"], global_keys)

    def test_macro_and_trigger_references(self):
        macros = {macro["macro"] for macro in self.entities["macros"]}
        keys = {item["key"] for item in self.entities["items"]}
        keys.update(item["key"] for rule in self.entities["discovery_rules"] for item in rule["item_prototypes"])
        text = json.dumps(self.entities)
        for macro in re.findall(r"\{\$[A-Z_.]+\}", text):
            self.assertIn(macro, macros)
        for key in re.findall('/' + re.escape(NAME) + r'/([a-z_.]+(?:\[[^\]]+\])?)', text):
            self.assertIn(key, keys)
        token = next(macro for macro in self.entities["macros"] if macro["macro"] == "{$HA.TOKEN}")
        self.assertEqual(token["type"], "SECRET_TEXT")
        self.assertEqual(token["value"], "")

    def test_reproducible_export(self):
        original = [(ROOT / name).read_bytes() for name in FILES]
        build()
        self.assertEqual(original, [(ROOT / name).read_bytes() for name in FILES])

    def test_exported_preprocessing(self):
        result = subprocess.run(["node", str(ROOT / "test_preprocessing.js")],
            input=json.dumps(self.entities), encoding="utf-8", capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        print(result.stdout.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
