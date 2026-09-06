import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

export default function EfficiencyCard() {
  const { result } = useSimulation();
  if (!result) return null;

  return (
    <Panel title="Design Efficiency Summary">
      <div className="flex items-center gap-4">
        <div className="relative w-16 h-16 shrink-0">
          <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
            <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1a2138" strokeWidth="3" />
            <circle
              cx="18"
              cy="18"
              r="15.5"
              fill="none"
              stroke="#3fb6c4"
              strokeWidth="3"
              strokeDasharray={`${(result.efficiencyScore / 100) * 97.4} 97.4`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-accent-teal">
            {result.efficiencyScore}%
          </div>
        </div>
        <div className="flex-1 space-y-1">
          <div>
            <div className="text-[9px] text-slate-500 uppercase">Most Efficient Combo</div>
            <div className="text-xs text-slate-200 font-medium">{result.mostEfficientCombo}</div>
          </div>
          <div>
            <div className="text-[9px] text-slate-500 uppercase">Energy Saved</div>
            <div className="text-sm text-accent-teal font-semibold">{result.energySavedPercent}%</div>
          </div>
        </div>
      </div>
    </Panel>
  );
}
