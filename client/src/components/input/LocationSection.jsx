import Panel from '../common/Panel';
import { Select } from '../common/Field';
import { useSimulation } from '../../context/SimulationContext';

const REGIONS = [{ value: 'ladakh', label: 'Ladakh' }];
const SEASONS = [
  { value: 'winter', label: 'Winter' },
  { value: 'summer', label: 'Summer' },
];

export default function LocationSection() {
  const { region, setRegion, season, setSeason, dateRange, setDateRange, dateRangePresets, climate } =
    useSimulation();

  return (
    <Panel title="Location Data" action={<span className="text-[10px] text-accent-blue">Dropdown</span>}>
      <div className="grid grid-cols-2 gap-2 mb-2">
        <Select value={region} onChange={setRegion} options={REGIONS} />
        <Select value={season} onChange={setSeason} options={SEASONS} />
      </div>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="text-[11px] text-slate-500 flex items-center">Longitude/Latitude</div>
        <div className="text-[11px] text-slate-300 font-mono text-right">-18.994 · -132.739</div>
      </div>
      <div>
        <div className="text-[11px] text-slate-500 mb-1">Date Range Selector</div>
        <Select value={dateRange} onChange={setDateRange} options={dateRangePresets} />
      </div>
      {climate && (
        <p className="text-[10px] text-slate-500 mt-2">{climate.label}</p>
      )}
    </Panel>
  );
}
