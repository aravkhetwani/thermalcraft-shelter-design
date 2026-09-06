import { useSimulation } from '../context/SimulationContext';

export default function TopBar() {
  const { isRunning, progress, result } = useSimulation();

  return (
    <header className="h-14 shrink-0 border-b border-panel-border bg-panel flex items-center justify-between px-5">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded bg-gradient-to-br from-accent-blue to-accent-teal flex items-center justify-center text-xs font-bold">
          HA
        </div>
        <div>
          <h1 className="text-sm font-semibold text-slate-100 leading-none">
            High Altitude Shelter Model
          </h1>
          <p className="text-[10px] text-slate-500 leading-none mt-0.5">
            Passive thermal design studio — Ladakh region
          </p>
        </div>
      </div>

      <div className="flex-1 max-w-md mx-8">
        <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
          <span>Simulation Progress</span>
          <span>{isRunning ? `${Math.round(progress)}%` : result ? '100%' : '—'}</span>
        </div>
        <div className="h-1.5 rounded-full bg-[#0d1224] overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-teal transition-all duration-200"
            style={{ width: `${isRunning ? progress : result ? 100 : 0}%` }}
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[10px] px-2 py-1 rounded-full bg-[#0d1224] border border-panel-border text-accent-teal font-medium tracking-wide">
          Data Source: {result?.source === 'mock' ? 'Mock' : result?.source || 'Mock'}
        </span>
        <span className="text-xs text-slate-500 font-semibold tracking-widest">SIH 2026</span>
      </div>
    </header>
  );
}
