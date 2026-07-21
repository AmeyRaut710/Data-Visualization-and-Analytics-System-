import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import DynamicChart from '../components/dashboard/DynamicChart';
import KPICard from '../components/dashboard/KPICard';
import AIInsightsPanel from '../components/dashboard/AIInsightsPanel';
import DashboardTable from '../components/dashboard/DashboardTable';
import { Loader2, RefreshCw, AlertCircle, Download, Share2, Moon, Sun, Search, RotateCcw } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";

export default function PowerBIDashboardPage() {
  const { sessionId, activeSheet } = useAppContext();
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [activeFilters, setActiveFilters] = useState({});
  const [isFiltering, setIsFiltering] = useState(false);
  
  const [theme, setTheme] = useState('light');

  const fetchDashboard = async (filters = null) => {
    try {
      const sheetParam = activeSheet ? `?sheet=${encodeURIComponent(activeSheet)}` : '';
      let res;
      // Send merged activeFilters and temporary filters if any
      const mergedFilters = filters || activeFilters;
      if (Object.keys(mergedFilters).length > 0) {
        setIsFiltering(true);
        res = await axios.post(`${API_URL}/api/dashboard/${sessionId}/filter`, {
          filters: mergedFilters,
          sheet: activeSheet
        });
        setIsFiltering(false);
      } else {
        res = await axios.post(`${API_URL}/api/dashboard/${sessionId}/generate${sheetParam}`);
      }
      setConfig(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError("Failed to generate dashboard.");
      setLoading(false);
      setIsFiltering(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      setLoading(true);
      fetchDashboard();
    }
  }, [sessionId, activeSheet]);

  const handleFilter = (column, value) => {
    // Cross-filtering from chart clicks
    const newFilters = { ...activeFilters };
    if (!newFilters[column]) {
      newFilters[column] = [value];
    } else {
      if (newFilters[column].includes(value)) {
        newFilters[column] = newFilters[column].filter(v => v !== value);
        if (newFilters[column].length === 0) delete newFilters[column];
      } else {
        newFilters[column].push(value);
      }
    }
    setActiveFilters(newFilters);
    fetchDashboard(newFilters);
  };

  const handleSlicerChange = (col, val) => {
    const newFilters = { ...activeFilters };
    if (val === "" || val === null || val === undefined) {
      delete newFilters[col];
    } else if (typeof val === 'object' && !Array.isArray(val)) {
      newFilters[col] = val; // {min, max} object
    } else {
      newFilters[col] = [val]; // string wrapped in array for categorical
    }
    setActiveFilters(newFilters);
    fetchDashboard(newFilters);
  };

  const clearFilters = () => {
    setActiveFilters({});
    fetchDashboard({});
  };

  const toggleTheme = () => {
    setTheme(t => t === 'light' ? 'dark' : 'light');
  };

  if (!sessionId) return <Navigate to="/" />;

  if (loading && !config) return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center bg-slate-50">
      <Loader2 className="w-16 h-16 text-indigo-600 animate-spin mb-4" />
      <h2 className="text-2xl font-black text-slate-800">Generating Universal BI Dashboard...</h2>
      <p className="text-slate-500 mt-2">Analyzing dataset, determining optimal layouts, and finding insights.</p>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center bg-slate-50">
      <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
      <h2 className="text-2xl font-black text-slate-800">Error</h2>
      <p className="text-slate-500 mt-2">{error}</p>
    </div>
  );

  const isDark = theme === 'dark';
  const bgClass = isDark ? 'bg-slate-900 text-slate-100' : 'bg-slate-50 text-slate-900';
  const panelClass = isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200';
  const textClass = isDark ? 'text-slate-200' : 'text-slate-800';
  const mutedTextClass = isDark ? 'text-slate-400' : 'text-slate-500';

  // Group charts by type based on the universal layout rules
  const groupedCharts = {
    trend: config?.charts?.filter(c => ['line', 'area'].includes(c.type)) || [],
    category: config?.charts?.filter(c => ['donut', 'pie', 'treemap'].includes(c.type)) || [],
    bar: config?.charts?.filter(c => ['horizontal_bar', 'bar'].includes(c.type)) || [],
    correlation: config?.charts?.filter(c => ['heatmap'].includes(c.type)) || [],
    scatter: config?.charts?.filter(c => ['scatter'].includes(c.type)) || [],
    distribution: config?.charts?.filter(c => ['histogram'].includes(c.type)) || [],
    box: config?.charts?.filter(c => ['box'].includes(c.type)) || [],
    geo: config?.charts?.filter(c => ['map'].includes(c.type)) || [],
    other: config?.charts?.filter(c => !['line', 'area', 'donut', 'pie', 'treemap', 'horizontal_bar', 'bar', 'heatmap', 'scatter', 'histogram', 'box', 'map'].includes(c.type)) || []
  };

  const renderChartBlock = (charts, fullWidth = false) => {
    if (!charts || charts.length === 0) return null;
    return charts.map(chart => (
      <div key={chart.id} className={`${panelClass} border rounded-2xl shadow-sm overflow-hidden flex flex-col ${fullWidth ? 'w-full' : 'w-full'}`} style={{ height: '350px' }}>
        <DynamicChart chartConfig={chart} onFilter={handleFilter} isDark={isDark} />
      </div>
    ));
  };

  return (
    <div className={`h-full flex flex-col ${bgClass} overflow-hidden`}>
      
      {/* 0. Multi-Sheet Tab Bar (if applicable) */}
      {config?.sheets && config.sheets.length > 1 && (
        <div className={`${panelClass} border-b px-4 py-2 flex items-center gap-2 overflow-x-auto no-scrollbar`}>
          <span className={`text-xs font-bold uppercase mr-2 ${mutedTextClass}`}>Sheets:</span>
          {config.sheets.map(sheet => (
             <button 
                key={sheet}
                onClick={() => {
                  if (window.setActiveSheet) window.setActiveSheet(sheet); // Assume context provides this or we can navigate
                }}
                className={`px-4 py-1.5 rounded-full text-sm font-bold whitespace-nowrap transition-colors ${activeSheet === sheet ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'}`}
             >
               {sheet}
             </button>
          ))}
        </div>
      )}

      {/* 1. Dashboard Header */}
      <div className={`${panelClass} border-b px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4 z-20 shadow-sm shrink-0`}>
        <div>
          <h1 className="text-xl font-black flex items-center gap-2 tracking-tight">
            📊 AI GENERATED BUSINESS INTELLIGENCE DASHBOARD
          </h1>
          <p className={`text-sm mt-1 font-medium ${mutedTextClass}`}>
            Dataset: <span className={textClass}>{config?.title.replace(" BI Dashboard", "") || "Dataset"}</span> | 
            Type: <span className={textClass}>AI Detected</span> | 
            Generated: <span className={textClass}>{new Date().toLocaleString()}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isFiltering && (
            <div className="flex items-center gap-2 text-indigo-500 font-bold text-sm px-2">
              <RefreshCw className="w-4 h-4 animate-spin" /> Updating...
            </div>
          )}
          <button className={`p-2 rounded-lg border ${panelClass} hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors`}>
            <Download className="w-4 h-4" />
          </button>
          <button className={`p-2 rounded-lg border ${panelClass} hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors`}>
            <Share2 className="w-4 h-4" />
          </button>
          <button onClick={toggleTheme} className={`p-2 rounded-lg border ${panelClass} hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors`}>
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button onClick={() => fetchDashboard(activeFilters)} className={`flex items-center gap-2 px-4 py-2 font-bold text-sm rounded-lg border shadow-sm transition-colors bg-indigo-600 hover:bg-indigo-700 text-white border-transparent`}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 pb-20 space-y-6">
        
        {/* 2. Summary Row */}
        {config?.summary && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {[
              { label: "Total Rows", value: config.summary.rows },
              { label: "Total Cols", value: config.summary.cols },
              { label: "Numeric", value: config.summary.numeric },
              { label: "Categories", value: config.summary.categories },
              { label: "Date Cols", value: config.summary.date_cols },
              { label: "Quality %", value: `${config.summary.quality}%`, highlight: true },
            ].map((stat, i) => (
              <div key={i} className={`${panelClass} border rounded-xl p-4 text-center shadow-sm`} style={{minWidth: '100px'}}>
                <div className={`text-xs font-bold uppercase mb-1 ${mutedTextClass}`}>{stat.label}</div>
                <div className={`text-xl font-black ${stat.highlight ? 'text-emerald-500' : textClass}`}>{stat.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* 3. Global Filter / Slicer Bar */}
        <div className={`${panelClass} border rounded-2xl shadow-sm p-4 flex flex-col md:flex-row gap-4 items-center`}>
          <div className="font-bold flex items-center gap-2 shrink-0">
            Filters / Slicers
          </div>
          <div className="flex-1 flex flex-wrap gap-4 items-center">
             {config?.filters?.map((f, i) => (
                <div key={i} className="flex-shrink-0 w-48">
                  {(f.type === 'categorical' || f.type === 'category') ? (
                    <select 
                      className={`w-full p-2 text-sm rounded-lg border ${panelClass} outline-none focus:ring-2 focus:ring-indigo-500 font-medium`}
                      value={activeFilters[f.column]?.[0] || ""}
                      onChange={(e) => handleSlicerChange(f.column, e.target.value)}
                    >
                      <option value="">{f.label} ▼</option>
                      {f.options && f.options.map(opt => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  ) : f.type === 'range' ? (
                    <div className="px-2">
                       <div className="text-xs font-bold text-slate-500 mb-1 flex justify-between">
                         <span>{f.label}</span>
                         <span className="text-indigo-600">{activeFilters[f.column]?.max ?? f.max}</span>
                       </div>
                       <input 
                         type="range" 
                         className="w-full accent-indigo-600 cursor-pointer" 
                         min={f.min} max={f.max} 
                         value={activeFilters[f.column]?.max ?? f.max}
                         onChange={(e) => handleSlicerChange(f.column, { min: f.min, max: parseFloat(e.target.value) })}
                       />
                    </div>
                  ) : null}
                </div>
             ))}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button onClick={clearFilters} className={`flex items-center gap-1 px-3 py-2 text-sm font-bold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${mutedTextClass}`}>
              <RotateCcw className="w-4 h-4" /> Reset Filters
            </button>
          </div>
        </div>

        {/* 4. Row 1: KPI Cards & AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6 grid grid-cols-2 gap-4">
            {config?.kpis?.map(kpi => (
              <KPICard key={kpi.id} {...kpi} isDark={isDark} />
            ))}
          </div>
          <div className={`lg:col-span-6 ${panelClass} border rounded-2xl shadow-sm p-5 flex flex-col`}>
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <span className="text-indigo-500">✨</span> AI Insights
            </h3>
            <div className="flex-1 overflow-y-auto max-h-80">
              <AIInsightsPanel insights={config?.insights} isDark={isDark} />
            </div>
          </div>
        </div>

        {/* 5. Row 2: Trend Analysis (Line Chart) */}
        {groupedCharts.trend.length > 0 && (
          <div className="grid grid-cols-1 gap-6">
            {renderChartBlock(groupedCharts.trend, true)}
          </div>
        )}

        {/* 6. Row 3: Category Distribution & Top Categories */}
        {(groupedCharts.category.length > 0 || groupedCharts.bar.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groupedCharts.category.length > 0 ? renderChartBlock(groupedCharts.category) : renderChartBlock([groupedCharts.bar.pop()])}
            {groupedCharts.bar.length > 0 ? renderChartBlock(groupedCharts.bar) : (groupedCharts.category.length > 1 ? renderChartBlock([groupedCharts.category.pop()]) : <div/>)}
          </div>
        )}

        {/* 7. Row 4: Correlation Matrix & Scatter Plot */}
        {(groupedCharts.correlation.length > 0 || groupedCharts.scatter.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groupedCharts.correlation.length > 0 ? renderChartBlock(groupedCharts.correlation) : renderChartBlock([groupedCharts.scatter.pop()])}
            {groupedCharts.scatter.length > 0 ? renderChartBlock(groupedCharts.scatter) : <div/>}
          </div>
        )}

        {/* 8. Row 5: Histogram & Box Plot */}
        {(groupedCharts.distribution.length > 0 || groupedCharts.box.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groupedCharts.distribution.length > 0 ? renderChartBlock(groupedCharts.distribution) : renderChartBlock([groupedCharts.box.pop()])}
            {groupedCharts.box.length > 0 ? renderChartBlock(groupedCharts.box) : <div/>}
          </div>
        )}

        {/* Other charts that didn't fit categories cleanly */}
        {groupedCharts.other.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderChartBlock(groupedCharts.other)}
          </div>
        )}

        {/* 9. Row 7: Interactive Data Table */}
        <div className="w-full">
           <DashboardTable data={config?.sample_data} isDark={isDark} />
        </div>

      </div>
    </div>
  );
}
