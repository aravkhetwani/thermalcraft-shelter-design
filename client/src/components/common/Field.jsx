export function FieldLabel({ children, action }) {
  return (
    <div className="flex items-center justify-between mb-1.5">
      <span className="text-[11px] text-slate-400">{children}</span>
      {action}
    </div>
  );
}

export function Select({ value, onChange, options, ...rest }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-[#0d1224] border border-panel-border rounded px-2.5 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-accent-blue"
      {...rest}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function ReadoutField({ label, value, unit }) {
  return (
    <div className="bg-[#0d1224] border border-panel-border rounded px-2.5 py-1.5">
      <div className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</div>
      <div className="text-sm text-slate-100 font-medium tabular-nums">
        {value}
        {unit && <span className="text-slate-400 text-xs ml-0.5">{unit}</span>}
      </div>
    </div>
  );
}
