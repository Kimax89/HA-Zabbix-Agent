#!/bin/sh
set -eu
umask 077

fail() {
    echo "Zabbix Agent 2: $1" >&2
    exit 1
}

options=/data/options.json
# Reject line breaks and control characters before writing agent directives.
jq -e 'type == "object" and all(.hostname, .server_active, .server_passive, .tls_psk_identity, .tls_psk; type == "string" and (test("[\\x00-\\x1f\\x7f]") | not))' "$options" >/dev/null || fail "Invalid options. Use single-line text values."
hostname=$(jq -er '.hostname | select(length > 0)' "$options") || fail "hostname is required."
active=$(jq -er '.server_active' "$options")
passive=$(jq -er '.server_passive' "$options")
port=$(jq -er '.listen_port | select(type == "number" and . == floor and . >= 1 and . <= 65535)' "$options") || fail "Invalid listen_port."
identity=$(jq -er '.tls_psk_identity' "$options")
psk=$(jq -er '.tls_psk' "$options")
[ -n "$active$passive" ] || fail "Set server_active or server_passive."
[ -S /var/run/docker.sock ] || fail "Docker socket unavailable. Disable protection mode."

mkdir -p /data/runtime
config=/data/runtime/zabbix_agent2.conf
{
    printf 'LogType=console\nHostname=%s\n' "$hostname"
    printf 'ControlSocket=/data/runtime/agent.sock\n'
    printf 'Plugins.Docker.Endpoint=unix:///var/run/docker.sock\n'
    # Never inherit image defaults that silently enable passive checks.
    if [ -n "$active" ]; then printf 'ServerActive=%s\n' "$active"; fi
    if [ -n "$passive" ]; then printf 'Server=%s\nListenPort=%s\n' "$passive" "$port"; fi
} > "$config"

if [ -n "$psk$identity" ]; then
    [ -n "$identity" ] || fail "PSK identity is required when using PSK."
    printf '%s' "$psk" | jq -Rse 'test("^[0-9a-fA-F]{32,512}$") and (length % 2 == 0)' >/dev/null || fail "PSK must contain 32-512 hexadecimal characters, in pairs."
    printf '%s\n' "$psk" > /data/runtime/agent.psk
    printf 'TLSConnect=psk\nTLSAccept=psk\nTLSPSKIdentity=%s\nTLSPSKFile=/data/runtime/agent.psk\n' "$identity" >> "$config"
else
    rm -f /data/runtime/agent.psk
fi

exec /usr/sbin/zabbix_agent2 --foreground -c "$config"
