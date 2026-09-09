import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

export default function RunHistoryCard() {
  const { history } = useSimulation();
  if (!history?.length) return null;

  return (
    <Panel title="Run History" action={<span className="text-[10px] text-slate-400">Persisted (SQLite)</span>}>
      <div className="space-y-1.5 max-h-40 overflow-y-auto">
        {history.map((run) => (
          <div
            key={run.id}
            className="flex items-center justify-between bg-[#0d1224] border border-panel-border rounded px-2.5 py-1.5"
          >
            <div className="min-w-0">
              <div className="text-[11px] text-slate-200 truncate">
                {run.shape} · {run.orientation} · {run.materialCombo}
              </div>
              <div className="text-[9px] text-slate-500">
                {run.region}/{run.season} · {new Date(run.createdAt).toLocaleString()}
              </div>
            </div>
            <div className="text-xs font-semibold text-accent-teal shrink-0 ml-2">{run.efficiencyScore}%</div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
