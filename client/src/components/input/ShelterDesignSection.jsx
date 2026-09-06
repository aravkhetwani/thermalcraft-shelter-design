import Panel from '../common/Panel';
import { Select } from '../common/Field';
import { useSimulation } from '../../context/SimulationContext';

const SHAPES = [
  { value: 'rectangular', label: 'Rectangular', icon: '▭' },
  { value: 'dome', label: 'Dome', icon: '◗' },
  { value: 'custom', label: 'Custom', icon: '◈' },
];

const SIZES = [
  { value: 'small', label: 'Small', dims: '5×4×2.5m' },
  { value: 'medium', label: 'Medium', dims: '8×5×3m' },
  { value: 'large', label: 'Large', dims: '12×7×3.5m' },
];

const ORIENTATIONS = [
  { value: 'south', label: '180° South' },
  { value: 'north', label: '0° North' },
  { value: 'east', label: '90° East' },
  { value: 'west', label: '270° West' },
];

function ToggleButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex flex-col items-center gap-1 py-2 rounded border text-xs transition-colors ${
        active
          ? 'bg-accent-blue/15 border-accent-blue text-accent-blue'
          : 'bg-[#0d1224] border-panel-border text-slate-400 hover:border-slate-600'
      }`}
    >
      {children}
    </button>
  );
}

export default function ShelterDesignSection() {
  const { shape, setShape, size, setSize, orientation, setOrientation } = useSimulation();

  return (
    <Panel title="Shelter Design">
      <div className="mb-3">
        <div className="text-[11px] text-slate-500 mb-1.5">Shape</div>
        <div className="flex gap-2">
          {SHAPES.map((s) => (
            <ToggleButton key={s.value} active={shape === s.value} onClick={() => setShape(s.value)}>
              <span className="text-lg leading-none">{s.icon}</span>
              {s.label}
            </ToggleButton>
          ))}
        </div>
      </div>

      <div className="mb-3">
        <div className="text-[11px] text-slate-500 mb-1.5">Size (fixed presets)</div>
        <div className="flex gap-2">
          {SIZES.map((s) => (
            <ToggleButton key={s.value} active={size === s.value} onClick={() => setSize(s.value)}>
              {s.label}
              <span className="text-[9px] text-slate-500">{s.dims}</span>
            </ToggleButton>
          ))}
        </div>
      </div>

      <div>
        <div className="text-[11px] text-slate-500 mb-1.5">Orientation</div>
        <Select value={orientation} onChange={setOrientation} options={ORIENTATIONS} />
      </div>
    </Panel>
  );
}
