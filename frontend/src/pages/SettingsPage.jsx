import { useAppContext } from '../context/AppContext';
import { Settings, DownloadCloud, Trash2, ShieldCheck } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


export default function SettingsPage() {
  const { sessionId, clearSession } = useAppContext();
  const navigate = useNavigate();

  const handleExport = (type) => {
    if (!sessionId) return;
    window.open(`${API_URL}/api/export/${sessionId}/${type}`, '_blank');
  };

  const handleClear = async () => {
    if (sessionId) {
      try {
        await axios.delete(`${API_URL}/api/session/${sessionId}`);
      } catch (err) {
        console.error(err);
      }
    }
    clearSession();
    navigate('/');
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-slate-900">Settings & Actions</h1>
        <p className="text-slate-500 mt-2">Manage your current session and download reports.</p>
      </div>

      <div className="space-y-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-xl font-bold flex items-center gap-2 mb-4">
            <DownloadCloud className="text-indigo-500" /> Export Data
          </h3>
          <p className="text-slate-500 mb-6">Download your cleaned dataset or a comprehensive HTML report containing your visualizations and quality scores.</p>
          <div className="flex gap-4">
            <button 
              onClick={() => handleExport('csv')}
              disabled={!sessionId}
              className="bg-indigo-50 text-indigo-700 font-bold px-6 py-3 rounded-xl border border-indigo-200 hover:bg-indigo-100 disabled:opacity-50"
            >
              Export to CSV
            </button>
            <button 
              onClick={() => handleExport('excel')}
              disabled={!sessionId}
              className="bg-indigo-50 text-indigo-700 font-bold px-6 py-3 rounded-xl border border-indigo-200 hover:bg-indigo-100 disabled:opacity-50"
            >
              Export to Excel
            </button>
            <button 
              onClick={() => handleExport('html')}
              disabled={!sessionId}
              className="bg-indigo-50 text-indigo-700 font-bold px-6 py-3 rounded-xl border border-indigo-200 hover:bg-indigo-100 disabled:opacity-50"
            >
              Export HTML Report
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-rose-200 shadow-sm border-l-4 border-l-rose-500">
          <h3 className="text-xl font-bold flex items-center gap-2 mb-4 text-rose-600">
            <ShieldCheck className="text-rose-500" /> Privacy & Danger Zone
          </h3>
          <p className="text-slate-500 mb-6">
            Your data is stored <strong>strictly in-memory (RAM)</strong>. It is never saved to the database or hard drive. 
            Clicking the button below will permanently wipe your session from memory.
          </p>
          <button 
            onClick={handleClear}
            className="flex items-center gap-2 bg-rose-600 text-white font-bold px-6 py-3 rounded-xl hover:bg-rose-700"
          >
            <Trash2 className="w-5 h-5" /> Terminate Session & Delete Data
          </button>
        </div>
      </div>
    </div>
  );
}
