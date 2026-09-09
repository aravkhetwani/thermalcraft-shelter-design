import Panel from '../common/Panel';
import ShelterViewport from './ShelterViewport';
import InsideTempCard from './InsideTempCard';
import SolarEnergyCard from './SolarEnergyCard';
import HeatFlowCard from './HeatFlowCard';
import EfficiencyCard from './EfficiencyCard';
import ComparisonCard from './ComparisonCard';
import RunHistoryCard from './RunHistoryCard';
import { useSimulation } from '../../context/SimulationContext';

export default function OutputDashboard() {
  const { result, isRunning } = useSimulation();

  return (
    <div className="flex-1 h-full overflow-y-auto p-3">
      <div className="panel-label px-1 mb-3">Output Dashboard — Thermal Analysis Results</div>

      <div className="grid grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)] gap-3">
        <div className="space-y-3 min-w-0">
          <Panel title="3D View" className="relative">
            <div className="h-[360px] -m-4 relative">
              <ShelterViewport />
              {isRunning && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-[1px]">
                  <div className="text-sm text-slate-200 font-medium animate-pulse">
                    Running simulation…
                  </div>
                </div>
              )}
            </div>
          </Panel>
          {result ? <EfficiencyCard /> : null}
          <ComparisonCard />
          <RunHistoryCard />
        </div>

        <div className="space-y-3 min-w-0">
          <InsideTempCard />
          <SolarEnergyCard />
          <HeatFlowCard />
        </div>
      </div>
    </div>
  );
}
