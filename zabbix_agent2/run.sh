#!/bin/sh
set -eu
umask 077
APP_NAME='Zabbix Agent 2'
CONFIG_FILE=/data/runtime/zabbix_agent2.conf
# shellcheck source=runtime/agent-common.sh
. /usr/local/lib/ha-zabbix.sh

write_agent_settings() {
    printf 'ControlSocket=%s/agent.sock\n' "$RUNTIME_DIR"
    printf 'Plugins.Docker.Endpoint=unix:///run/docker.sock\n'
}

load_options
[ -S /run/docker.sock ] || fail 'Docker socket unavailable. Disable protection mode.'
prepare_runtime
write_config
unset SUPERVISOR_TOKEN HASSIO_TOKEN
exec /usr/sbin/zabbix_agent2 --foreground -c "$CONFIG_FILE"
