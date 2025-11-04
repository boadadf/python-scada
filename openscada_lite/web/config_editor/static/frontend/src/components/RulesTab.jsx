import React, { useMemo, useState, useEffect } from 'react';
import Table from './Table';

// RulesTab — replaces the original tab with a visual Condition & Action builder.
// - ConditionEditor: build simple lists of conditions combined with AND/OR and optional negation.
// - ActionEditor: choose action type and parameters instead of free text.
// Notes:
// - This file tries to be backward-compatible: it will parse simple existing condition strings
//   (flat expressions joined by AND/OR) into the visual editor. It does not support parsing
//   arbitrary parenthesized expressions; such conditions fall back to a single RAW condition row.
// - When saving, the visual model is serialized back into the same string format currently used
//   by your engine (e.g. "AuxServer@PRESSURE > 100").

// Helper: shallow copy config for updates
function cloneConfig(cfg) {
  return JSON.parse(JSON.stringify(cfg || {}));
}

// Determine datapoint types and a flat list of datapoints from drivers
function buildDpIndex(config) {
  const drivers = (config?.drivers) || [];
  const dpIndex = {}; // key: "Driver@DP" -> { driver, name, type }
  drivers.forEach((d) => {
    (d.datapoints || []).forEach((p) => {
      const key = `${d.name}@${p.name}`;
      dpIndex[key] = { driver: d.name, name: p.name, type: p.type };
    });
    (d.command_datapoints || []).forEach((p) => {
      const key = `${d.name}@${p.name}`;
      dpIndex[key] = { driver: d.name, name: p.name, type: p.type, isCommand: true };
    });
  });
  return { drivers, dpIndex };
}

// Try to parse a simple condition string into atoms. This is best-effort only.
function parseConditionString(condStr) {
  if (!condStr) return { operator: 'AND', rows: [] };
  // Normalize plus detect top-level AND/OR joins (no parenthesis handling)
  const upper = condStr.replace(/\s+/g, ' ');
  // Try split by ' and ' first, then ' or '. If both present, default to OR if ' or ' found.
  let joinOp = 'AND';
  if (/\s+or\s+/i.test(upper) && !/\s+and\s+/i.test(upper)) joinOp = 'OR';
  const sep = joinOp === 'AND' ? /\s+and\s+/i : /\s+or\s+/i;
  const parts = upper.split(sep).map((p) => p.trim()).filter(Boolean);

  const rows = parts.map((p) => {
    // Remove leading NOT/AND NOT/OR NOT
    let neg = false;
    let raw = p;
    if (/^not\s+/i.test(raw)) {
      neg = true; raw = raw.replace(/^not\s+/i, '');
    }
    // Try to match float(...) wrapper
    const floatWrapped = /^float\(([^)]+)\)\s*(==|!=|<=|>=|<|>)\s*(.+)$/i.exec(raw);
    const atomMatch = floatWrapped || /^(?:([^\s]+@[^\s]+))\s*(==|!=|<=|>=|<|>)\s*(.+)$/.exec(raw);
    if (atomMatch) {
      const dp = atomMatch[1];
      const op = atomMatch[2];
      let val = atomMatch[3].trim();
      // Strip surrounding quotes
      if ((val.startsWith("\'") && val.endsWith("\'")) || (val.startsWith('"') && val.endsWith('"'))) {
        val = val.slice(1, -1);
      }
      // Try number
      const num = Number(val);
      const isNum = !Number.isNaN(num);
      return { type: 'atom', dp, op, value: isNum ? num : val, neg };
    }
    // fallback — raw expression
    return { type: 'raw', expr: p, neg };
  });

  return { operator: joinOp, rows };
}

function buildConditionString(model) {
  // model: { operator: 'AND'|'OR', rows: [{type:'atom', dp, op, value, neg} or {type:'raw', expr, neg}] }
  const parts = model.rows.map((r) => {
    if (r.type === 'atom') {
      const val = (typeof r.value === 'string') ? `'${r.value}'` : String(r.value);
      let atom = `${r.dp} ${r.op} ${val}`;
      if (r.neg) atom = `not ${atom}`;
      return atom;
    }
    if (r.type === 'raw') {
      return r.neg ? `not ${r.expr}` : r.expr;
    }
    return '';
  }).filter(Boolean);
  return parts.join(` ${model.operator.toLowerCase()} `);
}

// Operators UI
const OPERATORS = ['==', '!=', '<', '<=', '>', '>='];

