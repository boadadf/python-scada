import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function RulesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const rules = config.rules || [];

  useEffect(() => {
    if (selected != null && selected >= rules.length) setSelected(null);
  }, [rules.length]);

  function add() {
    const id = prompt('Rule id:');
    if (!id) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules.push({ rule_id: id, on_condition: '', on_actions: [], off_condition: '', off_actions: [] });
    setConfig(copy);
    setSelected(copy.rules.length - 1);
  }

  function remove() {
    if (selected == null) return; if (!confirm('Delete selected rule?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][field] = value;
    setConfig(copy);
  }

  function addAction(kind) {
    const act = prompt('Action (javascript-like string):');
    if (!act) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][kind].push(act);
    setConfig(copy);
  }

  function removeAction(kind, idx) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][kind].splice(idx, 1);
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={[ 'rule_id', 'on_condition' ]} data={rules} selectedIndex={selected} onSelect={setSelected} />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && rules[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Rule</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 8 }}>
            <label>Rule ID:</label>
            <input value={rules[selected].rule_id} onChange={e => updateField('rule_id', e.target.value)} />
            <label>On condition:</label>
            <input value={rules[selected].on_condition} onChange={e => updateField('on_condition', e.target.value)} />
            <label>On actions:</label>
            <div>
              <button onClick={() => addAction('on_actions')}>+ action</button>
              <ul>
                {(rules[selected].on_actions || []).map((a, i) => (
                  <li key={i}>{a} <button onClick={() => removeAction('on_actions', i)}>Del</button></li>
                ))}
              </ul>
            </div>
            <label>Off condition:</label>
            <input value={rules[selected].off_condition || ''} onChange={e => updateField('off_condition', e.target.value)} />
            <label>Off actions:</label>
            <div>
              <button onClick={() => addAction('off_actions')}>+ action</button>
              <ul>
                {(rules[selected].off_actions || []).map((a, i) => (
                  <li key={i}>{a} <button onClick={() => removeAction('off_actions', i)}>Del</button></li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}