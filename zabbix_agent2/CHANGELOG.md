# 0.0.2.2

- Fix CI cleanup of root-owned container data using named Docker volumes.
- Check actual passive listeners and custom ports in smoke tests.
- Check expected failure messages to prevent false-positive test results.
- Add bounded readiness checks, failure diagnostics, and a CI time limit.
- Add executable metadata, YAML, and startup-input regression checks.
- No changes to production agent behavior.

# 0.0.2.1

- Translate all app descriptions and documentation into English.
- No changes to agent behavior.

# 0.0.2.0

- Two separate apps for Zabbix Agent and Agent 2.
- Official alpine-latest images for the latest stable Alpine release.
- Configurable passive listening ports for running both apps together.
- Active/passive checks and optional TLS-PSK.
- GitHub build tests for amd64 and aarch64.
