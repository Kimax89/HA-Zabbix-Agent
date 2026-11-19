# Shared startup runtime

`agent-common.sh` owns the common option validation, PSK handling and configuration writing for both apps. Each `run.sh` supplies the app name, configuration path, agent-specific settings and executable.

The shared runtime is copied into each app as `runtime.sh` because Supervisor builds each app using its own folder as the Docker build context. Maintain `runtime/agent-common.sh`, then run:

```text
python scripts/sync_runtime.py
python scripts/sync_runtime.py --check
```

CI rejects stale copies. The shared code validates all options before creating runtime files. Files under `/data/runtime` are regenerated on startup and are excluded from backups. Option names, app slugs, Zabbix hostnames and default ports remain compatible with earlier releases.
