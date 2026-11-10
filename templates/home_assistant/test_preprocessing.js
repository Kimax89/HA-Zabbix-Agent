// Execute the JavaScript embedded in the exported template against synthetic API data.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const template = JSON.parse(fs.readFileSync(0, 'utf8'));
const items = Object.fromEntries(template.items.map(item => [item.key, item]));
const rules = Object.fromEntries(template.discovery_rules.map(rule => [rule.key, rule]));
let checks = 0;
function equal(actual, expected) { assert.deepEqual(actual, expected); checks++; }
function run(code, value) {
  return new vm.Script('(function(value) {' + code + '\n})(input)')
    .runInNewContext({input: typeof value === 'string' ? value : JSON.stringify(value)}, {timeout: 1000});
}
function script(object) { return object.preprocessing.find(step => step.type === 'JAVASCRIPT').parameters[0]; }
const timestamp = '2026-11-10T10:15:00.123456+00:00';
function entity(id, state, attrs = {}) { return {entity_id:id, state, attributes:attrs, last_changed:timestamp}; }
const source = [
  entity('sensor.temperature', '-2.5', {unit_of_measurement:'°C', latitude:55, access_token:'SECRET'}),
  entity('sensor.battery', '12', {unit_of_measurement:'%', device_class:'battery'}),
  entity('sensor.offline', 'unavailable', {unit_of_measurement:'W'}),
  entity('sensor.unknown', 'unknown'), entity('sensor.text', 'Cloudy'),
  entity('update.core', 'on'), entity('automation.test', 'off'), entity('binary_sensor.door', 'off'),
  entity('input_number.target', '20'), entity('counter.events', '0'), entity('sensor.empty', ''),
];
const sanitize = script(items['ha.states.get']);
const value = run(sanitize, source);
const sanitized = JSON.parse(value);
equal(sanitized.length, 11);
equal(value.includes('SECRET'), false);
equal(value.includes('latitude'), false);
equal(JSON.parse(run(sanitize, [...source].reverse())), sanitized);
assert.throws(() => run(sanitize, {message:'unauthorized'})); checks++;
assert.throws(() => run(sanitize, [entity('bad.id"', '1')])); checks++;
const countExpectations = {'ha.entities.total':11, 'ha.entities.unavailable':1, 'ha.entities.unknown':1,
  'ha.updates.pending':1, 'ha.automations.disabled':1};
for (const [key, expected] of Object.entries(countExpectations)) equal(run(script(items[key]), value), expected);
function discover(key) { return JSON.parse(run(script(rules[key]), value)); }
equal(discover('ha.entity.discovery').length, 11);
equal(discover('ha.battery.discovery').map(e => e['{#ENTITY_ID}']), ['sensor.battery']);
equal(discover('ha.update.discovery').map(e => e['{#ENTITY_ID}']), ['update.core']);
equal(discover('ha.numeric.discovery').map(e => e['{#ENTITY_ID}']),
  ['counter.events','input_number.target','sensor.battery','sensor.offline','sensor.temperature']);
const entityPrototypes = Object.fromEntries(rules['ha.entity.discovery'].item_prototypes.map(i => [i.key, i]));
const availability = script(entityPrototypes['ha.entity.available[{#ENTITY_ID}]']);
for (const [state, expected] of [['off',1], ['on',1], ['0',1], ['unknown',0], ['unavailable',0]]) {
  equal(run(availability, {state}), expected);
}
const number = script(rules['ha.numeric.discovery'].item_prototypes[0]);
for (const [text, expected] of [['-2.5',-2.5], ['0',0], ['1e3',1000], ['.25',0.25]]) equal(run(number,text), expected);
for (const text of ['unknown','unavailable','','12W','NaN','Infinity','1e999']) {
  assert.throws(() => run(number,text)); checks++;
}
const changed = script(entityPrototypes['ha.entity.last_changed[{#ENTITY_ID}]']);
equal(run(changed, timestamp), Math.floor(Date.parse(timestamp)/1000));
const update = script(rules['ha.update.discovery'].item_prototypes[0]);
equal(run(update,'on'),1); equal(run(update,'off'),0);
assert.throws(() => run(update,'unavailable')); checks++;
const config = JSON.parse(run(script(items['ha.config.get']),
  {version:'2026.11.0',state:'RUNNING',components:['api','sensor'],time_zone:'Europe/Copenhagen',latitude:55}));
equal(config.component_count,2); equal(config.version,'2026.11.0'); equal('latitude' in config,false);
console.log(checks + ' preprocessing assertions passed');
