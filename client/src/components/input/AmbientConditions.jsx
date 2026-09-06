import { LineChart, Line, BarChart, Bar, ResponsiveContainer, YAxis } from 'recharts';
import Panel from '../common/Panel';
import { ReadoutField } from '../common/Field';
import { useSimulation } from '../../context/SimulationContext';

function toChartData(series) {
  if (!series) return [];
  return series.hours.map((h, i) => ({ hour: h, value: series.values[i] }));
}

export default function AmbientConditions() {
  const { climate } = useSimulation();
  if (!climate) return null;

  const tempData = toChartData(climate.ambientTemp);
  const solarData = climate.solarFlux.hours.map((h, i) => ({
    hour: h,
    value: climate.solarFlux.values[i],
  }));

  return (
    <Panel title="Ambient Conditions">
      <div className="grid grid-cols-2 gap-2 mb-3">
        <ReadoutField label="Avg Temp" value={climate.avgTemp.toFixed(1)} unit="°C" />
        <ReadoutField label="Solar Irradiance" value={climate.solarIrradiance} unit="kWh/m²/y" />
        <ReadoutField label="Wind Speed" value={climate.windSpeed} unit="m/s" />
        <ReadoutField label="Cloud Cover" value={climate.cloudCover} unit="%" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="text-[10px] text-slate-500 mb-1">Ambient Temp Forecast</div>
          <div className="h-16 bg-[#0d1224] rounded border border-panel-border">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tempData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <YAxis hide domain={['dataMin - 2', 'dataMax + 2']} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#4f8bf2"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div>
          <div className="text-[10px] text-slate-500 mb-1">Solar Flux Forecast</div>
          <div className="h-16 bg-[#0d1224] rounded border border-panel-border">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={solarData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <YAxis hide />
                <Bar dataKey="value" fill="#e8a03f" radius={[1, 1, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="flex justify-between text-[9px] text-slate-600 mt-1 px-0.5">
        <span>0</span>
        <span>Time (24hrs)</span>
        <span>24</span>
      </div>
    </Panel>
  );
}
