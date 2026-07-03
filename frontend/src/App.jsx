import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Upload, LayoutDashboard, Eraser, LineChart, BrainCircuit, MessageSquare, Settings } from 'lucide-react';

// Placeholder imports for pages
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import WorkspacePage from './pages/WorkspacePage';

import VisualizationPage from './pages/VisualizationPage';
import SettingsPage from './pages/SettingsPage';
import TablePage from './pages/TablePage';

function App() {
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
            <NavLink to="/workspace" icon={<Eraser />} label="Interactive Workspace" />
            <NavLink to="/table" icon={<LayoutDashboard />} label="Table View" />
            <NavLink to="/dashboard" icon={<LayoutDashboard />} label="Dashboard" />

            <NavLink to="/visualize" icon={<LineChart />} label="Visualizations" />
          </nav>
          <div className="p-4 border-t border-slate-200">
            <NavLink to="/settings" icon={<Settings />} label="Settings" />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/workspace" element={<WorkspacePage />} />
            <Route path="/table" element={<TablePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            <Route path="/visualize" element={<VisualizationPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
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
