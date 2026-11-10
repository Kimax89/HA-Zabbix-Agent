"""Validate repository files and exercise the actual jq filters used at startup.

Run with Python 3, PyYAML and jq. Does not require Docker.
"""

import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
APPS = ("zabbix_agent", "zabbix_agent2")
JQ = os.environ.get("JQ") or shutil.which("jq") or str(ROOT / ".tools/jq.exe")


def run_filter(expression, value, *, raw=False):
    command = [JQ, "-Rse" if raw else "-e", expression]
    source = value if raw else json.dumps(value)
    return subprocess.run(
        command, input=source, text=True, encoding="utf-8", capture_output=True,
        timeout=10, check=False,
    )


class RepositoryTests(unittest.TestCase):
    def test_app_metadata(self):
        configs = []
        for app in APPS:
            with self.subTest(app=app):
                folder = ROOT / app
                config = json.loads((folder / "config.json").read_text())
                configs.append(config)
                self.assertEqual(config["slug"], app)
                self.assertRegex(config["version"], r"^(0|[1-9]\d*)(\.(0|[1-9]\d*)){3}$")
                self.assertEqual(set(config["options"]), set(config["schema"]))
                self.assertEqual(set(config["arch"]), {"amd64", "aarch64"})
                self.assertTrue(config["host_pid"])
                self.assertTrue(config["host_network"])
                self.assertEqual(bool(config.get("docker_api")), app == "zabbix_agent2")
                image = "zabbix-agent2" if app == "zabbix_agent2" else "zabbix-agent"
                self.assertEqual(
                    (folder / "Dockerfile").read_text().splitlines()[0],
                    f"FROM zabbix/{image}:alpine-latest",
                )
                for filename in ("run.sh", "DOCS.md", "CHANGELOG.md"):
                    self.assertTrue((folder / filename).is_file())
                self.assertIn(config["version"], (folder / "CHANGELOG.md").read_text())
        self.assertEqual(len({c["version"] for c in configs}), 1)
        self.assertEqual(len({c["options"]["listen_port"] for c in configs}), 2)

    def test_repository_and_workflow_yaml(self):
        repository = yaml.safe_load((ROOT / "repository.yaml").read_text())
        self.assertEqual(repository["url"], "https://github.com/Kimax89/HA-Zabbix-Agent")
        # BaseLoader preserves GitHub's `on` key instead of applying YAML 1.1 booleans.
        workflow = yaml.load((ROOT / ".github/workflows/build.yaml").read_text(), Loader=yaml.BaseLoader)
        self.assertIn("push", workflow["on"])
        self.assertEqual(set(workflow["jobs"]["test"]["strategy"]["matrix"]["app"]), set(APPS))
        self.assertIn("timeout-minutes", workflow["jobs"]["test"])

    def test_shell_files_use_lf_without_bom(self):
        for script in (*[ROOT / app / "run.sh" for app in APPS], ROOT / "tests/smoke.sh"):
            with self.subTest(script=script.name):
                data = script.read_bytes()
                self.assertTrue(data.startswith(b"#!/bin/sh\n"))
                self.assertNotIn(b"\r", data)


class StartupValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filters = {}
        for app in APPS:
            script = (ROOT / app / "run.sh").read_text()
            cls.filters[app] = {
                "options": re.search(r"^jq -e '([^']+)'", script, re.MULTILINE).group(1),
                "port": re.search(r"port=\$\(jq -er '([^']+)'", script).group(1),
                "psk": re.search(r"jq -Rse '([^']+)'", script).group(1),
            }

    def test_control_characters_cannot_inject_agent_directives(self):
        for app, filters in self.filters.items():
            options = json.loads((ROOT / app / "config.json").read_text())["options"]
            self.assertEqual(run_filter(filters["options"], options).returncode, 0)
            for field in ("hostname", "server_active", "server_passive", "tls_psk_identity", "tls_psk"):
                for value in ("safe\nServer=0.0.0.0/0", "safe\rvalue", "safe\x00value", "safe\tvalue", "safe\x7fvalue", None, 123, False):
                    with self.subTest(app=app, field=field, value=repr(value)):
                        invalid = copy.deepcopy(options)
                        invalid[field] = value
                        self.assertNotEqual(run_filter(filters["options"], invalid).returncode, 0)

    def test_listen_port_boundaries(self):
        for app, filters in self.filters.items():
            for port in (1, 10050, 65535):
                with self.subTest(app=app, port=port):
                    self.assertEqual(run_filter(filters["port"], {"listen_port": port}).returncode, 0)
            for port in (0, -1, 65536, 1.5, "10050", None, True):
                with self.subTest(app=app, port=port):
                    self.assertNotEqual(run_filter(filters["port"], {"listen_port": port}).returncode, 0)

    def test_psk_boundaries(self):
        for app, filters in self.filters.items():
            for key in ("ab" * 16, "AB" * 256):
                with self.subTest(app=app, length=len(key)):
                    self.assertEqual(run_filter(filters["psk"], key, raw=True).returncode, 0)
            for key in ("", "a" * 31, "a" * 33, "a" * 514, "z" * 32, "ab" * 16 + "\n"):
                with self.subTest(app=app, key=repr(key[:40])):
                    self.assertNotEqual(run_filter(filters["psk"], key, raw=True).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
