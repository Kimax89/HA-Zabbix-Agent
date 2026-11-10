#!/bin/sh
set -eu
app=${1:?Usage: sh tests/smoke.sh zabbix_agent-or-zabbix_agent2}
case "$app" in
    zabbix_agent) binary=zabbix_agentd; config=zabbix_agentd.conf ;;
    zabbix_agent2) binary=zabbix_agent2; config=zabbix_agent2.conf ;;
    *) echo "Unknown app: $app" >&2; exit 1 ;;
esac

# Named volumes avoid root-owned bind-mount files that a CI runner cannot delete.
data=$(mktemp -d)
container=
volume=
cleanup() {
    result=$?
    trap - EXIT INT TERM
    if [ -n "$container" ]; then
        if [ "$result" -ne 0 ]; then docker logs "$container" >&2 || true; fi
        docker rm -fv "$container" >/dev/null || result=1
    fi
    if [ -n "$volume" ]; then docker volume rm "$volume" >/dev/null || result=1; fi
    rm -f "$data/options.json" "$data/invalid.json"
    rmdir "$data" || result=1
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

write_options() {
    test_port=${5:-10050}
    jq -n --arg active "$1" --arg passive "$2" --arg identity "$3" --arg psk "$4" \
      --argjson port "$test_port" \
      '{hostname:"ci-agent",server_active:$active,server_passive:$passive,tls_psk_identity:$identity,tls_psk:$psk,listen_port:$port}' > "$data/options.json"
}
start() {
    volume=$(docker volume create)
    if [ "$app" = zabbix_agent2 ]; then
        container=$(docker create --init -v "$volume:/data" \
          -v /var/run/docker.sock:/var/run/docker.sock:ro ha-zabbix-test)
    else
        container=$(docker create --init -v "$volume:/data" ha-zabbix-test)
    fi
    docker cp "$data/options.json" "$container:/data/options.json"
    docker start "$container" >/dev/null
}
stop() {
    docker stop -t 10 "$container" >/dev/null
    docker rm -v "$container" >/dev/null
    container=
    docker volume rm "$volume" >/dev/null
    volume=
}
assert_running() {
    attempt=0
    while [ "$attempt" -lt 15 ]; do
        [ "$(docker inspect -f '{{.State.Running}}' "$container")" = true ]
        if output=$(docker exec "$container" "/usr/sbin/$binary" \
          -c "/data/runtime/$config" -t agent.ping 2>&1); then
            if printf '%s\n' "$output" | grep -Eq '\[(u|s)\|1\]'; then return; fi
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "Agent did not become ready: $output" >&2
    return 1
}
assert_listener() {
    expected=$1
    attempt=0
    while [ "$attempt" -lt 15 ]; do
        # Read failures must fail the test, rather than look like a closed port.
        sockets=$(docker exec "$container" cat /proc/net/tcp)
        actual=$(printf '%s\n' "$sockets" | awk -v port="$test_port" '$2 ~ (":" sprintf("%04X", port) "$") && $4 == "0A" {found=1} END {print found ? "open" : "closed"}')
        if [ "$actual" = "$expected" ]; then return; fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "Expected passive port $expected, found $actual" >&2
    return 1
}
expect_failure() {
    expected=$1
    start
    code=$(timeout 30 docker wait "$container")
    [ "$code" != 0 ]
    # Check the reason as well as the exit code, so unrelated failures cannot pass.
    docker logs "$container" 2>&1 | grep -F "$expected"
    stop
}

write_options 127.0.0.1:10051 '' '' ''
start
assert_running
assert_listener closed
stop

write_options '' 127.0.0.1 '' ''
start
assert_running
assert_listener open
stop

write_options 127.0.0.1:10051 127.0.0.1 ci-key 0123456789abcdef0123456789abcdef
start
assert_running
assert_listener open
stop

write_options '' 127.0.0.1 '' '' 10052
start
assert_running
assert_listener open
stop

write_options 127.0.0.1:10051 '' ci-key invalid
expect_failure 'PSK must contain'
write_options '' '' '' ''
expect_failure 'Set server_active or server_passive.'
write_options 127.0.0.1:10051 '' '' ''
jq '.hostname = "ci-agent\nServer=0.0.0.0/0"' "$data/options.json" > "$data/invalid.json"
mv "$data/invalid.json" "$data/options.json"
expect_failure 'Invalid options.'
