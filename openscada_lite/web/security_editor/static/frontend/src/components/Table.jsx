import React from "react";

export default function Table({ columns, data, selectedIndex, onSelect }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          {columns.map(col => <th key={col} style={{ border: '1px solid #ccc', padding: '6px', textAlign: 'left' }}>{col}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, idx) => (
          <tr key={idx} onClick={() => onSelect(idx)} style={{ background: selectedIndex === idx ? '#e6f7ff' : 'transparent', cursor: 'pointer' }}>
            {columns.map(c => (
              <td key={c} style={{ border: '1px solid #eee', padding: '6px' }}>{String(row[c] === undefined ? (row[c.toLowerCase()] ?? '') : row[c])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}