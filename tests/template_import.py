"""Import and reimport the API template in an isolated Zabbix 8.0 Docker stack."""

import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = ROOT / "templates/home_assistant/home_assistant_entities.yaml"


class ZabbixAPIError(RuntimeError):
    pass


def docker(*arguments, check=True):
    result = subprocess.run(
        ["docker", *arguments], capture_output=True, text=True, timeout=240, check=False
    )
    if check and result.returncode:
        raise RuntimeError(f"Docker {arguments[0]} failed: {result.stderr}")
    return result


def api_call(url, method, params, token=None):
    headers = {"Content-Type": "application/json-rpc"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        url,
        data=json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        ).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        reply = json.load(response)
    if "error" in reply:
        raise ZabbixAPIError(f"{method}: {reply['error']}")
    return reply["result"]


def wait_for_login(url):
    deadline = time.monotonic() + 180
    last_error = None
    while time.monotonic() < deadline:
        try:
            return api_call(
                url, "user.login", {"username": "Admin", "password": "zabbix"}
            )
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ZabbixAPIError,
        ) as error:
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"Zabbix API did not become ready: {last_error}")


def import_and_check(url, token):
    source = TEMPLATE_FILE.read_text(encoding="utf-8")
    template = yaml.safe_load(source)["zabbix_export"]["templates"][0]
    rules = {
        name: {"createMissing": True, "updateExisting": True}
        for name in ("templates", "items", "discoveryRules", "triggers")
    }
    rules["template_groups"] = {"createMissing": True, "updateExisting": True}
    for attempt in range(2):
        result = api_call(
            url,
            "configuration.import",
            {"format": "yaml", "rules": rules, "source": source},
            token,
        )
        if result is not True:
            raise RuntimeError("Template import did not report success")
        print(f"Template import {attempt + 1} accepted by Zabbix")
    matches = api_call(
        url,
        "template.get",
        {"filter": {"host": template["template"]}, "output": ["templateid"]},
        token,
    )
    if len(matches) != 1:
        raise RuntimeError("Imported template is missing or duplicated")
    template_id = matches[0]["templateid"]
    items = api_call(
        url, "item.get", {"templateids": [template_id], "output": ["key_"]}, token
    )
    discovery = api_call(
        url,
        "discoveryrule.get",
        {"templateids": [template_id], "output": ["key_"]},
        token,
    )
    prototypes = api_call(
        url,
        "itemprototype.get",
        {"templateids": [template_id], "output": ["key_"]},
        token,
    )
    if {item["key_"] for item in items} != {item["key"] for item in template["items"]}:
        raise RuntimeError("Imported item keys differ from the exported template")
    if len(discovery) != len(template["discovery_rules"]):
        raise RuntimeError("Discovery rules were not imported")
    expected_prototypes = sum(
        len(rule["item_prototypes"]) for rule in template["discovery_rules"]
    )
    if len(prototypes) != expected_prototypes:
        raise RuntimeError("Item prototypes were not imported")
    print(
        f"Verified {len(items)} items, {len(discovery)} discovery rules and {len(prototypes)} prototypes"
    )


def main():
    prefix = "ha-zabbix-import-" + uuid4().hex[:10]
    database, server, web = (prefix + suffix for suffix in ("-db", "-server", "-web"))
    containers = (database, server, web)
    docker("network", "create", prefix)
    try:
        # All credentials below belong to a disposable CI-only database.
        common = (
            "-e",
            "POSTGRES_USER=zabbix",
            "-e",
            "POSTGRES_PASSWORD=ci-only-password",
            "-e",
            "POSTGRES_DB=zabbix",
        )
        docker(
            "run",
            "-d",
            "--name",
            database,
            "--network",
            prefix,
            *common,
            "postgres:16-alpine",
        )
        docker(
            "run",
            "-d",
            "--name",
            server,
            "--network",
            prefix,
            "-e",
            "DB_SERVER_HOST=" + database,
            *common,
            "zabbix/zabbix-server-pgsql:alpine-8.0-latest",
        )
        docker(
            "run",
            "-d",
            "--name",
            web,
            "--network",
            prefix,
            "-p",
            "127.0.0.1::8080",
            "-e",
            "DB_SERVER_HOST=" + database,
            "-e",
            "ZBX_SERVER_HOST=" + server,
            *common,
            "zabbix/zabbix-web-nginx-pgsql:alpine-8.0-latest",
        )
        address = docker("port", web, "8080/tcp").stdout.strip()
        url = "http://" + address + "/api_jsonrpc.php"
        token = wait_for_login(url)
        print("Zabbix API version:", api_call(url, "apiinfo.version", {}))
        import_and_check(url, token)
    except Exception:
        for name in containers:
            logs = docker("logs", "--tail", "30", name, check=False)
            print(f"--- {name} ---\n{logs.stdout}{logs.stderr}")
        raise
    finally:
        for name in reversed(containers):
            docker("rm", "-fv", name, check=False)
        cleanup = docker("network", "rm", prefix, check=False)
        if cleanup.returncode:
            print("Could not remove the test network:", cleanup.stderr)


if __name__ == "__main__":
    main()