// == ConditionEditor ==
function ConditionEditor({ config, value, onChange }) {
  // value is the existing condition string (may be empty)
  const { dpIndex } = useMemo(() => buildDpIndex(config), [config]);
  const [model, setModel] = useState(() => parseConditionString(value));

  useEffect(() => {
    // keep model in sync if external value changed
    setModel(parseConditionString(value));
  }, [value]);

  useEffect(() => {
    onChange && onChange(buildConditionString(model));
  }, [model]);

  function addAtom() {
    setModel((m) => ({ ...m, rows: [...m.rows, { type: 'atom', dp: Object.keys(dpIndex)[0] || '', op: '==', value: '', neg: false }] }));
  }

  function updateRow(i, patch) {
    setModel((m) => {
      const rows = m.rows.slice(); rows[i] = { ...rows[i], ...patch }; return { ...m, rows };
    });
  }

  function removeRow(i) {
    setModel((m) => { const rows = m.rows.slice(); rows.splice(i, 1); return { ...m, rows }; });
  }

  return (
    <div style={{ border: '1px solid #ddd', padding: 8, borderRadius: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <strong>Condition</strong>
        <div>
          <select value={model.operator} onChange={e => setModel({ ...model, operator: e.target.value })}>
            <option value="AND">AND</option>
            <option value="OR">OR</option>
          </select>
          <button style={{ marginLeft: 8 }} onClick={addAtom}>+ add rule</button>
        </div>
      </div>

      {model.rows.length === 0 && <div style={{ color: '#666' }}>No conditions — rule will always be true.</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {model.rows.map((r, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '28px 1fr 120px 120px 60px', gap: 6, alignItems: 'center' }}>
            <label style={{ fontSize: 12 }} title="Negate">not</label>
            <input type="checkbox" checked={!!r.neg} onChange={e => updateRow(i, { neg: e.target.checked })} />

            {r.type === 'atom' ? (
              <>
                <select value={r.dp} onChange={e => updateRow(i, { dp: e.target.value })}>
                  {Object.keys(dpIndex).map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
                <select value={r.op} onChange={e => updateRow(i, { op: e.target.value })}>
                  {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
                </select>
                <input value={String(r.value ?? '')} onChange={e => {
                  const v = e.target.value;
                  // try parse number
                  const num = Number(v);
                  updateRow(i, { value: (v === '' ? '' : (!Number.isNaN(num) ? num : v)) });
                }} />
              </>
            ) : (
              <>
                <input value={r.expr} onChange={e => updateRow(i, { expr: e.target.value })} style={{ gridColumn: '2 / span 3' }} />
                <div />
              </>
            )}

            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => removeRow(i)}>Del</button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}

// == ActionEditor ==
const ACTION_TYPES = [
  { key: 'send_command', label: 'Send Command' },
  { key: 'raise_alarm', label: 'Raise Alarm' },
  { key: 'lower_alarm', label: 'Lower Alarm' },
];

function ActionEditor({ config, actions = [], onChange }) {
  const { dpIndex } = useMemo(() => buildDpIndex(config), [config]);
  const [model, setModel] = useState(() => (actions || []).slice());

  useEffect(() => setModel((actions || []).slice()), [actions]);
  useEffect(() => onChange && onChange(model), [model]);

  function addAction() {
    setModel(m => [...m, { type: 'raise_alarm' }]);
  }

  function updateAction(i, patch) {
    setModel(m => { const copy = m.slice(); copy[i] = { ...copy[i], ...patch }; return copy; });
  }

  function removeAction(i) { setModel(m => { const c = m.slice(); c.splice(i, 1); return c; }); }

  return (
    <div style={{ border: '1px solid #ddd', padding: 8, borderRadius: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <strong>Actions</strong>
        <button onClick={addAction}>+ action</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {model.map((a, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'center' }}>
            <select value={a.type} onChange={e => updateAction(i, { type: e.target.value, target: undefined, value: undefined })}>
              {ACTION_TYPES.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
            </select>

            {a.type === 'send_command' ? (
              <div style={{ display: 'flex', gap: 6 }}>
                <select value={a.target || Object.keys(dpIndex)[0] || ''} onChange={e => updateAction(i, { target: e.target.value })}>
                  {Object.keys(dpIndex).filter(k => dpIndex[k].isCommand).map(k => <option key={k} value={k}>{k}</option>)}
                </select>
                <input value={a.value ?? ''} onChange={e => updateAction(i, { value: e.target.value })} placeholder="value" />
              </div>
            ) : (
              <div style={{ color: '#333' }}>{a.type === 'raise_alarm' ? 'Raise alarm' : 'Lower alarm'}</div>
            )}

            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => removeAction(i)}>Del</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// -- Main RulesTab --
export default function RulesTab({ config, setConfig }) {
  const rules = config.rules || [];
  const [selected, setSelected] = useState(null);

  // Keep selected valid when rules change
  useEffect(() => {
    if (selected != null && selected >= rules.length) setSelected(null);
  }, [rules.length]);

  const { drivers, dpIndex } = useMemo(() => buildDpIndex(config), [config]);

  function addRule() {
    const copy = cloneConfig(config);
    copy.rules = copy.rules || [];
    const newRule = { rule_id: `rule_${Date.now()}`, on_condition: '', on_actions: [], off_condition: '', off_actions: [] };
    copy.rules.push(newRule);
    setConfig(copy);
    setSelected(copy.rules.length - 1);
  }

  function removeRule() {
    if (selected == null) return; if (!confirm('Delete selected rule?')) return;
    const copy = cloneConfig(config);
    copy.rules.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateRuleField(idx, field, value) {
    const copy = cloneConfig(config);
    copy.rules[idx] = copy.rules[idx] || {};
    copy.rules[idx][field] = value;
    setConfig(copy);
  }

  // Actions serializer/deserializer — convert between array-of-objects and array-of-strings used in storage
  function actionsModelToStorage(actionsModel) {
    // actionsModel: [{type:'send_command', target:'WaterTank@PUMP_CMD', value:'OPEN'} ...]
    const out = actionsModel.map(a => {
      if (a.type === 'send_command') {
        const val = (typeof a.value === 'string' && !/^\d+$/.test(a.value)) ? `'${a.value}'` : String(a.value);
        return `send_command('${a.target}', ${val})`;
      }
      if (a.type === 'raise_alarm') return 'raise_alarm()';
      if (a.type === 'lower_alarm') return 'lower_alarm()';
      return typeof a === 'string' ? a : JSON.stringify(a);
    });
    return out;
  }

  function actionsStorageToModel(actionsStorage) {
    if (!actionsStorage) return [];
    return actionsStorage.map(a => {
      if (typeof a !== 'string') return { type: 'unknown', raw: a };
      const sc = /^send_command\(\s*'([^']+)'\s*,\s*(.+)\s*\)$/i.exec(a);
      if (sc) {
        let val = sc[2].trim();
        if ((val.startsWith("'") && val.endsWith("'")) || (val.startsWith('"') && val.endsWith('"'))) val = val.slice(1, -1);
        return { type: 'send_command', target: sc[1], value: val };
      }
      if (/^raise_alarm\(\s*\)\s*$/i.test(a)) return { type: 'raise_alarm' };
      if (/^lower_alarm\(\s*\)\s*$/i.test(a)) return { type: 'lower_alarm' };
      return { type: 'unknown', raw: a };
    });
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={[ 'rule_id', 'on_condition' ]} data={rules} selectedIndex={selected} onSelect={setSelected} />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={addRule}>+ add</button>
          <button onClick={removeRule}>- delete</button>
        </div>
      </div>

      {selected != null && rules[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Rule</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 8 }}>
            <label>Rule ID:</label>
            <input value={rules[selected].rule_id || ''} onChange={e => updateRuleField(selected, 'rule_id', e.target.value)} />

            <label>On condition:</label>
            <div>
              <ConditionEditor config={config} value={rules[selected].on_condition} onChange={(s) => updateRuleField(selected, 'on_condition', s)} />
            </div>

            <label>On actions:</label>
            <div>
              <ActionEditor config={config} actions={actionsStorageToModel(rules[selected].on_actions || [])} onChange={(m) => updateRuleField(selected, 'on_actions', actionsModelToStorage(m))} />
            </div>

            <label>Off condition:</label>
            <div>
              <ConditionEditor config={config} value={rules[selected].off_condition || ''} onChange={(s) => updateRuleField(selected, 'off_condition', s)} />
            </div>

            <label>Off actions:</label>
            <div>
              <ActionEditor config={config} actions={actionsStorageToModel(rules[selected].off_actions || [])} onChange={(m) => updateRuleField(selected, 'off_actions', actionsModelToStorage(m))} />
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
