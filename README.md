# Zabbix Agent and Zabbix Agent 2 for Home Assistant

Monitor your Home Assistant host with Zabbix. Both apps use Zabbix's official latest stable Alpine images and support amd64/aarch64, active and passive checks, and optional TLS-PSK encryption.

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FKimax89%2FHA-Zabbix-Agent)

| App | Default passive port | Docker monitoring | Setup |
| --- | --- | --- | --- |
| ![Agent icon](zabbix_agent/icon.png) **Zabbix Agent** | 10052 | No | [Documentation](zabbix_agent/DOCS.md) |
| ![Agent 2 icon](zabbix_agent2/icon.png) **Zabbix Agent 2** | 10050 | Yes | [Documentation](zabbix_agent2/DOCS.md) |

App version: **1.0.0.2**. The app version is separate from the upstream Zabbix version. This is a community project, not an official Zabbix or Home Assistant app.

## Install

1. Use the button above, or add `https://github.com/Kimax89/HA-Zabbix-Agent` under **Settings → Apps → App store → Repositories**.
2. Install the app you want. Supervisor builds it on your device from its Dockerfile.
3. Configure your Zabbix host name and server/proxy address. Follow that app's Documentation tab for every option, PSK settings and Zabbix templates.
4. Turn off Protection mode for host process monitoring; Agent 2 also needs it for the Docker socket.
5. Start the app and check its log.

Requires Supervisor, normally Home Assistant OS. Home Assistant Container alone cannot install apps. Older Home Assistant interfaces use the term Add-ons. For development, copy an entire app folder to `/addons/<app-folder>` and reload the app store.

## Access and limitations

Host network/PID/UTS access is needed to see host interfaces, processes and hostname. Both apps run as root and retain Docker's default AppArmor profile. Agent 2's Docker socket gives extensive host access even when mounted read-only, which explains its low security rating. No extra hardware access or Core/Supervisor API roles are requested.

The host root filesystem is not generally mounted. Filesystem, OS/package and some cgroup values can describe the app container; compare them with the host and adjust your Zabbix template filters. Remote commands and custom UserParameters are not enabled. Neither app has a web interface.

## Optional extra: Home Assistant API template

[Home Assistant entities by HTTP](templates/home_assistant/README.md) is an independent **Zabbix 8.0** template for entity states, numeric readings, availability, battery levels and exposed update entities. It uses a Home Assistant token and does not require either app.

[Download the YAML](https://raw.githubusercontent.com/Kimax89/HA-Zabbix-Agent/main/templates/home_assistant/home_assistant_entities.yaml), then follow its import/setup instructions. Entity monitoring polls current states; it does not capture every event, all recorder history, backups or Supervisor diagnostics.

## Updates and backups

The maintainer chose official `alpine-latest` images so a new build can use the latest stable Alpine release. Floating tags are not reproducible: check `agent.version` after upgrading and verify compatibility with your server/templates. **Restart** does not update the image; **Rebuild** fetches a newer upstream build. A published app-version change also gives Home Assistant an update indication.

Saved options, including PSK secrets, are part of Home Assistant backups. Generated `/data/runtime` files are excluded and recreated on startup. Restore the saved options and restart the app; runtime sockets/PID files do not need restoring.

## Development and verification

Install Python 3.12+, Node.js, jq, ShellCheck and Docker. From the repository root:

```text
python -m pip install -r requirements-dev.txt
python scripts/sync_runtime.py --check
ruff check .
ruff format --check .
python tests/validate.py
python templates/home_assistant/test_templates.py
```

Edit the shared runtime in `runtime/agent-common.sh`, then run `python scripts/sync_runtime.py` to update both independent build contexts. See [runtime maintenance](runtime/README.md).

For container checks on Linux:

```text
docker build --pull --no-cache -t ha-zabbix-test zabbix_agent
sh tests/smoke.sh zabbix_agent
docker build --pull --no-cache -t ha-zabbix-test zabbix_agent2
sh tests/smoke.sh zabbix_agent2
python tests/template_import.py
```

CI checks Python/shell quality, generated copies, app metadata/translations using the official Supervisor schema, both architectures, real passive/PSK requests, negative configurations and restart/file permissions. A separate disposable Zabbix stack checks API-template import and reimport. CI does not replace a real Home Assistant OS installation/restore test. See [validation evidence](VALIDATION.md) and the [guideline/Clean Code review](REVIEW.md).

## Support and license

[Report an issue](https://github.com/Kimax89/HA-Zabbix-Agent/issues) with app/upstream versions, architecture and relevant logs. Remove PSK keys and API tokens before sharing configuration or logs. Maintainer: Klaus Kirkeby <kimax@wattup.eu>.

Repository code uses [GNU GPL v3](LICENSE). Official Zabbix binaries retain their upstream AGPL v3 license; other image packages retain their own licenses. Zabbix trademarks belong to Zabbix SIA. See [icon source/attribution](assets/icons/README.md).
