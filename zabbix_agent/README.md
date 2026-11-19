# Zabbix Agent

Monitor the Home Assistant host with Zabbix Agent, using Zabbix's official latest stable Alpine image. Supports active and passive checks and optional TLS-PSK encryption on amd64 and aarch64.

This classic agent does not provide the Agent 2 Docker plugin.

Configure a Zabbix server or proxy before starting. Host process monitoring requires Protection mode off. Filesystem and some OS/cgroup measurements can describe the app container rather than the full host.

See the Documentation tab for all settings, network requirements, security implications and limitations. This is a community app, not an official Home Assistant or Zabbix product.
