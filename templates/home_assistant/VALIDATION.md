# Template validation

Version **1.0.0.0**, November 10, 2026. Target format: Zabbix **8.0**.

## Passed locally

- Five automated structure/preprocessing test methods in `test_templates.py`.
- Thirty-eight assertions executed against the actual exported JavaScript using Node.js, including:
  - State-response validation and removal of unnecessary attributes.
  - Stable sorting independent of API entity order.
  - Discovery of all entities, numeric entities, batteries, and updates.
  - Zero, negative, decimal and scientific-notation values.
  - Rejection of text, unavailable, unknown, empty, and non-finite numeric values.
  - Correct availability semantics for on/off versus unavailable/unknown.
  - Home Assistant timestamps with microseconds.
  - Config summary extraction without location coordinates.
- YAML parsing, UUID uniqueness, item-key uniqueness, macro references, master-item references, and standalone API template structure.
- Deterministic regeneration produces the same template files.
- Zabbix 8.0 export format checked against upstream examples; no parent templates are required.

Tools: Python 3.12, PyYAML 6.0.3, Node.js 24.22.1. Node.js testing does not constitute testing inside Zabbix's JavaScript engine.

## Not yet tested

- Import into a running Zabbix 8.0 server or validation by its full frontend/API import validator.
- Zabbix-native JSONPath evaluation, trigger evaluation, discovery filtering, inheritance, or Duktape preprocessing.
- Real Home Assistant authentication, permissions, polling, TLS, scale, or collected measurements.

## Acceptance checks on the installation

1. Import the entities template. Confirm no import errors; set URL and secret token, then inspect the two bulk items using **Execute now** and **Test preprocessing**.
2. Confirm total entity count, discovery, sample states and numeric values against Home Assistant. Test an unavailable entity, an update entity and a battery sensor.
3. Test an invalid token and temporary API outage. Check no-data alerts and recovery; ensure stale entity data does not leave misleading alarms.
4. Check include/exclude expressions and per-entity history volume. Verify permissions with the intended Home Assistant user.
5. Configure notification actions and verify API monitoring recovers after Home Assistant restarts.

The templates are prepared for import and local checks passed; live import and monitoring compatibility are not yet confirmed.
