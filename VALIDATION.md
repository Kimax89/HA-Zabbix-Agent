# Validation - November 10, 2026

Reviewed package: **0.0.2.2**. Both production startup scripts are unchanged by this review; the fixes concern test reliability and documentation.

## Findings and fixes

1. The original smoke test used a bind mount. Root-owned runtime directories created with umask 077 could prevent the non-root GitHub runner from removing them. Tests now use named Docker volumes and remove both containers and volumes.
2. Active-only testing originally checked that the Server directive was absent, rather than checking the listening port. Tests now inspect the actual IPv4 TCP listener for active-only, passive-only, PSK, and custom-port scenarios. This is a socket-state check, not a remote Zabbix protocol test.
3. Negative tests originally accepted any nonzero exit status. They now require the expected error message, preventing unrelated failures from passing the test.
4. A fixed startup delay could produce intermittent failures. Tests now use bounded readiness checks, keep diagnostic logs on failure, and have a job time limit.
5. The workflow now checks the smoke script syntax too and runs input-validation regression tests for both apps.
6. GitHub reported a Node.js 20 deprecation warning for actions/checkout@v4. The workflow now uses checkout@v7.

## Published repository and existing GitHub checks

Reviewed public repository commit `79bce0a` (Translated to English). Its production startup scripts and Dockerfiles match the local versions. The public run [42723544637](https://github.com/Kimax89/HA-Zabbix-Agent/actions/runs/42723544637) shows successful image builds and shell syntax checks for both apps on amd64 and arm64. All four startup/configuration smoke-test steps failed.

GitHub's public API exposes the failing step and exit code, but downloading its detailed logs returned HTTP 403 requiring repository administration rights. Therefore the exact cause of each existing failure is not confirmed. The test defects identified above are real review findings, but must not be assumed to explain every failed job. The revised workflow must be run and its logs reviewed before considering these failures resolved. No changes were pushed to GitHub.

## Checks actually run locally

- `tests/validate.py`: **6 test methods passed**, including parameterized checks for both apps. Uses the actual jq filters extracted from the production startup scripts, not a reimplementation.
- Rejected control characters and wrong types in all five text fields, including attempted newline injection of an agent configuration directive.
- Tested valid and invalid port boundaries, fractional ports, strings, booleans, and missing/null values.
- Tested PSK length boundaries, odd lengths, non-hexadecimal characters, and trailing newlines.
- Parsed both app JSON files, repository YAML, and workflow YAML. Checked matching option/schema keys, distinct app slugs and default ports, version consistency, and correct Alpine image references.
- Portable BusyBox `sh -n`: both production startup scripts and `tests/smoke.sh` passed shell syntax checks.
- Docker Hub registry checks: both `zabbix/zabbix-agent:alpine-latest` and `zabbix/zabbix-agent2:alpine-latest` publish Linux amd64 and arm64 manifests. Manifest availability does not prove the images build or run correctly.
- Checked LF shell line endings and reviewed all current source files. Downloaded validation tools are kept in ignored `.tools/` and excluded from distribution.

Local tools: Python 3.12, jq 1.8.1, PyYAML 6.0.3, and portable BusyBox. BusyBox is only used as a shell syntax checker; no Linux agent was executed locally. Metadata checking is not a full execution of Supervisor's validation schema.

## Not performed

Docker is unavailable locally. The revised smoke test, local container builds, Linux agent startup, real PSK handshakes, Supervisor installation, and actual host/container measurements have not been run here. Existing GitHub build results are described above; the revised workflow has not been uploaded or run from this environment. Passing local checks is not a claim of production readiness.

## Reproduce the checks

With Python 3, jq and PyYAML installed, from the repository root:

    python3 tests/validate.py

On Linux with Docker and jq:

    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent
    sh tests/smoke.sh zabbix_agent
    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent2
    sh tests/smoke.sh zabbix_agent2

The GitHub workflow is configured to build and test on amd64 and arm64. Container tests check startup and local agent.ping; they do not verify communication with a Zabbix server or the accuracy of host measurements.

## Home Assistant integration checks still required

1. Install both apps from the repository. Check build logs and agent.version, including the selected stable upstream version.
2. Confirm active checks in Zabbix and verify that active-only mode does not listen on a passive port.
3. Test passive requests from allowed and denied source addresses using the selected ports.
4. Run both apps together with different Zabbix hostnames and ports.
5. Test Agent 2 Docker discovery and statistics. Compare process, network, CPU, and memory values with the host; adjust filesystem discovery where it describes the app container.
6. Test PSK over the network with a correct key, an incorrect key, and an unencrypted connection. The latter two must be rejected in PSK mode.
7. Test stop, restart, host reboot, and backup. Check for missing data and ensure secrets are not logged.
8. Rebuild after an upstream update, then verify version and template compatibility.

## References checked during review

- https://contributors.home-assistant.io/apps/reference/configuration/
- https://github.com/home-assistant/supervisor/blob/main/supervisor/apps/validate.py
- https://github.com/home-assistant/supervisor/blob/main/supervisor/docker/app.py
- https://www.zabbix.com/documentation/current/en/manual/appendix/config/zabbix_agentd
- Docker Hub registry manifests for the two alpine-latest tags.
