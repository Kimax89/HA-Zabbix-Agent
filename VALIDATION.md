# Validation - November 10, 2026

## Completed locally

- Checked JSON parsing, unique slugs, version format, option/schema consistency, and different default ports for both apps.
- Checked Dockerfiles for the correct official alpine-latest images.
- Manually reviewed agent-specific configuration: Agent uses AllowRoot, PidFile, and StartAgents=0 without passive checks; Agent 2 uses ControlSocket and the Docker plugin. PSK values and control characters are validated before startup. User input is not evaluated as shell code.
- Shell files use LF line endings; .gitattributes preserves this format.
- Translated app descriptions, setup documentation, changelogs, and this validation report into English in app version 0.0.2.1. Runtime behavior is unchanged by the translation.

## Not performed

Docker is unavailable locally: builds, shell/jq execution, agent startup, Home Assistant schema validation, TLS connections, and real measurements have not been tested. GitHub Actions has been prepared but has not been run or uploaded from this environment. Passing CI would not replace Supervisor and Zabbix integration testing.

## Reproducible container tests

On Linux with Docker and jq, run from the repository root:

    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent
    sh tests/smoke.sh zabbix_agent
    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent2
    sh tests/smoke.sh zabbix_agent2

The GitHub workflow is configured to run the same tests on amd64 and arm64. The tests cover active/passive checks, PSK startup, agent.ping, invalid PSK values, and missing servers. They do not verify network TLS handshakes or the accuracy of host measurements.

## Home Assistant testing before regular use

1. Install each app from the repository. Check the build, log, and agent.version; verify a stable upstream version.
2. Confirm active checks in Zabbix and verify that active-only mode does not listen on a passive port.
3. Test passive checks from allowed and denied addresses, including the selected listening ports.
4. Run both apps together using different Zabbix hostnames and ports.
5. Test Agent 2 container discovery and statistics. Compare process, network, CPU, and memory data with the host. Adjust filesystem discovery.
6. Test PSK with the correct key, an incorrect key, and an unencrypted connection. The latter two must be rejected in PSK mode.
7. Test restart, stop, host reboot, and backup. Check for missing data and ensure secrets are not logged.
8. Rebuild after an upstream update and verify the new version and template compatibility.

Production readiness has not been declared.
