import { AnimatePresence, motion } from 'framer-motion';
import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

function MaterialCard({ material, onAdd }) {
  return (
    <div className="flex items-center gap-2.5 bg-[#0d1224] border border-panel-border rounded px-2.5 py-2 hover:border-slate-600 transition-colors">
      <span
        className="w-3 h-3 rounded-sm shrink-0"
        style={{ backgroundColor: material.color }}
      />
      <div className="flex-1 min-w-0">
        <div className="text-xs text-slate-200 font-medium truncate">{material.name}</div>
        <div className="text-[9px] text-slate-500 tabular-nums">
          {material.thicknessCm}cm · ρ{material.density} · k{material.thermalConductivity} · c
          {material.heatCapacity}
        </div>
      </div>
      <button
        onClick={() => onAdd(material.id)}
        className="text-[10px] px-2 py-1 rounded bg-accent-blue/15 text-accent-blue border border-accent-blue/30 hover:bg-accent-blue/25 transition-colors shrink-0"
      >
        + Add Layer
      </button>
    </div>
  );
}

function WallLayerRow({ layer, material, onRemove, disabled }) {
  if (!material) return null;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -16, height: 0 }}
      animate={{ opacity: 1, x: 0, height: 'auto' }}
      exit={{ opacity: 0, x: 16, height: 0 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}
      className="flex items-center gap-2 overflow-hidden"
    >
      <div
        className="h-6 rounded-sm flex-1"
        style={{ backgroundColor: material.color, opacity: 0.85 }}
        title={`${material.name} — ${material.thicknessCm}cm`}
      />
      <span className="text-[10px] text-slate-400 w-24 truncate">{material.name}</span>
      <button
        onClick={() => onRemove(layer.uid)}
        disabled={disabled}
        className="text-[10px] text-slate-500 hover:text-accent-red disabled:opacity-20 disabled:cursor-not-allowed w-4"
      >
        ✕
      </button>
    </motion.div>
  );
}

export default function MaterialSystem() {
  const {
    materials,
    wallLayers,
    addLayer,
    removeLayer,
    applyMaterial,
    isApplyingMaterial,
    comboKey,
    appliedMaterialCombo,
  } = useSimulation();

  const materialsById = Object.fromEntries(materials.map((m) => [m.id, m]));
  const isDirty = comboKey !== appliedMaterialCombo;

  return (
    <Panel title="Material Properties">
      <div className="text-[11px] text-slate-500 mb-1.5">Choose the constituent components</div>
      <div className="space-y-1.5 mb-3">
        {materials.map((m) => (
          <MaterialCard key={m.id} material={m} onAdd={addLayer} />
        ))}
      </div>

      <div className="text-[11px] text-slate-500 mb-1.5">Wall Layer Stack (outside → inside)</div>
      <div className="bg-[#0d1224] border border-panel-border rounded p-2 space-y-1.5 min-h-[52px]">
        <AnimatePresence initial={false} mode="popLayout">
          {wallLayers.map((layer) => (
            <WallLayerRow
              key={layer.uid}
              layer={layer}
              material={materialsById[layer.materialId]}
              onRemove={removeLayer}
              disabled={wallLayers.length <= 1}
            />
          ))}
        </AnimatePresence>
      </div>

      <button
        onClick={applyMaterial}
        disabled={isApplyingMaterial}
        className={`w-full mt-3 py-2 rounded text-sm font-medium transition-colors ${
          isDirty
            ? 'bg-accent-teal/20 border border-accent-teal text-accent-teal hover:bg-accent-teal/30'
            : 'bg-[#0d1224] border border-panel-border text-slate-500'
        } disabled:opacity-60`}
      >
        {isApplyingMaterial ? 'Applying…' : 'Apply Material'}
      </button>
    </Panel>
  );
}
