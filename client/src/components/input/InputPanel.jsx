import LocationSection from './LocationSection';
import AmbientConditions from './AmbientConditions';
import ShelterDesignSection from './ShelterDesignSection';
import MaterialSystem from './MaterialSystem';
import { useSimulation } from '../../context/SimulationContext';

export default function InputPanel() {
  const { runFullSimulation, isRunning } = useSimulation();

  return (
    <div className="w-[360px] shrink-0 h-full overflow-y-auto p-3 space-y-3 border-r border-panel-border">
      <div className="panel-label px-1">Input Control Panel — Ladakh Region</div>
      <LocationSection />
      <AmbientConditions />
      <ShelterDesignSection />
      <MaterialSystem />

      <div className="grid grid-cols-2 gap-2 pt-1">
        <button className="py-2 rounded text-xs border border-panel-border text-slate-400 hover:border-slate-600 transition-colors">
          Load Region Data
        </button>
        <button className="py-2 rounded text-xs border border-panel-border text-slate-400 hover:border-slate-600 transition-colors">
          Define Design
        </button>
      </div>
      <button
        onClick={runFullSimulation}
        disabled={isRunning}
        className="w-full py-2.5 rounded font-semibold text-sm bg-accent-blue text-white hover:bg-blue-500 transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-accent-blue/20"
      >
        {isRunning ? 'Running Simulation…' : 'Run Simulation'}
      </button>
    </div>
  );
}
