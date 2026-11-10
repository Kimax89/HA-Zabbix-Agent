# Zabbix Agent and Zabbix Agent 2 for Home Assistant

Repository: https://github.com/Kimax89/HA-Zabbix-Agent

Two separate Home Assistant apps, app version **0.0.2.2**:

| App | Official base image | Default passive check port | Docker plugin |
| --- | --- | --- | --- |
| Zabbix Agent | `zabbix/zabbix-agent:alpine-latest` | 10052 | No |
| Zabbix Agent 2 | `zabbix/zabbix-agent2:alpine-latest` | 10050 | Yes |

Both use the latest stable Alpine variant rather than `alpine-trunk`. The actual Zabbix version depends on the image published by Zabbix at build time. Docker Hub descriptions were not mutually consistent when checked on November 10, 2026, so this project does not claim a specific patch version for both images. Check the agent startup log or `agent.version` for the installed version.

## Install from GitHub

1. Upload `repository.yaml`, both app folders, and the remaining project files to the root of the public repository. Upload the extracted files, not the ZIP archive. Include `.github`, which contains automated build tests.
2. In Home Assistant, open **Settings → Apps → App store → ⋮ → Repositories**. Older interfaces use the term Add-ons.
3. Add `https://github.com/Kimax89/HA-Zabbix-Agent` and install the app you want. Home Assistant builds it locally and needs access to Docker images and Alpine packages.
4. Turn off **Protection mode** to access host processes. Agent 2 also requires this for the Docker socket.
5. Configure and start the app. Check its log.

Supervisor and the app store are required, normally through Home Assistant OS. Home Assistant Container alone does not support app installation. For local installation, copy the folders to `/addons/zabbix_agent` and `/addons/zabbix_agent2` instead.

## Configuration

Example for Agent 2:

```yaml
hostname: homeassistant
server_active: "192.168.1.20:10051"
server_passive: ""
listen_port: 10050
tls_psk_identity: ""
tls_psk: ""
```

Replace the server address. The classic Agent defaults to `hostname: homeassistant-agent` and `listen_port: 10052`. If both apps run at the same time, use different Zabbix hostnames and passive listening ports.

- `hostname`: must exactly match the hostname in Zabbix, including letter case.
- `server_active`: server/proxy address with an optional port, normally 10051. Leave empty to disable active checks.
- `server_passive`: allowed server/proxy addresses or networks, separated by commas and without ports. Leave empty to disable passive checks.
- `listen_port`: the host TCP port for passive checks. It must be available and match the agent interface configured on the Zabbix host. Ignored when passive checks are disabled.
- `tls_psk_identity` and `tls_psk`: fill in both to enable encryption. The key must contain 32-512 hexadecimal characters and have an even length. Configure the same key, identity, and PSK connection types in Zabbix. When PSK is enabled, only PSK connections are allowed. The key is included in app configuration and backups. Without PSK, traffic is unencrypted; use a trusted network or VPN.

At least one server field must be filled in. Link a Linux template using the selected check type. Agent 2 can also use the Zabbix Docker template; passive Docker items require passive checks. Match templates to your server and agent versions.

## Access and measurement limitations

Both apps share the host PID, network, and hostname namespaces and run as root. They can see host processes and network interfaces. Compare CPU and memory measurements against the host because cgroups may affect some values.

Only Agent 2 receives access to the Docker socket and its built-in Docker plugin for container discovery, status, and statistics. The Docker socket provides extensive access to the host, even when mounted read-only. The classic Agent does not include Agent 2's Docker plugin.

The host root filesystem and SMART devices are not generally mounted. Filesystem, OS, and package information may describe the app container. Review Linux template discovery and unsupported items. Remote commands and custom UserParameters are not enabled. Neither app has a web interface or uses a Home Assistant API token.

## Updates and testing

`alpine-latest` is fetched during a new build. Restarting does not update the agent. Select **Rebuild** to fetch a newer upstream image, then verify the installed version in the log. For builds outside Home Assistant, use `docker build --pull --no-cache`. New app versions in the repository produce an update notification in Home Assistant; upstream image changes alone do not.

The GitHub Actions workflow is configured to build both apps on amd64 and arm64 and run `tests/smoke.sh`. The tests check active/passive startup, actual passive listening ports, custom ports, PSK configuration, and the expected rejection messages for invalid configuration. It does not replace Home Assistant integration testing. For local metadata and input-validation checks, install Python 3, PyYAML and jq, then run `python3 tests/validate.py`. See `VALIDATION.md` for checks actually performed. Both apps are experimental.

## Sources

- https://github.com/zabbix/zabbix-docker
- https://hub.docker.com/r/zabbix/zabbix-agent/
- https://hub.docker.com/r/zabbix/zabbix-agent2/
- https://developers.home-assistant.io/docs/apps/configuration/

Zabbix 7.0 and later use AGPL-3.0. Preserve upstream license notices when distributing. These files have been prepared locally and have not been uploaded to GitHub from this environment.
