import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

export default function SolarEnergyCard() {
  const { result } = useSimulation();
  if (!result) return null;

  const data = result.solarEnergy.hours.map((h, i) => ({
    hour: h,
    kwh: result.solarEnergy.valuesKwh[i],
  }));
  const maxKwh = Math.max(...data.map((d) => d.kwh));

  return (
    <Panel
      title="2. Prediction of Solar Thermal Energy"
      action={<span className="text-xs text-accent-orange font-semibold">Total: {result.totalSolarKwh} kWh</span>}
    >
      <div className="flex justify-between text-[9px] text-slate-500 mb-1 px-1">
        <span>Peak hours</span>
        <span>9am–4pm</span>
        <span>Peak hours</span>
      </div>
      <div className="h-28">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" />
            <XAxis dataKey="hour" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <Tooltip
              contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
              formatter={(v) => [`${v} kWh`, 'Energy']}
              labelFormatter={(h) => `Hour ${h}:00`}
            />
            <Bar dataKey="kwh" radius={[2, 2, 0, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.kwh === maxKwh && maxKwh > 0 ? '#e8a03f' : '#3a4a78'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
