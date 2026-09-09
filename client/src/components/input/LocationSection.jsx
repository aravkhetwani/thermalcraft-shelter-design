import Panel from '../common/Panel';
import { Select } from '../common/Field';
import { useSimulation } from '../../context/SimulationContext';

const SEASONS = [
  { value: 'winter', label: 'Winter' },
  { value: 'summer', label: 'Summer' },
];

export default function LocationSection() {
  const {
    regions,
    region,
    setRegion,
    season,
    setSeason,
    dateRange,
    setDateRange,
    dateRangePresets,
    climate,
  } = useSimulation();

  const regionOptions = regions.length
    ? regions.map((r) => ({ value: r.value, label: r.label }))
    : [{ value: 'ladakh', label: 'Ladakh' }];
  const activeRegion = regions.find((r) => r.value === region);

  return (
    <Panel title="Location Data" action={<span className="text-[10px] text-accent-blue">Live weather</span>}>
      <div className="grid grid-cols-2 gap-2 mb-2">
        <Select value={region} onChange={setRegion} options={regionOptions} />
        <Select value={season} onChange={setSeason} options={SEASONS} />
      </div>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="text-[11px] text-slate-500 flex items-center">Latitude/Longitude</div>
        <div className="text-[11px] text-slate-300 font-mono text-right">
          {activeRegion ? `${activeRegion.latitude}° N · ${activeRegion.longitude}° E` : '—'}
        </div>
      </div>
      {activeRegion && (
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="text-[11px] text-slate-500 flex items-center">Elevation</div>
          <div className="text-[11px] text-slate-300 font-mono text-right">{activeRegion.elevationM} m</div>
        </div>
      )}
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
