import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import Panel from '../common/Panel';
import { fetchResearchSummary } from '../../api/client';

const MODEL_COLORS = {
  mean_baseline: '#4a5578',
  linear_regression: '#4f8bf2',
  random_forest: '#3fb6c4',
  gradient_boosting: '#e8a03f',
  xgboost: '#3fc47a',
};
const MODEL_LABELS = {
  mean_baseline: 'Mean Baseline',
  linear_regression: 'Linear Regression',
  random_forest: 'Random Forest',
  gradient_boosting: 'Gradient Boosting',
  xgboost: 'XGBoost',
};
const TARGET_LABELS = {
  indoor_temp_c: 'Indoor Temperature (°C)',
  total_loss_w: 'Total Heat Loss (W)',
};

function ModelComparisonTable({ target, data }) {
  const rows = Object.entries(data.models).map(([name, m]) => ({ name, ...m }));
  return (
    <div className="mb-4">
      <div className="text-[11px] text-slate-400 mb-1.5">
        {TARGET_LABELS[target] || target} — {data.nTrain} train / {data.nVal} val / {data.nTest} test samples
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-slate-500 border-b border-panel-border">
              <th className="text-left py-1 pr-2">Model</th>
              <th className="text-right py-1 px-2">MAE</th>
              <th className="text-right py-1 px-2">RMSE</th>
              <th className="text-right py-1 pl-2">R²</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.name}
                className={`border-b border-panel-border/50 ${r.name === data.bestModel ? 'text-slate-100 font-semibold' : 'text-slate-400'}`}
              >
                <td className="py-1 pr-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: MODEL_COLORS[r.name] }} />
                  {MODEL_LABELS[r.name] || r.name}
                  {r.name === data.bestModel && <span className="text-accent-teal text-[9px] ml-1">BEST</span>}
                </td>
                <td className="text-right py-1 px-2 tabular-nums">{r.mae.toFixed(3)}</td>
                <td className="text-right py-1 px-2 tabular-nums">{r.rmse.toFixed(3)}</td>
                <td className="text-right py-1 pl-2 tabular-nums">{r.r2.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FeatureImportanceChart({ target, items }) {
  const data = [...items].reverse();
  return (
    <div className="mb-2">
      <div className="text-[11px] text-slate-400 mb-1.5">{TARGET_LABELS[target] || target}</div>
      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <YAxis type="category" dataKey="feature" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={130} />
            <Tooltip
              contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
              formatter={(v) => [v.toFixed(5), 'Permutation importance']}
            />
            <Bar dataKey="importance" radius={[0, 3, 3, 0]} fill="#3fb6c4" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function OptimizationSummary({ opt }) {
  if (!opt) return null;
  const bd = opt.bestDesign;
  return (
    <div className="space-y-3">
      <div className="rounded border border-accent-teal/40 bg-accent-teal/10 px-3 py-2">
        <div className="text-[9px] text-accent-teal uppercase tracking-wide">Surrogate-Optimized Design (simulator-validated)</div>
        <div className="text-[11px] text-slate-300 mt-1">
          {bd.orientation} · {bd.primary_material} · wall {bd.wall_thickness_m.toFixed(2)}m · insulation {bd.insulation_thickness_m.toFixed(2)}m ·
          {' '}ACH {bd.air_changes_per_hour.toFixed(2)}
        </div>
        <div className="flex gap-4 mt-2 text-xs">
          <div>
            <span className="text-slate-500">Baseline: </span>
            <span className="text-slate-300 tabular-nums">{opt.baselineActualIndoorTempC.toFixed(1)}°C</span>
          </div>
          <div>
            <span className="text-slate-500">Optimized (real simulator): </span>
            <span className="text-accent-teal font-semibold tabular-nums">{bd.actual_indoor_temp_c.toFixed(1)}°C</span>
          </div>
          <div>
            <span className="text-slate-500">Improvement: </span>
            <span className="text-accent-teal font-semibold tabular-nums">+{opt.improvementOverBaselineC.toFixed(1)}°C</span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[10px]">
        <div className="rounded border border-panel-border bg-[#0d1224] px-2 py-1.5 text-center">
          <div className="text-slate-500">Candidates Screened</div>
          <div className="text-sm text-slate-100 font-semibold tabular-nums">{opt.nCandidatesScreened.toLocaleString()}</div>
        </div>
        <div className="rounded border border-panel-border bg-[#0d1224] px-2 py-1.5 text-center">
          <div className="text-slate-500">Surrogate Screen Time</div>
          <div className="text-sm text-slate-100 font-semibold tabular-nums">{(opt.surrogateBatchPredictSeconds * 1000).toFixed(0)} ms</div>
        </div>
        <div className="rounded border border-panel-border bg-[#0d1224] px-2 py-1.5 text-center">
          <div className="text-slate-500">Top-K Surrogate Error</div>
          <div className="text-sm text-slate-100 font-semibold tabular-nums">±{opt.validation.mean_abs_surrogate_error_c.toFixed(2)}°C</div>
        </div>
      </div>
    </div>
  );
}

function SpeedupChart({ rows }) {
  const data = rows.map((r) => ({ batch: r.batch_size.toLocaleString(), speedup: r.speedup_x }));
  return (
    <div className="h-40">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" vertical={false} />
          <XAxis dataKey="batch" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
          <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
            formatter={(v) => [`${v.toFixed(2)}x`, 'Speedup vs. simulator loop']}
          />
          <Bar dataKey="speedup" radius={[3, 3, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.speedup >= 1 ? '#3fc47a' : '#e8664b'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function ResearchDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResearchSummary()
      .then(setSummary)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return null;
  if (!summary?.hasData) {
    return (
      <Panel title="ML Research Pipeline">
        <p className="text-[11px] text-slate-500">
          No research results found. Run <code className="text-slate-400">python -m research.run_all</code> inside{' '}
          <code className="text-slate-400">Ansys simulation/</code> to generate the dataset, train the surrogate
          models, run the optimization search, and populate this dashboard with real results.
        </p>
      </Panel>
    );
  }

  return (
    <>
      <Panel title="ML Research — Model Comparison" action={<span className="text-[10px] text-accent-blue">Surrogate for ANSYS-grade physics</span>}>
        {Object.entries(summary.modelComparison).map(([target, data]) => (
          <ModelComparisonTable key={target} target={target} data={data} />
        ))}
      </Panel>

      <Panel title="Feature Importance (permutation, best model)">
        {Object.entries(summary.featureImportance).map(([target, items]) => (
          <FeatureImportanceChart key={target} target={target} items={items} />
        ))}
      </Panel>

      {summary.optimization && (
        <Panel title="Surrogate-Driven Design Optimization">
          <OptimizationSummary opt={summary.optimization} />
        </Panel>
      )}

      {summary.speedupBenchmark && (
        <Panel title="Surrogate vs. Simulator Speedup" action={<span className="text-[10px] text-slate-400">measured, not assumed</span>}>
          <SpeedupChart rows={summary.speedupBenchmark} />
          <p className="text-[10px] text-slate-500 mt-1">
            At small batches the surrogate can be slower than the closed-form simulator itself (inference overhead);
            speedup grows at scale — real measured numbers, not a fixed claim.
          </p>
        </Panel>
      )}
    </>
  );
}
