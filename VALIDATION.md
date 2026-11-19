# Validation - November 19, 2026

Reviewed app version: **1.0.0.2**. Scope and guideline decisions are recorded in [REVIEW.md](REVIEW.md).

## Current local results

- Eight metadata/input/listener test methods pass, including both independent app build contexts, synchronized runtime copies, complete English labels, documented options, valid PNG icons, PSK/port boundaries and injection rejection.
- Five API-template structure/preprocessing tests pass; the exported JavaScript passes 38 assertions against synthetic Home Assistant data.
- Ruff code/import checks and formatting checks pass.
- ShellCheck analysis and shell syntax checks pass for both entrypoints, the shared runtime and the smoke test.
- The API template generator produces the same export after refactoring and now regenerates into a temporary project-local directory during tests.

Local tools: Python 3.12.14, jq 1.8.1, PyYAML 6.0.3, Pillow, Ruff 0.14.5, ShellCheck 0.11.0 and portable BusyBox. GitHub uses the pinned development requirements and its Linux shell tools. No Docker daemon is available in the local Windows workspace.

## CI coverage for this candidate

The updated workflow is configured to run:

1. Python/shell checks and shared-runtime synchronization.
2. Metadata and English labels through the official Home Assistant Supervisor schemas.
3. Both apps on amd64 and arm64, built from official latest stable Alpine images.
4. Active-only startup without a listener; passive requests and custom ports; correct PSK requests; rejection of incorrect PSK and unencrypted requests; private runtime/config/key modes; repair of older file modes after restart; expected validation failures before runtime files are created; graceful stop.
5. Import and reimport of the API template through a disposable Zabbix 8.0 API, checking actual items, discovery rules and prototypes.

Execution results for this candidate will be recorded after the workflow completes. Earlier version 1.0.0.1 passed all four image/runtime jobs in [run 44419270736](https://github.com/Kimax89/HA-Zabbix-Agent/actions/runs/44419270736). The earlier Agent 2 false negatives were traced to IPv4-only socket inspection and fixed; the current tests inspect both IPv4 and IPv6.

## Real-installation checks still required

Plain Docker/schema checks are not a full Home Assistant OS test. These checks require the user's actual environment:

- App-store installation/update, Protection mode behavior and the Docker socket mount on Supervisor.
- Real active communication with a configured Zabbix server/proxy and its templates.
- Accuracy of host CPU, memory, process, network and filesystem measurements versus container/cgroup views.
- Home Assistant backup/restore and restart after a host reboot.
- Real Home Assistant API credentials, entity permissions, discovery scale, TLS certificates and resulting alerts/notifications.
- Custom AppArmor policy auditing, if a dedicated policy is introduced later.

No full-device certification or confirmation of measurements in the user's installation is claimed.

## Reproduce

See the commands in the repository README. `tests/supervisor_schema.py` must run inside the official Supervisor image; `tests/template_import.py` requires Docker and creates/removes its own isolated test containers and network. Never use production credentials for these tests.
