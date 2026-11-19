"""Validate repository files and exercise the actual jq filters used at startup.

Run with Python 3, PyYAML and jq. Does not require Docker.
"""

import copy
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APPS = ("zabbix_agent", "zabbix_agent2")
JQ = os.environ.get("JQ") or shutil.which("jq") or str(ROOT / ".tools/jq.exe")


def run_filter(expression, value, *, raw=False):
    command = [JQ, "-Rse" if raw else "-e", expression]
    source = value if raw else json.dumps(value)
    return subprocess.run(
        command,
        input=source,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        check=False,
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
                self.assertRegex(
                    config["version"], r"^(0|[1-9]\d*)(\.(0|[1-9]\d*)){3}$"
                )
                self.assertEqual(set(config["options"]), set(config["schema"]))
                self.assertEqual(set(config["arch"]), {"amd64", "aarch64"})
                self.assertTrue(config["host_pid"])
                self.assertTrue(config["host_network"])
                self.assertEqual(bool(config.get("docker_api")), app == "zabbix_agent2")
                self.assertTrue(config["init"])
                self.assertTrue(config["apparmor"])
                self.assertEqual(config["stage"], "stable")
                self.assertEqual(config["schema"]["tls_psk"], "password")
                self.assertIn("runtime/**", config["backup_exclude"])
                image = "zabbix-agent2" if app == "zabbix_agent2" else "zabbix-agent"
                self.assertEqual(
                    (folder / "Dockerfile").read_text().splitlines()[0],
                    f"FROM zabbix/{image}:alpine-latest",
                )
                for filename in (
                    "run.sh",
                    "runtime.sh",
                    "README.md",
                    "DOCS.md",
                    "CHANGELOG.md",
                ):
                    self.assertTrue((folder / filename).is_file())
                self.assertIn(config["version"], (folder / "CHANGELOG.md").read_text())
        self.assertEqual(len({c["version"] for c in configs}), 1)
        self.assertEqual(len({c["options"]["listen_port"] for c in configs}), 2)

    def test_app_presentation_and_shared_runtime(self):
        expected_runtime = (ROOT / "runtime/agent-common.sh").read_bytes()
        for app in APPS:
            folder = ROOT / app
            with self.subTest(app=app):
                self.assertEqual((folder / "runtime.sh").read_bytes(), expected_runtime)
                config = json.loads((folder / "config.json").read_text())
                labels = yaml.safe_load(
                    (folder / "translations/en.yaml").read_text(encoding="utf-8")
                )["configuration"]
                self.assertEqual(set(labels), set(config["schema"]))
                docs = (folder / "DOCS.md").read_text(encoding="utf-8")
                for option in config["schema"]:
                    self.assertTrue(labels[option]["name"])
                    self.assertTrue(labels[option]["description"])
                    self.assertIn(f"`{option}`", docs)
                with Image.open(folder / "icon.png") as icon:
                    self.assertEqual(icon.format, "PNG")
                    self.assertEqual(icon.width, icon.height)
                    self.assertGreaterEqual(icon.width, 128)
                    icon.verify()

    def test_repository_and_workflow_yaml(self):
        repository = yaml.safe_load((ROOT / "repository.yaml").read_text())
        self.assertEqual(
            repository["url"], "https://github.com/Kimax89/HA-Zabbix-Agent"
        )
        # BaseLoader preserves GitHub's `on` key instead of applying YAML 1.1 booleans.
        workflow = yaml.load(
            (ROOT / ".github/workflows/build.yaml").read_text(), Loader=yaml.BaseLoader
        )
        self.assertIn("push", workflow["on"])
        self.assertEqual(
            set(workflow["jobs"]["test"]["strategy"]["matrix"]["app"]), set(APPS)
        )
        self.assertIn("timeout-minutes", workflow["jobs"]["test"])

    def test_shell_files_use_lf_without_bom(self):
        scripts = [ROOT / "runtime/agent-common.sh", ROOT / "tests/smoke.sh"]
        scripts.extend(
            ROOT / app / name for app in APPS for name in ("run.sh", "runtime.sh")
        )
        for script in scripts:
            with self.subTest(script=script.name):
                data = script.read_bytes()
                self.assertTrue(data.startswith(b"#!/bin/sh\n"))
                self.assertNotIn(b"\r", data)


class StartupValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filters = {}
        for app in APPS:
            script = (ROOT / app / "runtime.sh").read_text()
            cls.filters[app] = {
                "options": re.search(
                    r"^OPTIONS_FILTER='([^']+)'", script, re.MULTILINE
                ).group(1),
                "port": re.search(
                    r"^PORT_FILTER='([^']+)'", script, re.MULTILINE
                ).group(1),
                "psk": re.search(r"^PSK_FILTER='([^']+)'", script, re.MULTILINE).group(
                    1
                ),
            }

    def test_control_characters_cannot_inject_agent_directives(self):
        for app, filters in self.filters.items():
            options = json.loads((ROOT / app / "config.json").read_text())["options"]
            self.assertEqual(run_filter(filters["options"], options).returncode, 0)
            for field in (
                "hostname",
                "server_active",
                "server_passive",
                "tls_psk_identity",
                "tls_psk",
            ):
                for value in (
                    "safe\nServer=0.0.0.0/0",
                    "safe\rvalue",
                    "safe\x00value",
                    "safe\tvalue",
                    "safe\x7fvalue",
                    None,
                    123,
                    False,
                ):
                    with self.subTest(app=app, field=field, value=repr(value)):
                        invalid = copy.deepcopy(options)
                        invalid[field] = value
                        self.assertNotEqual(
                            run_filter(filters["options"], invalid).returncode, 0
                        )

    def test_listen_port_boundaries(self):
        for app, filters in self.filters.items():
            for port in (1, 10050, 65535):
                with self.subTest(app=app, port=port):
                    self.assertEqual(
                        run_filter(filters["port"], {"listen_port": port}).returncode, 0
                    )
            for port in (0, -1, 65536, 1.5, "10050", None, True):
                with self.subTest(app=app, port=port):
                    self.assertNotEqual(
                        run_filter(filters["port"], {"listen_port": port}).returncode, 0
                    )

    def test_psk_boundaries(self):
        for app, filters in self.filters.items():
            for key in ("ab" * 16, "AB" * 256):
                with self.subTest(app=app, length=len(key)):
                    self.assertEqual(
                        run_filter(filters["psk"], key, raw=True).returncode, 0
                    )
            for key in ("", "a" * 31, "a" * 33, "a" * 514, "z" * 32, "ab" * 16 + "\n"):
                with self.subTest(app=app, key=repr(key[:40])):
                    self.assertNotEqual(
                        run_filter(filters["psk"], key, raw=True).returncode, 0
                    )


class ListenerValidationTests(unittest.TestCase):
    def test_ipv4_ipv6_and_closed_ports(self):
        script = (ROOT / "tests/smoke.sh").read_text()
        expression = re.search(r"awk -v port=\"\$test_port\" '([^']+)'", script).group(
            1
        )
        awk = shutil.which("awk")
        command = [awk] if awk else [str(ROOT / ".tools/busybox.exe"), "awk"]
        ipv4 = "0: 00000000:2742 00000000:0000 0A 00000000:00000000\n"
        ipv6 = "0: 00000000000000000000000000000000:2742 00000000000000000000000000000000:0000 0A 00000000:00000000\n"
        for sockets, port, expected in (
            (ipv4, 10050, "open"),
            (ipv6, 10050, "open"),
            (ipv4 + ipv6, 10050, "open"),
            (ipv6, 10052, "closed"),
            (ipv6.replace(":2742", ":2744"), 10052, "open"),
            (ipv6.replace(" 0A ", " 01 "), 10050, "closed"),
            ("sl local_address rem_address st\n", 10050, "closed"),
        ):
            with self.subTest(port=port, sockets=sockets, expected=expected):
                result = subprocess.run(
                    command + ["-v", f"port={port}", expression],
                    input=sockets,
                    text=True,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
