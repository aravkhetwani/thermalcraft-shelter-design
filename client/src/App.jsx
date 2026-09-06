import { SimulationProvider } from './context/SimulationContext';
import TopBar from './components/TopBar';
import InputPanel from './components/input/InputPanel';
import OutputDashboard from './components/output/OutputDashboard';

export default function App() {
  return (
    <SimulationProvider>
      <div className="h-screen w-screen flex flex-col bg-base overflow-hidden">
        <TopBar />
        <div className="flex-1 flex min-h-0">
          <InputPanel />
          <OutputDashboard />
        </div>
      </div>
    </SimulationProvider>
  );
}
