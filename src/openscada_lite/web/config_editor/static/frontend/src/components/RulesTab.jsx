import React, { useState, useEffect, useMemo } from "react";
import Table from "./Table";

// Helper: Clone the config object for updates
function cloneConfig(cfg) {
  return JSON.parse(JSON.stringify(cfg || {}));
}

// Helper: Build datapoint index from drivers
function buildDpIndex(config) {
  const drivers = config?.drivers || [];
  const dpIndex = {}; // key: "Driver@DP" -> { driver, name, type }
  drivers.forEach((driver) => {
    (driver.datapoints || []).forEach((dp) => {
      const key = `${driver.name}@${dp.name}`;
      dpIndex[key] = { driver: driver.name, name: dp.name, type: dp.type };
    });
    (driver.command_datapoints || []).forEach((dp) => {
      const key = `${driver.name}@${dp.name}`;
      dpIndex[key] = { driver: driver.name, name: dp.name, type: dp.type, isCommand: true };
    });
  });
  return { drivers, dpIndex };
}

// Main RulesTab Component
export default function RulesTab({ config, setConfig }) {
  const rules = config.rules || [];
  const [selected, setSelected] = useState(null);

  // Ensure `selected` remains valid when `rules` changes
  useEffect(() => {
    if (selected != null && selected >= rules.length) {
      setSelected(rules.length > 0 ? rules.length - 1 : null);
    }
  }, [rules.length]);

  const { dpIndex } = useMemo(() => buildDpIndex(config), [config]);

  // Add a new rule
  function addRule() {
    const copy = cloneConfig(config);
    copy.rules = copy.rules || [];
    const newRule = {
      rule_id: `rule_${Date.now()}`,
      on_condition: "",
      on_actions: [],
      off_condition: "",
      off_actions: [],
    };
    copy.rules.push(newRule);
    setConfig(copy);
    setSelected(copy.rules.length - 1); // Select the newly added rule
  }

  // Remove the selected rule
  function removeRule() {
    if (selected == null) return;
    if (!window.confirm("Delete selected rule?")) return;
    const copy = cloneConfig(config);
    copy.rules.splice(selected, 1);
    setConfig(copy);
    setSelected(null); // Deselect after deletion
  }

  // Update a specific field of the selected rule
  function updateRuleField(idx, field, value) {
    const copy = cloneConfig(config);
    copy.rules[idx][field] = value;
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      {/* Top Section: Rules Table */}
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["rule_id", "on_condition"]}
            data={rules}
            selectedIndex={selected}
            onSelect={setSelected}
          />
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={addRule}>+ Add</button>
          <button onClick={removeRule} disabled={selected == null}>
            - Delete
          </button>
        </div>
      </div>

      {/* Bottom Section: Rule Editor */}
      {selected != null && rules[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Rule</h3>
          <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 8 }}>
            <label>Rule ID:</label>
            <input
              value={rules[selected].rule_id || ""}
              onChange={(e) => updateRuleField(selected, "rule_id", e.target.value)}
            />

            <label>On Condition:</label>
            <textarea
              value={rules[selected].on_condition || ""}
              onChange={(e) => updateRuleField(selected, "on_condition", e.target.value)}
              style={{ width: "100%", height: "60px" }}
            />

            <label>On Actions:</label>
            <textarea
              value={(rules[selected].on_actions || []).join("\n")}
              onChange={(e) =>
                updateRuleField(selected, "on_actions", e.target.value.split("\n"))
              }
              style={{ width: "100%", height: "60px" }}
            />

            <label>Off Condition:</label>
            <textarea
              value={rules[selected].off_condition || ""}
              onChange={(e) => updateRuleField(selected, "off_condition", e.target.value)}
              style={{ width: "100%", height: "60px" }}
            />

            <label>Off Actions:</label>
            <textarea
              value={(rules[selected].off_actions || []).join("\n")}
              onChange={(e) =>
                updateRuleField(selected, "off_actions", e.target.value.split("\n"))
              }
              style={{ width: "100%", height: "60px" }}
            />
          </div>
        </div>
      )}
    </div>
  );
}