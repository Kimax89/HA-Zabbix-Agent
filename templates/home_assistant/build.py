"""Build deterministic Zabbix 8.0 template exports. Requires PyYAML."""

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml


ROOT = Path(__file__).resolve().parent
NAME = "Home Assistant entities by HTTP"
GROUP = "Templates/Applications"


def uid(name):
    digest = uuid5(NAMESPACE_URL, "https://github.com/Kimax89/HA-Zabbix-Agent/templates/" + name)
    return UUID(bytes=digest.bytes, version=4).hex


def js(code, discard=False):
    step = {"type": "JAVASCRIPT", "parameters": [code]}
    if discard:
        step["error_handler"] = "DISCARD_VALUE"
    return step


def path(expression, discard=False):
    step = {"type": "JSONPATH", "parameters": [expression]}
    if discard:
        step["error_handler"] = "DISCARD_VALUE"
    return step


def tags(component):
    return [{"tag": "application", "value": "home-assistant"},
            {"tag": "component", "value": component}]


def trigger(key, title, expression, severity="WARNING"):
    return {"uuid": uid("trigger/" + key), "name": title,
            "expression": expression, "priority": severity, "tags": tags("health")}


def dependent(key, title, master, preprocessing, value_type="UNSIGNED", history="7d"):
    result = {"uuid": uid(key), "name": title, "type": "DEPENDENT", "key": key,
              "delay": "0", "history": history, "value_type": value_type,
              "preprocessing": preprocessing, "master_item": {"key": master},
              "tags": tags("entities")}
    if value_type in ("UNSIGNED", "FLOAT"):
        result["trends"] = "30d"
    return result


def http(key, title, endpoint, preprocessing):
    return {"uuid": uid(key), "name": title, "type": "HTTP_AGENT", "key": key,
            "delay": "{$HA.POLL.INTERVAL}", "history": "0", "value_type": "TEXT",
            "url": "{$HA.URL}" + endpoint, "timeout": "10s", "status_codes": "200",
            "follow_redirects": "NO", "verify_peer": "YES", "verify_host": "YES",
            "headers": [{"name": "Authorization", "value": "Bearer {$HA.TOKEN}"},
                        {"name": "Accept", "value": "application/json"}],
            "preprocessing": preprocessing, "tags": tags("api")}


SANITIZE_STATES = """var states = JSON.parse(value);
if (!Array.isArray(states)) { throw 'Expected an entity-state array'; }
var result = [];
for (var i = 0; i < states.length; i++) {
    var s = states[i];
    if (!s || typeof s.entity_id !== 'string' ||
        !/^[a-z0-9_]+\\.[a-z0-9_]+$/.test(s.entity_id) || typeof s.state !== 'string') {
        throw 'Invalid entity-state record';
    }
    var a = s.attributes || {};
    result.push({entity_id: s.entity_id, state: s.state,
        unit: typeof a.unit_of_measurement === 'string' ? a.unit_of_measurement : '',
        device_class: typeof a.device_class === 'string' ? a.device_class : '',
        last_changed: s.last_changed || ''});
}
result.sort(function(a, b) { return a.entity_id < b.entity_id ? -1 : a.entity_id > b.entity_id ? 1 : 0; });
return JSON.stringify(result);"""

SANITIZE_CONFIG = """var c = JSON.parse(value);
if (!c || typeof c.version !== 'string' || !Array.isArray(c.components)) {
    throw 'Expected Home Assistant configuration';
}
return JSON.stringify({version: c.version, state: c.state || '',
    time_zone: c.time_zone || '', component_count: c.components.length});"""

NUMERIC = """var text = String(value).trim();
if (!/^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$/.test(text)) {
    throw 'Not a numeric state';
}
var number = Number(text);
if (!isFinite(number)) { throw 'Non-finite state'; }
return number;"""


def discovery(key, title, selection):
    code = """var entities = JSON.parse(value), result = [];
for (var i = 0; i < entities.length; i++) {
    var e = entities[i];
    if (SELECTION) {
        result.push({'{#ENTITY_ID}': e.entity_id, '{#UNIT}': e.unit});
    }
}
return JSON.stringify(result);""".replace("SELECTION", selection)
    return {"uuid": uid(key), "name": title, "type": "DEPENDENT", "key": key,
            "delay": "0", "lifetime": "7d", "enabled_lifetime_type": "DISABLE_NEVER",
            "master_item": {"key": "ha.states.get"},
            "filter": {"evaltype": "AND", "conditions": [
                {"macro": "{#ENTITY_ID}", "value": "{$HA.ENTITY.MATCHES}", "formulaid": "A"},
                {"macro": "{#ENTITY_ID}", "value": "{$HA.ENTITY.NOT_MATCHES}",
                 "operator": "NOT_MATCHES_REGEX", "formulaid": "B"}]},
            "preprocessing": [js(code), {"type": "DISCARD_UNCHANGED_HEARTBEAT", "parameters": ["1h"]}],
            "item_prototypes": []}


