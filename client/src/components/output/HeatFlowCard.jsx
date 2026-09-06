import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

const COLORS = { Roof: '#e8664b', Wall: '#e8a03f', Openings: '#4f8bf2' };

export default function HeatFlowCard() {
  const { result } = useSimulation();
  if (!result) return null;

  const { roofW, wallW, openingsW } = result.heatFlow;
  const totalW = roofW + wallW + openingsW;
  const data = [
    { part: 'Roof', watts: roofW },
    { part: 'Wall', watts: wallW },
    { part: 'Openings', watts: openingsW },
  ];

  return (
    <Panel
      title="3. Heat Flow Analysis"
      action={<span className="text-xs text-slate-300 font-semibold">Total: {totalW} W</span>}
    >
      <div className="flex items-center justify-around mb-2 text-[10px] text-slate-400">
        <span>🌙 Nighttime · Total Heat Losses (W)</span>
      </div>
      <div className="grid grid-cols-3 gap-2 mb-2">
        {data.map((d) => (
          <div
            key={d.part}
            className="rounded border border-panel-border bg-[#0d1224] px-2 py-1.5 text-center"
          >
            <div className="text-[9px] text-slate-500">{d.part}</div>
            <div className="text-sm font-semibold tabular-nums" style={{ color: COLORS[d.part] }}>
              {d.watts}W
            </div>
          </div>
        ))}
      </div>
      <div className="h-20">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <YAxis type="category" dataKey="part" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={54} />
            <Tooltip
              contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
              formatter={(v) => [`${v} W`, 'Heat loss']}
            />
            <Bar dataKey="watts" radius={[0, 3, 3, 0]}>
              {data.map((d) => (
                <Cell key={d.part} fill={COLORS[d.part]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
