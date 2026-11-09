# Setup

See the [installation and configuration guide](https://github.com/Kimax89/HA-Zabbix-Agent#readme).

Set hostname and at least one server field. Passive checks use listen_port. Turn off Protection mode to access host processes. Only Agent 2 receives Docker access. Filesystem measurements may describe the container.

Both PSK fields are required for encryption. Without PSK, traffic is unencrypted. The default port is 10052 for Agent and 10050 for Agent 2. Use different hostnames and ports when running both apps together.

The app uses upstream's stable alpine-latest image. Rebuild to fetch a newer image; restarting is not enough.
