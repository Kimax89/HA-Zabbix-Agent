#!/bin/sh
# Shared startup contract: the app sets APP_NAME and defines write_agent_settings.

OPTIONS_FILTER='type == "object" and all(.hostname, .server_active, .server_passive, .tls_psk_identity, .tls_psk; type == "string" and (test("[\\x00-\\x1f\\x7f]") | not))'
PORT_FILTER='.listen_port | select(type == "number" and . == floor and . >= 1 and . <= 65535)'
PSK_FILTER='test("^[0-9a-fA-F]{32,512}$") and (length % 2 == 0)'
OPTIONS_FILE=/data/options.json
RUNTIME_DIR=/data/runtime
PSK_FILE=$RUNTIME_DIR/agent.psk

fail() {
    printf '%s: %s\n' "$APP_NAME" "$1" >&2
    exit 1
}

load_options() {
    jq -e "$OPTIONS_FILTER" "$OPTIONS_FILE" >/dev/null 2>&1 || fail "Invalid options. Use single-line text values."
    hostname=$(jq -er '.hostname | select(length > 0)' "$OPTIONS_FILE") || fail "hostname is required."
    active=$(jq -er '.server_active' "$OPTIONS_FILE")
    passive=$(jq -er '.server_passive' "$OPTIONS_FILE")
    port=$(jq -er "$PORT_FILTER" "$OPTIONS_FILE") || fail "Invalid listen_port."
    identity=$(jq -er '.tls_psk_identity' "$OPTIONS_FILE")
    psk=$(jq -er '.tls_psk' "$OPTIONS_FILE")
    [ -n "$active$passive" ] || fail "Set server_active or server_passive."
    if [ -n "$psk$identity" ]; then
        [ -n "$identity" ] || fail "PSK identity is required when using PSK."
        printf '%s' "$psk" | jq -Rse "$PSK_FILTER" >/dev/null 2>&1 || fail "PSK must contain 32-512 hexadecimal characters, in pairs."
    fi
}

prepare_runtime() {
    mkdir -p "$RUNTIME_DIR"
    chmod 0700 "$RUNTIME_DIR"
    if [ -n "$psk" ]; then
        printf '%s\n' "$psk" > "$PSK_FILE"
        chmod 0600 "$PSK_FILE"
    else
        rm -f "$PSK_FILE"
    fi
}

write_common_settings() {
    printf 'LogType=console\nHostname=%s\n' "$hostname"
    if [ -n "$active" ]; then printf 'ServerActive=%s\n' "$active"; fi
    if [ -n "$passive" ]; then printf 'Server=%s\nListenPort=%s\n' "$passive" "$port"; fi
    if [ -n "$psk" ]; then
        printf 'TLSConnect=psk\nTLSAccept=psk\nTLSPSKIdentity=%s\nTLSPSKFile=%s\n' "$identity" "$PSK_FILE"
    fi
}

write_config() {
    # The temporary file prevents a failed write from replacing a complete config.
    pending_config=$CONFIG_FILE.pending
    trap 'rm -f "$pending_config"' EXIT
    {
        write_common_settings
        write_agent_settings
    } > "$pending_config"
    chmod 0600 "$pending_config"
    mv -f "$pending_config" "$CONFIG_FILE"
    trap - EXIT
}
