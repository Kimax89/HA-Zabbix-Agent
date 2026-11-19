#!/bin/sh
set -eu
umask 077
APP_NAME='Zabbix Agent'
CONFIG_FILE=/data/runtime/zabbix_agentd.conf
# shellcheck source=runtime/agent-common.sh
. /usr/local/lib/ha-zabbix.sh

write_agent_settings() {
    printf 'AllowRoot=1\nPidFile=%s/agent.pid\n' "$RUNTIME_DIR"
    if [ -z "$passive" ]; then printf 'StartAgents=0\n'; fi
}

load_options
prepare_runtime
write_config
unset SUPERVISOR_TOKEN HASSIO_TOKEN
exec /usr/sbin/zabbix_agentd --foreground -c "$CONFIG_FILE"
