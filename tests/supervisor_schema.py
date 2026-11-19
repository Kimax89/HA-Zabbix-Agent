"""Run inside the official Supervisor image to validate app metadata and labels."""

import json
import sys
from pathlib import Path

import yaml


def main():
    # The official image keeps its installed Supervisor package here.
    sys.path.insert(0, "/usr/src")
    from supervisor.apps.validate import (
        SCHEMA_APP_CONFIG_QUIET,
        SCHEMA_APP_TRANSLATIONS,
    )

    root = Path(__file__).resolve().parents[1]
    for app in ("zabbix_agent", "zabbix_agent2"):
        config = json.loads((root / app / "config.json").read_text())
        SCHEMA_APP_CONFIG_QUIET(config)
        labels = yaml.safe_load((root / app / "translations/en.yaml").read_text())
        SCHEMA_APP_TRANSLATIONS(labels)
        print(f"Supervisor schema accepted {app} configuration and English labels")


if __name__ == "__main__":
    main()
