# Home Assistant API monitoring template

Template version **1.0.0.0**, targeting **Zabbix 8.0**. This standalone template monitors the Home Assistant API and entities. It requires HTTP access from the Zabbix server/proxy and a Home Assistant access token. No agent or parent templates are required.

## Home Assistant entities

Import `home_assistant_entities.yaml` under **Data collection → Templates → Import**. Link **Home Assistant entities by HTTP** to a host. No agent interface or app installation is required for this template.

On the host, configure these macros:

| Macro | Value / default |
| --- | --- |
| `{$HA.URL}` | Home Assistant base URL, e.g. `http://192.168.1.50:8123`, without a trailing slash |
| `{$HA.TOKEN}` | Your Home Assistant long-lived access token; keep the macro type **Secret text** |
| `{$HA.POLL.INTERVAL}` | `60s` |
| `{$HA.API.NODATA}` | `5m`; keep longer than three polling intervals |
| `{$HA.ENTITY.MATCHES}` | `.*`, to discover all accessible entity IDs |
| `{$HA.ENTITY.NOT_MATCHES}` | `^$`, to exclude none |
| `{$HA.BATTERY.MIN}` | `20`, the low-battery threshold in percent |

Create the token from the Home Assistant user's profile under **Security → Long-lived access tokens**. A dedicated user is preferable. The token inherits that user's permissions; it is not inherently read-only. The template itself only makes GET requests. Do not paste the token into the YAML or commit it to GitHub.

The Zabbix server/proxy, rather than the Agent app, performs the HTTP requests. It must resolve the configured name and reach the configured port. If `homeassistant.local` does not resolve there, use the host's IP or a working DNS name. HTTPS certificate verification is enabled, and HTTP redirects are disabled; configure the final URL and a certificate trusted by the Zabbix server/proxy.

### Measurements

- All entities returned by `/api/states`: state, available/unavailable flag, and last state-change timestamp.
- Numeric sensor, number, input_number, and counter values, including their units. Text, unknown, unavailable, and non-finite values are discarded from numeric items while their text states remain visible.
- Battery levels for entities with `device_class: battery` and unit `%`.
- Pending updates represented by `update.*` entities.
- Global entity, unavailable, unknown, pending-update, and disabled-automation counts.
- Core version, lifecycle state, time zone, and loaded component count from `/api/config`.

Discovery follows the include/exclude macros. Global counts describe the entire API response, including entities excluded from discovery. For example, use `^(sensor|binary_sensor|update)\.` to include selected domains, or `^sensor\.noisy_` to exclude a group of sensors. Lost entities are retained for seven days and are then deleted by discovery. Changes to discovery filters can take up to one hour to appear when discovery output is otherwise unchanged; temporarily shorten the discovery rule's discard-unchanged heartbeat interval if a shorter delay is needed.

### Alerts

- No valid entity API response for five minutes: **High**. This includes connectivity, authentication and invalid-response failures.
- No valid Core configuration for five minutes: **Warning**.
- Entity unavailable or unknown for three received samples: **Warning**. At the default interval this is roughly two minutes from the first bad sample, not a guaranteed full three-minute delay. Stale per-entity data suppresses this alert after the no-data interval.
- Fresh battery reading below the configured threshold: **Warning**.
- Update entity reporting `on`: **Information**.

An `off` binary sensor is treated as available, not as an error. Alarm conditions vary by entity; create additional triggers for your door, smoke, water, security and other important entities according to their actual meaning. Set up Zabbix notification actions separately; importing a template does not send notifications by itself.

### Scope and data volume

The template polls current states. It cannot guarantee capture of short-lived changes between polls, every event, or the complete Home Assistant recorder history. It only sees entities accessible to the token; disabled or absent entities cannot be discovered. It does not query entity/device registries, detailed logs, backups, Supervisor health, or integration diagnostics. Update monitoring only covers exposed update entities.

Unnecessary entity attributes and location information from `/api/config` are removed during preprocessing. The bulk source items and per-entity intermediate data have no history. Entity states can still contain private information. History for individual values is seven days; numeric trends are thirty days. One HTTP request per poll retrieves all states, but discovering thousands of entities still creates thousands of Zabbix items. Use the filters and history settings to control storage and workload.

## Verification

See `VALIDATION.md` for checks actually performed and checks still needed on a real Zabbix/Home Assistant installation.

To regenerate the exports, install Python 3 and PyYAML, then run:

```text
python templates/home_assistant/build.py
```

To run local structure and preprocessing checks, also install Node.js and run:

```text
python templates/home_assistant/test_templates.py
```

## References

- [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/)
- [Zabbix template export/import](https://www.zabbix.com/documentation/current/en/manual/config/xml_export_import/templates)
