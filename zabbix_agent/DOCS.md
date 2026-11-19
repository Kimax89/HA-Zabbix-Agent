# Zabbix Agent: setup and reference

## Install and start

Add `https://github.com/Kimax89/HA-Zabbix-Agent` under **Settings → Apps → App store → Repositories**, then install **Zabbix Agent**. Requires Supervisor, normally Home Assistant OS; Home Assistant Container alone cannot install apps.

1. Fill in `hostname` and at least one server field below.
2. Turn off **Protection mode** on the app information page to enable host process monitoring.
3. Configure the corresponding host and templates on your Zabbix server or proxy.
4. Save, start the app, and check the Log tab. Restart after changing options.

```yaml
hostname: homeassistant-agent
server_active: "192.168.1.20:10051"
server_passive: ""
listen_port: 10052
tls_psk_identity: ""
tls_psk: ""
```

Replace the example address with your Zabbix server/proxy. Its template and agent version must be compatible. The Home Assistant app version and upstream Zabbix version are separate; see `agent.version` or the app log for the actual Zabbix version.

## All options

| Option | Default | Meaning |
| --- | --- | --- |
| `hostname` | `homeassistant-agent` | Exact, case-sensitive Zabbix **Host name**. Required and non-empty. |
| `server_active` | Empty | Server/proxy address, optionally with port (default 10051). Supports Zabbix address lists. Empty disables active checks. |
| `server_passive` | Empty | Comma-separated allowed server/proxy IPs, DNS names or CIDR networks, without ports. Empty disables passive checks. |
| `listen_port` | `10052` | Host TCP port for passive checks; must be free. Ignored when passive checks are disabled. |
| `tls_psk_identity` | Empty | Identity agreed with Zabbix. Set together with `tls_psk` to enable PSK-only connections. |
| `tls_psk` | Empty | Secret key: an even number of hexadecimal characters, 32–512 characters total. Both PSK fields must be filled or both empty. |

At least one server field is required. Single-line text is required; configuration line breaks/control characters are rejected. Keep PSK values in a password field or use Home Assistant's supported `!secret` mechanism; never post keys in logs/issues.

## Configure Zabbix and network access

For active checks, use **Linux by Zabbix agent active** or another matching active template. The app initiates connections to the configured server/proxy (normally TCP 10051). `hostname` must match the monitored host. If using a proxy, assign the Zabbix host to that proxy and use the proxy address in the app.

For passive checks, set `server_passive`, configure the Zabbix host's agent interface with the Home Assistant machine's IP and `listen_port`, and allow the server/proxy to connect to that TCP port. No passive TCP listener is opened when `server_passive` is empty. The app uses host networking, so there is no separate Home Assistant port mapping.

For Docker monitoring, install the separate **Zabbix Agent 2** app instead; this app has no built-in Docker plugin.

Both apps may run together, but their Zabbix hostnames and passive listening ports must differ. The classic Agent defaults to 10052; Agent 2 defaults to 10050.

## PSK encryption

Generate a random hexadecimal key and configure the same identity/key on the Zabbix host. For active traffic, set the host's **Connections from host** to PSK; for passive traffic, set **Connections to host** to PSK. With PSK configured, the app uses and accepts PSK only. Without PSK, agent traffic is unencrypted; use a trusted network or VPN.

The key is included in the app's saved options and Home Assistant backups. Generated key/config files under `/data/runtime` are root-only, recreated on startup and excluded from backups; the original saved options are still backed up.

## Access and limitations

- `host_network` exposes real host interfaces and the passive listening port. It is needed for host network metrics.
- `host_pid` exposes host processes, requiring Protection mode off.
- `host_uts` exposes the host's system hostname to system metrics; it does not override the configured Zabbix `hostname`.
- The app runs as root for access to host process metadata. It requests no added Linux capabilities, hardware access, Home Assistant API role or Supervisor API role. Docker's default AppArmor profile remains enabled.
- Host root filesystems, SMART devices and host logs are not generally mounted. Filesystem, OS/package and some cgroup measurements can describe the app container. Compare values with the host and adjust template discovery filters.
- Remote commands/custom UserParameters are not enabled by this app. It has no web interface, ingress or user login.

## Updates, backups and troubleshooting

The app follows the official `alpine-latest` image by design. A new build fetches the then-current stable Alpine image. Restarting does not update it. Select **Rebuild** when you want to refresh the upstream version and verify `agent.version` afterwards. Floating tags are less reproducible than pinned images; check server/template compatibility before an upgrade.

| Symptom | Check |
| --- | --- |
| App stops immediately | Log tab: missing server/hostname, invalid PSK or port, or an agent configuration error. |
| No active data | Host name matches exactly; correct proxy assignment; server TCP 10051 reachable; matching active template. |
| Passive connection fails | Allowed address matches the server/proxy's source IP; selected host port is free/reachable; correct agent interface and PSK. |
| Port already in use | Change `listen_port` and the agent-interface port in Zabbix. |
| Filesystem data looks different | The app has no general host root mount; filter container filesystem discovery. |

A normal stop sends SIGTERM through Docker's init process. Reboot/restart reloads the saved options and regenerates transient files. Restore the app options from a Home Assistant backup and restart; transient files do not need restoring.

## Support and license

Report issues at [Kimax89/HA-Zabbix-Agent](https://github.com/Kimax89/HA-Zabbix-Agent/issues), including app/upstream versions, architecture, relevant logs and a configuration with keys removed. Never include tokens or PSK secrets.

Repository code is licensed under [GNU GPL v3](https://github.com/Kimax89/HA-Zabbix-Agent/blob/main/LICENSE). The official Zabbix binaries retain their upstream AGPL v3 license, and Alpine packages retain their own licenses. Zabbix trademarks belong to Zabbix SIA. This community app is not affiliated with or endorsed by Zabbix or Home Assistant.