def state_path():
    return '$[?(@.entity_id == "{#ENTITY_ID}")].first()'


def entity_value(key, title, expression, value_type="UNSIGNED"):
    return dependent(key, title, "ha.states.get",
                     [path(state_path(), discard=True), path(expression)], value_type)


def export(template):
    return {"zabbix_export": {"version": "8.0", "template_groups": [
        {"uuid": "a571c0d144b14fd4a87a9d9b2aa9fcd6", "name": GROUP}], "templates": [template]}}


def build():
    template = {"uuid": uid(NAME), "template": NAME, "name": NAME,
                "description": "Home Assistant Core API and entity monitoring. Template version 1.0.0.0. "
                               "Uses GET requests only. Configure HA.URL and HA.TOKEN. "
                               "Link Linux and Docker templates separately for host/container metrics.",
                "groups": [{"name": GROUP}], "items": [], "discovery_rules": [], "macros": []}
    items = template["items"]
    items.append(http("ha.states.get", "Home Assistant: Get entity states", "/api/states", [js(SANITIZE_STATES)]))
    items.append(http("ha.config.get", "Home Assistant: Get Core configuration", "/api/config", [js(SANITIZE_CONFIG)]))
    for key, title, code in (
        ("ha.entities.total", "Total entities", "return JSON.parse(value).length;"),
        ("ha.entities.unavailable", "Unavailable entities", "return JSON.parse(value).filter(function(e) { return e.state === 'unavailable'; }).length;"),
        ("ha.entities.unknown", "Entities with unknown state", "return JSON.parse(value).filter(function(e) { return e.state === 'unknown'; }).length;"),
        ("ha.updates.pending", "Pending update entities", "return JSON.parse(value).filter(function(e) { return e.entity_id.indexOf('update.') === 0 && e.state === 'on'; }).length;"),
        ("ha.automations.disabled", "Disabled automations", "return JSON.parse(value).filter(function(e) { return e.entity_id.indexOf('automation.') === 0 && e.state === 'off'; }).length;"),
    ):
        items.append(dependent(key, "Home Assistant: " + title, "ha.states.get", [js(code)]))
    items[2]["triggers"] = [trigger("api.nodata", "Home Assistant: No valid entity data from API",
        f"nodata(/{NAME}/ha.entities.total,{{$HA.API.NODATA}})=1", "HIGH")]
    for key, title, field, value_type in (
        ("ha.core.version", "Core version", "version", "CHAR"),
        ("ha.core.state", "Core lifecycle state", "state", "CHAR"),
        ("ha.core.time_zone", "Time zone", "time_zone", "CHAR"),
        ("ha.components.total", "Loaded components", "component_count", "UNSIGNED"),
    ):
        items.append(dependent(key, "Home Assistant: " + title, "ha.config.get", [path("$." + field)], value_type))
    items[-1]["triggers"] = [trigger("config.nodata", "Home Assistant: No valid Core configuration from API",
        f"nodata(/{NAME}/ha.components.total,{{$HA.API.NODATA}})=1", "WARNING")]

    entities = discovery("ha.entity.discovery", "Home Assistant: Entity discovery", "true")
    raw = dependent('ha.entity.data[{#ENTITY_ID}]', 'Entity {#ENTITY_ID}: Data', 'ha.states.get',
                    [path(state_path(), discard=True)], "TEXT", "0")
    state = dependent('ha.entity.state[{#ENTITY_ID}]', 'Entity {#ENTITY_ID}: State', raw["key"], [path("$.state")], "TEXT")
    available = dependent('ha.entity.available[{#ENTITY_ID}]', 'Entity {#ENTITY_ID}: Available', raw["key"],
        [js("var e=JSON.parse(value); return e.state === 'unavailable' || e.state === 'unknown' ? 0 : 1;")])
    available["trigger_prototypes"] = [trigger("entity.unavailable", "Home Assistant: Entity {#ENTITY_ID} is unavailable or unknown",
        f"max(/{NAME}/ha.entity.available[{{#ENTITY_ID}}],#3)=0 and "
        f"count(/{NAME}/ha.entity.available[{{#ENTITY_ID}}],#3)=3 and "
        f"nodata(/{NAME}/ha.entity.available[{{#ENTITY_ID}}],{{$HA.API.NODATA}})=0")]
    changed = dependent('ha.entity.last_changed[{#ENTITY_ID}]', 'Entity {#ENTITY_ID}: Last state change', raw["key"],
        [path("$.last_changed"), js("var text=value.replace(/(\\.\\d{3})\\d+/, '$1'); var time=Date.parse(text); if (!isFinite(time)) { throw 'Invalid timestamp'; } return Math.floor(time/1000);", discard=True)])
    changed["units"] = "unixtime"
    entities["item_prototypes"] = [raw, state, available, changed]
    template["discovery_rules"].append(entities)

    numeric = discovery("ha.numeric.discovery", "Home Assistant: Numeric entity discovery",
        "/^(sensor|number|input_number|counter)\\./.test(e.entity_id) && "
        "(e.unit !== '' || /^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$/.test(e.state.trim()))")
    number = entity_value('ha.entity.numeric[{#ENTITY_ID}]', 'Entity {#ENTITY_ID}: Numeric value', "$.state", "FLOAT")
    number["preprocessing"].append(js(NUMERIC, discard=True))
    number["units"] = "{#UNIT}"
    numeric["item_prototypes"] = [number]
    template["discovery_rules"].append(numeric)

    battery = discovery("ha.battery.discovery", "Home Assistant: Battery sensor discovery", "e.device_class === 'battery' && e.unit === '%'")
    level = entity_value('ha.battery.level[{#ENTITY_ID}]', 'Battery {#ENTITY_ID}: Level', "$.state", "FLOAT")
    level["units"] = "%"
    level["preprocessing"].append(js(NUMERIC, discard=True))
    level["trigger_prototypes"] = [trigger("battery.low", "Home Assistant: Battery {#ENTITY_ID} is low",
        f"last(/{NAME}/ha.battery.level[{{#ENTITY_ID}}])<{{$HA.BATTERY.MIN}} and "
        f"nodata(/{NAME}/ha.battery.level[{{#ENTITY_ID}}],{{$HA.API.NODATA}})=0")]
    battery["item_prototypes"] = [level]
    template["discovery_rules"].append(battery)

    updates = discovery("ha.update.discovery", "Home Assistant: Update entity discovery", "e.entity_id.indexOf('update.') === 0")
    update = entity_value('ha.update.pending[{#ENTITY_ID}]', 'Update {#ENTITY_ID}: Pending', "$.state")
    update["preprocessing"].append(js("if (value === 'on') { return 1; } if (value === 'off') { return 0; } throw 'Unknown update state';", discard=True))
    update["trigger_prototypes"] = [trigger("update.pending", "Home Assistant: Update available for {#ENTITY_ID}",
        f"last(/{NAME}/ha.update.pending[{{#ENTITY_ID}}])=1 and "
        f"nodata(/{NAME}/ha.update.pending[{{#ENTITY_ID}}],{{$HA.API.NODATA}})=0", "INFO")]
    updates["item_prototypes"] = [update]
    template["discovery_rules"].append(updates)

    for macro, value, description in (
        ("HA.URL", "http://homeassistant.local:8123", "Base URL reachable from Zabbix server/proxy; no trailing slash."),
        ("HA.TOKEN", "", "Home Assistant long-lived access token. Configure on the Zabbix host as a secret macro."),
        ("HA.POLL.INTERVAL", "60s", "API polling interval."),
        ("HA.API.NODATA", "5m", "Alert if valid API data is not received for this period; keep longer than three polling intervals."),
        ("HA.ENTITY.MATCHES", ".*", "Discover entity IDs matching this regular expression."),
        ("HA.ENTITY.NOT_MATCHES", "^$", "Do not discover entity IDs matching this regular expression; default excludes none."),
        ("HA.BATTERY.MIN", "20", "Low battery threshold in percent."),
    ):
        entry = {"macro": "{$" + macro + "}", "value": value, "description": description}
        if macro == "HA.TOKEN":
            entry["type"] = "SECRET_TEXT"
        template["macros"].append(entry)

    class TemplateDumper(yaml.SafeDumper):
        pass

    def readable_string(dumper, value):
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|" if "\n" in value else None)

    TemplateDumper.add_representer(str, readable_string)
    (ROOT / "home_assistant_entities.yaml").write_text(
        yaml.dump(export(template), Dumper=TemplateDumper, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
