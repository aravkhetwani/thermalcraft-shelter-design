import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  fetchClimate,
  fetchComparison,
  fetchHistory,
  fetchMaterials,
  fetchRegions,
  fetchSimulationResult,
  runSimulation,
} from '../api/client';

const SimulationContext = createContext(null);

const DATE_RANGE_PRESETS = {
  winter: [
    { value: 'jan1-7', label: 'Jan 1 – Jan 7' },
    { value: 'jan8-14', label: 'Jan 8 – Jan 14' },
    { value: 'dec15-21', label: 'Dec 15 – Dec 21' },
  ],
  summer: [
    { value: 'jul1-7', label: 'Jul 1 – Jul 7' },
    { value: 'jul8-14', label: 'Jul 8 – Jul 14' },
    { value: 'jun20-26', label: 'Jun 20 – Jun 26' },
  ],
};

let layerUid = 0;
const nextLayerUid = () => `layer-${++layerUid}-${Date.now()}`;

export function SimulationProvider({ children }) {
  const [regions, setRegions] = useState([]);
  const [region, setRegion] = useState('ladakh');
  const [season, setSeason] = useState('winter');
  const [dateRange, setDateRange] = useState('jan1-7');

  const [shape, setShape] = useState('dome');
  const [size, setSize] = useState('medium');
  const [orientation, setOrientation] = useState('south');

  // Openings: doors/windows/ventilation — feeds heat-loss-through-openings calc.
  const [doors, setDoors] = useState(1);
  const [windows, setWindows] = useState(2);
  const [ventilation, setVentilation] = useState('medium');
  const openings = useMemo(() => ({ doors, windows, ventilation }), [doors, windows, ventilation]);

  const [materials, setMaterials] = useState([]);
  const [climate, setClimate] = useState(null);

  // Wall layers: ordered list of { uid, materialId }, supports composite walls.
  const [wallLayers, setWallLayers] = useState([]);
  const [appliedMaterialCombo, setAppliedMaterialCombo] = useState('rammed-earth');

  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isApplyingMaterial, setIsApplyingMaterial] = useState(false);
  const [progress, setProgress] = useState(0);

  const [comparison, setComparison] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [history, setHistory] = useState([]);

  // Load the region + material libraries once via the API layer (never hardcode inline).
  useEffect(() => {
    fetchRegions().then(setRegions);
    fetchMaterials().then((data) => {
      setMaterials(data);
      if (data.length) {
        setWallLayers([{ uid: nextLayerUid(), materialId: data[0].id }]);
      }
    });
    fetchHistory(10).then(setHistory);
  }, []);

  // Re-fetch the climate profile whenever region/season changes.
  useEffect(() => {
    fetchClimate(region, season).then(setClimate);
  }, [region, season]);

  useEffect(() => {
    const presets = DATE_RANGE_PRESETS[season] || DATE_RANGE_PRESETS.winter;
    setDateRange(presets[0].value);
  }, [season]);

  const comboKey = useMemo(
    () => wallLayers.map((l) => l.materialId).join('+') || 'rammed-earth',
    [wallLayers]
  );

  const fetchResultFor = useCallback(
    async (materialCombo) => {
      const data = await fetchSimulationResult({ materialCombo, orientation, size, shape, region, season, openings });
      setResult(data);
    },
    [orientation, size, shape, region, season, openings]
  );

  const loadComparison = useCallback(async () => {
    setIsComparing(true);
    try {
      const data = await fetchComparison({ region, season, size, openings });
      setComparison(data);
    } finally {
      setIsComparing(false);
    }
  }, [region, season, size, openings]);

  // Load an initial result as soon as materials are ready, and whenever
  // region/season/size/shape/orientation/openings change.
  useEffect(() => {
    if (wallLayers.length) fetchResultFor(comboKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [materials.length, region, season, size, shape, orientation, openings]);

  // Re-run the optimization/comparison sweep whenever the site/geometry context changes.
  useEffect(() => {
    loadComparison();
  }, [loadComparison]);

  const addLayer = useCallback((materialId) => {
    setWallLayers((layers) => [...layers, { uid: nextLayerUid(), materialId }]);
  }, []);

  const removeLayer = useCallback((uid) => {
    setWallLayers((layers) => (layers.length > 1 ? layers.filter((l) => l.uid !== uid) : layers));
  }, []);

  const applyMaterial = useCallback(async () => {
    setIsApplyingMaterial(true);
    try {
      setAppliedMaterialCombo(comboKey);
      await fetchResultFor(comboKey);
    } finally {
      setIsApplyingMaterial(false);
    }
  }, [comboKey, fetchResultFor]);

  const runFullSimulation = useCallback(async () => {
    setIsRunning(true);
    setProgress(0);
    const tick = setInterval(() => {
      setProgress((p) => Math.min(92, p + Math.random() * 18 + 6));
    }, 180);
    try {
      const data = await runSimulation({ materialCombo: comboKey, orientation, size, shape, region, season, openings });
      setAppliedMaterialCombo(comboKey);
      setProgress(100);
      setResult(data);
      fetchHistory(10).then(setHistory);
    } finally {
      clearInterval(tick);
      setTimeout(() => {
        setIsRunning(false);
        setProgress(0);
      }, 350);
    }
  }, [comboKey, orientation, size, shape, region, season, openings]);

  const value = {
    regions,
    region,
    setRegion,
    season,
    setSeason,
    dateRange,
    setDateRange,
    dateRangePresets: DATE_RANGE_PRESETS[season] || DATE_RANGE_PRESETS.winter,

    shape,
    setShape,
    size,
    setSize,
    orientation,
    setOrientation,

    doors,
    setDoors,
    windows,
    setWindows,
    ventilation,
    setVentilation,
    openings,

    materials,
    climate,

    wallLayers,
    addLayer,
    removeLayer,
    comboKey,
    appliedMaterialCombo,
    applyMaterial,
    isApplyingMaterial,

    result,
    isRunning,
    progress,
    runFullSimulation,

    comparison,
    isComparing,
    loadComparison,

    history,
  };

  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>;
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider');
  return ctx;
}
