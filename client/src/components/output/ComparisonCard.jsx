import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

export default function ComparisonCard() {
  const { comparison, isComparing, comboKey, shape, orientation, size } = useSimulation();
  if (!comparison && !isComparing) return null;

  const top = (comparison?.top || []).slice(0, 6);
  const currentComboLabel = `${comboKey}_${orientation}_${size}_${shape}`;

  return (
    <Panel
      title="5. Optimization & Comparison"
      action={
        <span className="text-[10px] text-slate-400">
          {comparison ? `${comparison.configurationsEvaluated} configs scored` : 'Scoring…'}
        </span>
      }
    >
      {comparison?.best && (
        <div className="mb-3 rounded border border-accent-teal/40 bg-accent-teal/10 px-3 py-2">
          <div className="text-[9px] text-accent-teal uppercase tracking-wide">Recommended Design</div>
          <div className="text-sm text-slate-100 font-semibold">{comparison.best.label}</div>
          <div className="text-[10px] text-slate-400">
            Efficiency {comparison.best.efficiencyScore}% · Energy saved {comparison.best.energySavedPercent}%
          </div>
        </div>
      )}

      <div className="text-[10px] text-slate-500 mb-1.5">
        Vary geometry · orientation · material layers — top scoring combinations
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={top} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fontSize: 8, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              width={140}
            />
            <Tooltip
              contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
              formatter={(v) => [`${v}%`, 'Efficiency']}
            />
            <Bar dataKey="efficiencyScore" radius={[0, 3, 3, 0]}>
              {top.map((d) => (
                <Cell
                  key={d.comboLabel}
                  fill={d.comboLabel === currentComboLabel ? '#4f8bf2' : d.comboLabel === comparison.best.comboLabel ? '#3fb6c4' : '#2a3355'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
