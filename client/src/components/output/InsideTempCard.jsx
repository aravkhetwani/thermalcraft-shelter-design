import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from 'recharts';
import Panel from '../common/Panel';
import { useSimulation } from '../../context/SimulationContext';

export default function InsideTempCard() {
  const { result } = useSimulation();
  if (!result) return null;

  const data = result.insideTemp.hours.map((h, i) => ({
    hour: h,
    inside: result.insideTemp.values[i],
    outside: result.ambientTemp.values[i],
  }));

  return (
    <Panel title="1. Prediction of Inside Temperature">
      <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1 px-1">
        <span>Night</span>
        <span>Day</span>
      </div>
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2138" />
            <XAxis dataKey="hour" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#26304f' }} />
            <Tooltip
              contentStyle={{ background: '#12182b', border: '1px solid #26304f', fontSize: 11 }}
              labelFormatter={(h) => `Hour ${h}:00`}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Line type="monotone" dataKey="inside" name="Inside" stroke="#e8a03f" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="outside" name="Outside" stroke="#4f8bf2" strokeWidth={2} dot={false} strokeDasharray="4 3" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
