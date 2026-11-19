"""Copy the shared runtime into each independent Home Assistant build context."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime/agent-common.sh"
APPS = ("zabbix_agent", "zabbix_agent2")


def write_runtime_copies():
    expected = SOURCE.read_bytes()
    for app in APPS:
        (ROOT / app / "runtime.sh").write_bytes(expected)


def check_runtime_copies():
    expected = SOURCE.read_bytes()
    stale = []
    for app in APPS:
        destination = ROOT / app / "runtime.sh"
        if not destination.is_file() or destination.read_bytes() != expected:
            stale.append(str(destination.relative_to(ROOT)))
    if stale:
        raise SystemExit(
            "Run python scripts/sync_runtime.py; stale files: " + ", ".join(stale)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail if build-context copies are stale"
    )
    if parser.parse_args().check:
        check_runtime_copies()
    else:
        write_runtime_copies()
