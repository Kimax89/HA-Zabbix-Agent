# Home Assistant guideline and Clean Code review

Reviewed November 19, 2026. App version **1.0.0.2**. Scope: both apps, runtime/build scripts, CI, documentation, icons, and the optional Zabbix API template. References are the official Home Assistant app contributor documentation listed below.

## Guideline coverage

| Area | Result |
| --- | --- |
| Repository structure | Valid `repository.yaml`; one independently buildable folder per app; stable repository URL and app slugs retained. |
| App configuration | JSON is an accepted format. Stable stage, four-part app version, both supported 64-bit architectures, explicit init and AppArmor settings. Existing options and ports remain compatible. |
| Options and secrets | All six options have schema entries, English UI labels, descriptions, defaults, examples and troubleshooting. PSK remains a password field. Control characters and invalid values fail before runtime files are written. |
| Presentation | Each app has its own README, complete DOCS, current changelog and square PNG icon. Optional wide logos are not needed. The 256px icons use a permitted square size. |
| Runtime and shutdown | Official Zabbix Alpine images are used directly. No S6 dependency; `init: true` is appropriate. Startup uses `exec`, logs go to the console, and SIGTERM/shutdown is exercised by CI. |
| Privileges | Host network, PID and UTS access are required for the advertised host metrics and explained in each app's docs. Only Agent 2 requests Docker API access. No added capabilities, hardware/device mounts, Core API role or elevated Supervisor role are requested. |
| Protection mode | Users are told why host process/Docker monitoring requires it off. Agent 2 fails clearly without the socket. Startup does not attempt to turn protection off automatically. |
| AppArmor | Docker's default profile remains enabled. A custom profile is recommended by the guide but optional. An unverified custom profile has not been installed: it must first be audited against real host metrics on Home Assistant OS. |
| Security rating | Host monitoring necessarily lowers the rating; Docker API access makes Agent 2's rating low. No unrelated privileges or artificial ingress/login have been added to inflate it. |
| Storage and backups | Generated configuration, socket, PID and PSK files are root-only and regenerated at startup. `runtime` is excluded from backups; saved user options, including their PSK, remain part of backups. |
| Build context | `.dockerignore` restricts each app's image inputs to its Dockerfile and startup files. Source/version labels identify the wrapper; upstream license information is retained. Supervisor supplies its own `io.hass.*` labels during installation. |
| Base image policy | The guide recommends pinned tags for reproducibility. The maintainer explicitly chose the latest stable official Alpine build, so `alpine-latest` is intentionally retained and its update/reproducibility implications are documented. |
| Distribution | Building on the device is a supported method and remains in use. Pre-built/signed images are a recommendation, not a requirement; no registry or signing credentials are configured. Switching distribution would require testing public registry access and a separate release workflow. |
| S6/Bashio | Not used: these images run one foreground process and need host PID access. The guide explicitly allows other base images and ordinary JSON parsing. |
| Ingress, API roles and service discovery | Not applicable: no web UI, user login, Supervisor/Core API calls, MQTT or database service is exposed. Unused Supervisor token variables are removed before the agent starts. |
| Licensing/support | Existing GPL v3 repository license is preserved. Docs distinguish wrapper code, Zabbix's AGPL v3 binaries, package licenses and trademarks; issue reporting instructions exclude secrets. |
| Validation | Local unit/lint checks plus CI on amd64/arm64; official Supervisor configuration/translation schema validation; real passive/PSK protocol tests; isolated Zabbix API template import/reimport. See VALIDATION.md for execution results and remaining live checks. |

This is a review of applicable requirements and recommendations, not a Home Assistant certification. Real-device installation, backup/restore, AppArmor audit and measurement accuracy cannot be certified by plain Docker tests alone.

## Clean Code changes

- Shared validation, PSK handling and configuration writing have one maintained source in `runtime/agent-common.sh`. Generated copies are necessary because Supervisor uses an independent Docker build context per app; CI verifies byte-for-byte synchronization.
- Small app entrypoints contain only their own agent settings and startup sequence. There is no generic plugin framework or change to external option names, slugs or Zabbix keys.
- Validation precedes side effects. Functions that load options, prepare storage and write settings state their actions. Temporary configuration files have an explicit cleanup trap and replace the completed file only after successful writing.
- The API template generator is split into named item/discovery/macro builders. Generated UUIDs, item keys and export content are unchanged. Tests regenerate into a temporary project-local directory instead of rewriting source artifacts.
- Python formatting/import checks and shell analysis are part of CI. Tests cover behavior: invalid input, secret file modes, protocol responses, TLS rejection, restart, IPv4/IPv6 listeners and real template imports, rather than only matching implementation text.
- Icon rendering and synthetic JavaScript fixtures were reviewed and formatted where appropriate. Existing artwork and the API template's monitored scope are preserved.
- Historical validation claims were replaced with current evidence and explicit limits. Optional features have not been introduced simply to imitate an example app.

## Official references reviewed

- [Apps overview](https://contributors.home-assistant.io/apps/)
- [App configuration](https://contributors.home-assistant.io/apps/reference/configuration/)
- [App files and translation format](https://contributors.home-assistant.io/apps/reference/files/)
- [Runtime environment](https://contributors.home-assistant.io/apps/reference/environment/)
- [Security rating](https://contributors.home-assistant.io/apps/reference/security-rating/)
- [Build the container image](https://contributors.home-assistant.io/apps/guides/dockerfile/)
- [Run services with S6](https://contributors.home-assistant.io/apps/guides/s6-overlay/)
- [Add options](https://contributors.home-assistant.io/apps/guides/options/)
- [Access hardware and the host](https://contributors.home-assistant.io/apps/guides/hardware/)
- [Talk to Home Assistant and Supervisor](https://contributors.home-assistant.io/apps/guides/communication/)
- [Ingress](https://contributors.home-assistant.io/apps/guides/ingress/)
- [Services and discovery](https://contributors.home-assistant.io/apps/guides/services-discovery/)
- [Test your app](https://contributors.home-assistant.io/apps/guides/testing/)
- [Secure your app](https://contributors.home-assistant.io/apps/guides/security/)
- [Present your app](https://contributors.home-assistant.io/apps/guides/presentation/)
- [Publish your app](https://contributors.home-assistant.io/apps/guides/publishing/)
- [Create/share a repository](https://contributors.home-assistant.io/apps/guides/repository/)
