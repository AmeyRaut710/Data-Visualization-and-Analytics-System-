import { BrainCircuit, Eraser, LayoutDashboard, LineChart, Settings, Upload, BarChart2, CheckCircle2, AlertCircle } from 'lucide-react';
import React from 'react';
import { Link, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { useAppContext } from './context/AppContext';

// Placeholder imports for pages
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import WorkspacePage from './pages/WorkspacePage';

import SettingsPage from './pages/SettingsPage';
import TablePage from './pages/TablePage';
import VisualizationPage from './pages/VisualizationPage';
import PowerBIDashboardPage from './pages/PowerBIDashboardPage';

function App() {
  const { aiDashboardData, sheets, activeSheet, setActiveSheet, setOverview, allOverviews, toast, sessionId, hasGeneratedDashboard } = useAppContext();
  
  return (
    <Router>
      <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
          <div className="p-6 border-b border-slate-200">
            <h1 className="text-xl font-black text-indigo-600 tracking-tight flex items-center gap-2">
              <BrainCircuit className="w-6 h-6" />
              AI Analyst
            </h1>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <NavLink to="/" icon={<Upload />} label="Upload Data" />
            <NavLink to="/dashboard" icon={<LayoutDashboard />} label="Dashboard" />
            <NavLink to="/table" icon={<LayoutDashboard />} label="Table View" />
            <NavLink to="/workspace" icon={<Eraser />} label="Data Cleaning" />
            <NavLink to="/visualize" icon={<LineChart />} label="Visualizations" />
            {hasGeneratedDashboard && (
              <NavLink to="/powerbi-dashboard" icon={<BarChart2 />} label="Power BI Dashboard" />
            )}

          </nav>
          <div className="p-4 border-t border-slate-200">
            <NavLink to="/settings" icon={<Settings />} label="Settings" />
          </div>
        </aside>

        {/* Global Toast */}
        {toast && (
          <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] animate-in fade-in slide-in-from-top-4 duration-300">
            <div className={`px-6 py-3 rounded-2xl shadow-xl flex items-center gap-3 border ${toast.type === 'error' ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>
              {toast.type === 'error' ? <AlertCircle className="w-5 h-5"/> : <CheckCircle2 className="w-5 h-5"/>}
              <span className="font-bold text-sm">{toast.message}</span>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-hidden relative flex flex-col bg-slate-50">
          {sheets && sheets.length > 1 && (
            <div className="bg-white border-b border-slate-200 px-6 py-3 flex gap-2 overflow-x-auto shadow-sm z-10 shrink-0">
               {sheets.map(sheet => (
                  <button 
                    key={sheet}
                    onClick={() => {
                        setActiveSheet(sheet);
                        if (allOverviews && allOverviews[sheet]) {
                            setOverview(allOverviews[sheet]);
                        }
                    }}
                    className={`px-4 py-2 rounded-lg font-bold text-sm whitespace-nowrap transition-colors ${activeSheet === sheet ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                  >
                    {sheet}
                  </button>
               ))}
            </div>
          )}
          <div className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<UploadPage />} />
              <Route path="/workspace" element={<WorkspacePage />} />
              <Route path="/table" element={<TablePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              <Route path="/visualize" element={<VisualizationPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/powerbi-dashboard" element={<PowerBIDashboardPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

function NavLink({ to, icon, label }) {
  return (
    <Link to={to} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors font-medium">
      {React.cloneElement(icon, { className: "w-5 h-5" })}
      {label}
    </Link>
  );
}

export default App;
