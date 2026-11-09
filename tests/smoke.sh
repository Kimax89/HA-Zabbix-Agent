#!/bin/sh
set -eu
app=$1
case "$app" in
    zabbix_agent) binary=zabbix_agentd; config=zabbix_agentd.conf ;;
    zabbix_agent2) binary=zabbix_agent2; config=zabbix_agent2.conf ;;
    *) exit 1 ;;
esac
data=$(mktemp -d)
container=
cleanup() {
    if [ -n "$container" ]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
    rm -rf "$data"
}
trap cleanup EXIT INT TERM
write_options() {
    jq -n --arg active "$1" --arg passive "$2" --arg identity "$3" --arg psk "$4" \
      '{hostname:"ci-agent",server_active:$active,server_passive:$passive,tls_psk_identity:$identity,tls_psk:$psk,listen_port:10050}' > "$data/options.json"
}
start() {
    container=$(docker run -d -v "$data:/data" -v /var/run/docker.sock:/var/run/docker.sock ha-zabbix-test)
}
stop() {
    docker rm -f "$container" >/dev/null
    container=
}
assert_running() {
    sleep 3
    docker logs "$container"
    [ "$(docker inspect -f '{{.State.Running}}' "$container")" = true ]
    docker exec "$container" "/usr/sbin/$binary" -c "/data/runtime/$config" -t agent.ping | grep -E '\[(u|s)\|1\]'
}

# Active-only mode must start without opening a passive listener.
write_options 127.0.0.1:10051 '' '' ''
start
assert_running
docker exec "$container" sh -c "! grep -q '^Server=' /data/runtime/$config"
stop

# Passive-only mode and combined checks with PSK must parse and start.
write_options '' 127.0.0.1 '' ''
start
assert_running
stop
write_options 127.0.0.1:10051 127.0.0.1 ci-key 0123456789abcdef0123456789abcdef
start
assert_running
stop

# Invalid secrets and missing servers must fail startup, rather than loop silently.
for scenario in invalid_psk missing_server; do
    if [ "$scenario" = invalid_psk ]; then
        write_options 127.0.0.1:10051 '' ci-key invalid
    else
        write_options '' '' '' ''
    fi
    start
    code=$(timeout 30 docker wait "$container")
    [ "$code" != 0 ]
    stop
done
