import { useEffect, useState } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import { Database, Hash, Columns, FileText, AlertTriangle, CheckCircle, ShieldAlert, Sparkles, Copy, DownloadCloud, Activity, Bot, Search, LayoutGrid, CheckCircle2, AlertOctagon } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


export default function DashboardPage() {
  const { sessionId, overview } = useAppContext();
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingPhase, setLoadingPhase] = useState(0);

  const loadingMessages = [
    "Analyzing Dataset Size & Structure...",
    "Scanning via Polars Vectorized Engine...",
    "Validating Extreme Scale Missing Values...",
    "Hashing Columns for Exact Duplicates...",
    "Aggregating 1,000,000+ Row Data Quality Profiles...",
    "Generating Advanced Charts & Dashboard..."
  ];

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setLoadingPhase(prev => (prev < loadingMessages.length - 1 ? prev + 1 : prev));
      }, 3500); // Shift message every 3.5 seconds
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (sessionId) {
      axios.get(`${API_URL}/api/quality/${sessionId}`)
        .then(res => {
          setQuality(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          // If session expired or 404, force user back to upload
          alert("Session expired or data not found. Please upload your file again.");
          window.location.href = "/";
        });
    }
  }, [sessionId]);

  if (!sessionId) return <Navigate to="/" />;

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center min-h-[70vh]">
      <div className="w-24 h-24 relative mb-8">
        <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center text-indigo-600 font-black text-xl">
          {Math.min(99, Math.floor((loadingPhase / loadingMessages.length) * 100))}%
        </div>
      </div>
      <h2 className="text-3xl font-black text-slate-800 mb-3">{loadingMessages[loadingPhase]}</h2>
      <p className="text-slate-500 font-medium">Running Enterprise Polars Multi-Threaded Engine</p>
      
      <div className="mt-12 w-full max-w-md bg-slate-100 rounded-full h-3 overflow-hidden">
        <div className="bg-indigo-600 h-full transition-all duration-1000 ease-out" style={{width: `${((loadingPhase + 1) / loadingMessages.length) * 100}%`}}></div>
      </div>
    </div>
  );

  const { metrics, scores, distributions, anomalies, ai_health_report } = quality || {};
  
  const gaugeData = [
    { name: 'Score', value: scores?.overall_cleanliness || 0 },
    { name: 'Missing', value: 100 - (scores?.overall_cleanliness || 0) }
  ];
  const GAUGE_COLORS = [scores?.overall_cleanliness > 90 ? '#10b981' : scores?.overall_cleanliness > 75 ? '#f59e0b' : '#ef4444', '#f1f5f9'];

  const missingChartData = Object.entries(distributions?.missing_per_column || {}).map(([col, count]) => ({
    name: col,
    Missing: count
  }));

  const duplicateCountChartData = Object.entries(distributions?.duplicate_count_by_col || {})
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([col, count]) => ({
      name: col,
      Count: count
    }));

  const duplicatePctChartData = Object.entries(distributions?.duplicate_pct_by_col || {})
    .filter(([_, pct]) => pct > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([col, pct]) => ({
      name: col,
      Percentage: pct
    }));

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-20">
      {/* Header Profile */}
      <div className="bg-slate-900 rounded-3xl p-8 shadow-2xl text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 rounded-full mix-blend-screen filter blur-[80px] opacity-30"></div>
        <div className="flex flex-col md:flex-row justify-between items-center relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-bold uppercase tracking-wider mb-4">
              <Sparkles className="w-4 h-4 text-indigo-400" /> Multi-Threaded Engine Output
            </div>
            <h1 className="text-4xl font-black mb-2">Data Quality Profile</h1>
            <p className="text-slate-400">{overview?.filename} • {(overview?.file_size_bytes / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          
          <div className="mt-6 md:mt-0 flex gap-4">
            <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 p-6 rounded-2xl flex items-center gap-6">
              <div className="w-24 h-24 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={gaugeData} cx="50%" cy="50%" innerRadius={35} outerRadius={45} startAngle={90} endAngle={-270} dataKey="value" stroke="none">
                      {gaugeData.map((entry, index) => <Cell key={`cell-${index}`} fill={GAUGE_COLORS[index]} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-xl font-black leading-none">{scores?.overall_cleanliness}%</span>
                </div>
              </div>
              <div>
                <div className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Overall Cleanliness</div>
                <div className="text-emerald-400 font-medium text-sm flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Ready for Analysis
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Total Rows" value={metrics?.total_rows} icon={<Hash />} />
        <StatCard label="Total Columns" value={metrics?.total_cols} icon={<Columns />} />
        <StatCard label="Exact Duplicates" value={metrics?.total_exact_duplicates} pct={scores?.duplicate_pct} icon={<Copy />} color="amber" alert={metrics?.total_exact_duplicates > 0} />
        <StatCard label="Outliers" value={metrics?.total_outliers} pct={scores?.outlier_pct} icon={<AlertTriangle />} color="rose" alert={metrics?.total_outliers > 0} />
        <StatCard label="Missing Values" value={metrics?.total_missing_values} pct={scores?.missing_pct} icon={<FileText />} color="rose" alert={metrics?.total_missing_values > 0} />
        <StatCard label="Empty Cells" value={metrics?.total_empty_cells} pct={scores?.empty_pct} icon={<FileText />} color="orange" alert={metrics?.total_empty_cells > 0} />
      </div>

      {/* Pillars of Quality */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-xl shadow-slate-200/50">
        <h2 className="text-2xl font-black text-slate-800 mb-6 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-indigo-500" /> Five Pillars of Data Quality
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <ScorePillar label="Completeness" score={scores?.completeness} />
          <ScorePillar label="Consistency" score={scores?.consistency} />
          <ScorePillar label="Validity" score={scores?.validity} />
          <ScorePillar label="Uniqueness" score={scores?.uniqueness} />
          <ScorePillar label="Accuracy" score={scores?.accuracy} />
        </div>
      </div>

      {/* Exact Duplicate Module */}
      <div className="bg-amber-50/30 border border-amber-200 rounded-3xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-amber-100 text-amber-600 rounded-xl"><Copy className="w-6 h-6" /></div>
          <div>
            <h2 className="text-2xl font-black text-slate-800">Exact Duplicate Detection</h2>
            <p className="text-slate-500 font-medium">100% exact character-for-character matching. No estimation.</p>
          </div>
        </div>

        {/* Duplicate Summary Text */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mb-8 flex flex-col md:flex-row gap-6 md:items-center">
          <div className="flex-1">
             <h3 className="font-bold text-slate-800 mb-2">Duplicate Summary</h3>
             <p className="text-slate-600 text-sm">The dataset contains <span className="font-bold text-slate-800">{metrics?.total_exact_duplicates?.toLocaleString()} fully duplicated rows</span>.</p>
             <p className="text-slate-600 text-sm">There are <span className="font-bold text-slate-800">{anomalies?.columns_containing_duplicates?.toLocaleString()} columns</span> that contain repeating identical values.</p>
             {anomalies?.col_duplicates_details?.length > 0 && (
               <p className="text-slate-600 text-sm mt-3 bg-amber-50 p-3 rounded-lg border border-amber-100">
                 <span className="font-bold text-amber-800">Explanation:</span> The column <b>{anomalies.col_duplicates_details[0].column}</b> contains duplicate values. For example, the value <b>"{anomalies.col_duplicates_details[0].value}"</b> appears {anomalies.col_duplicates_details[0].total_appearances} times, including in rows {anomalies.col_duplicates_details[0].rows.slice(0, 4).join(', ')}.
               </p>
             )}
          </div>
          <div className="grid grid-cols-2 gap-4 shrink-0">
             <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-center">
                <div className="text-3xl font-black text-amber-500">{metrics?.total_exact_duplicates?.toLocaleString()}</div>
                <div className="text-xs font-bold text-slate-400 uppercase mt-1">Total Duplicate Rows</div>
             </div>
             <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-center">
                <div className="text-3xl font-black text-indigo-500">{anomalies?.columns_containing_duplicates?.toLocaleString()}</div>
                <div className="text-xs font-bold text-slate-400 uppercase mt-1">Columns w/ Duplicates</div>
             </div>
          </div>
        </div>

        {/* Duplicate Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-800 mb-6">Top Columns by Duplicate Count</h3>
            {duplicateCountChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={duplicateCountChartData} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" tick={{fontSize: 12}} width={100} />
                  <RechartsTooltip cursor={{fill: '#f1f5f9'}} />
                  <Bar dataKey="Count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-slate-400 text-sm text-center py-10">No column duplicates found.</p>}
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-800 mb-6">Top Columns by Duplicate Percentage</h3>
            {duplicatePctChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={duplicatePctChartData} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" unit="%" />
                  <YAxis dataKey="name" type="category" tick={{fontSize: 12}} width={100} />
                  <RechartsTooltip cursor={{fill: '#f1f5f9'}} />
                  <Bar dataKey="Percentage" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-slate-400 text-sm text-center py-10">No column duplicates found.</p>}
          </div>
        </div>

        {/* Duplicate Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 bg-slate-50 border-b border-slate-200">
              <h3 className="font-bold text-slate-800">Duplicate Row Details</h3>
            </div>
            <div className="overflow-auto max-h-[400px]">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-xs text-slate-500 uppercase sticky top-0 border-b border-slate-200 shadow-sm z-10">
                  <tr>
                    <th className="px-4 py-3">Original Row</th>
                    <th className="px-4 py-3">Exact Duplicate Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {anomalies?.row_duplicates_details?.length > 0 ? anomalies.row_duplicates_details.map((row, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-900">Row {row.original_row}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {row.duplicate_rows.join(', ')} 
                        {row.has_more && <span className="text-amber-500 font-bold ml-1">...and {row.total_duplicates - row.duplicate_rows.length} more</span>}
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="2" className="px-4 py-8 text-center text-slate-400 font-medium">{metrics?.total_rows > 500000 ? "Row extraction disabled for extreme datasets." : "No identical row duplicates found."}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 bg-slate-50 border-b border-slate-200">
              <h3 className="font-bold text-slate-800">Column Duplicate Details</h3>
            </div>
            <div className="overflow-auto max-h-[400px]">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-xs text-slate-500 uppercase sticky top-0 border-b border-slate-200 shadow-sm z-10">
                  <tr>
                    <th className="px-4 py-3">Column Name</th>
                    <th className="px-4 py-3">Duplicate Value</th>
                    <th className="px-4 py-3">Appears In Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {anomalies?.col_duplicates_details?.length > 0 ? anomalies.col_duplicates_details.map((col, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-bold text-slate-700">{col.column}</td>
                      <td className="px-4 py-3 font-mono text-xs bg-slate-50 rounded border border-slate-100 my-1 mx-2 inline-block px-2 break-all max-w-[150px] truncate">"{col.value}"</td>
                      <td className="px-4 py-3 text-slate-600 leading-relaxed">
                        {col.rows.join(', ')}
                        {col.has_more && <span className="text-amber-500 font-bold ml-1 cursor-pointer">...and {col.total_appearances - col.rows.length} more</span>}
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="3" className="px-4 py-8 text-center text-slate-400 font-medium">{metrics?.total_rows > 500000 ? "Column extraction disabled for extreme datasets." : "No column duplicates found."}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>

      {/* Deep Actionable Analysis */}
      <div className="bg-slate-900 rounded-3xl p-8 shadow-xl text-slate-100 mt-12 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-8 border-b border-slate-700 pb-6">
          <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-xl"><Activity className="w-8 h-8" /></div>
          <div>
            <h2 className="text-3xl font-black text-white tracking-tight">Deep Actionable Analysis</h2>
            <p className="text-slate-400 font-medium">AI-driven insights and column-level quality profiling.</p>
          </div>
        </div>

        {/* AI Health Report */}
        {ai_health_report && (
          <div className="bg-slate-800 rounded-2xl p-6 mb-8 border border-slate-700 shadow-inner">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-indigo-300">
              <Bot className="w-5 h-5" /> Dataset Assessment
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Strengths</h4>
                  <ul className="space-y-2">
                    {ai_health_report.strengths.map((str, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                        {str}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Issues</h4>
                  <ul className="space-y-2">
                    {ai_health_report.issues.map((iss, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <AlertOctagon className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
                        {iss}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700">
                  <h4 className="text-sm font-bold text-indigo-400 uppercase tracking-wider mb-2">Recommended Actions</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-slate-300 font-medium">
                    {ai_health_report.actions.map((act, i) => (
                      <li key={i}>{act}</li>
                    ))}
                  </ol>
                </div>
                
                <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700 flex justify-between items-center">
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Overall Data Quality</div>
                    <div className={`text-xl font-black ${ai_health_report.overall_quality === 'Poor' ? 'text-rose-400' : ai_health_report.overall_quality === 'Average' ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {ai_health_report.overall_quality}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-black text-white">{ai_health_report.completeness_score.toFixed(2)}%</div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Completeness Score</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Missing Data Matrix */}
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
             <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
               <LayoutGrid className="w-5 h-5 text-indigo-400" /> Missing Data Heatmap
             </h3>
             <p className="text-xs text-slate-400 mb-4">A visual representation of missing data. (Red = Missing, Downsampled to 100 rows)</p>
             {anomalies?.missing_data_heatmap?.length > 0 ? (
               <div className="w-full flex">
                 <div className="flex-1 border border-slate-700 bg-slate-900 overflow-x-auto">
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                     {anomalies.missing_data_heatmap.map((row, i) => (
                       <div key={i} style={{ display: 'flex', gap: '1px' }}>
                         {Object.keys(row).filter(k => k !== '_row_id').map((k, j) => (
                           <div key={j} style={{ width: '4px', height: '4px', flexShrink: 0, backgroundColor: row[k] === 1 ? '#ef4444' : '#1e293b' }} title={`Row: ${row._row_id}, Col: ${k}`} />
                         ))}
                       </div>
                     ))}
                   </div>
                 </div>
               </div>
             ) : (
               <p className="text-sm text-slate-400 text-center py-10">No missing data heatmap available.</p>
             )}
             
             <div className="mt-6 p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                <div className="text-slate-300 text-sm"><span className="font-bold text-rose-400">{anomalies?.poor_quality_rows_count || 0}</span> rows have &gt;50% missing or empty cells (Row Quality Analysis).</div>
             </div>
          </div>

          {/* Column Importance & Unique Values */}
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 overflow-hidden flex flex-col">
             <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
               <Search className="w-5 h-5 text-indigo-400" /> Column Profile Ranking
             </h3>
             <div className="overflow-auto flex-1 max-h-[300px]">
               <table className="w-full text-sm text-left">
                 <thead className="bg-slate-900/50 text-xs text-slate-400 uppercase sticky top-0 border-b border-slate-700 z-10">
                   <tr>
                     <th className="px-4 py-3">Column</th>
                     <th className="px-4 py-3">Unique Vals</th>
                     <th className="px-4 py-3">Importance</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-700/50">
                   {distributions?.unique_counts_by_col && Object.entries(distributions.unique_counts_by_col).map(([col, count]) => {
                     const imp = distributions?.column_importance?.[col] || "Medium";
                     return (
                       <tr key={col} className="hover:bg-slate-700/30">
                         <td className="px-4 py-3 font-medium text-slate-200">{col}</td>
                         <td className="px-4 py-3 text-slate-400">{count.toLocaleString()}</td>
                         <td className="px-4 py-3">
                           <span className={`px-2 py-1 rounded text-xs font-bold ${imp === 'High' ? 'bg-emerald-500/20 text-emerald-400' : imp === 'Low' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
                             {imp}
                           </span>
                         </td>
                       </tr>
                     );
                   })}
                 </tbody>
               </table>
             </div>
          </div>
        </div>

        {/* Column-wise Quality & Data Type Validation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 overflow-hidden flex flex-col">
             <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
               <FileText className="w-5 h-5 text-indigo-400" /> Column-wise Missing Data
             </h3>
             <div className="overflow-auto flex-1 max-h-[300px]">
               <table className="w-full text-sm text-left">
                 <thead className="bg-slate-900/50 text-xs text-slate-400 uppercase sticky top-0 border-b border-slate-700 z-10">
                   <tr>
                     <th className="px-4 py-3">Column</th>
                     <th className="px-4 py-3 text-right">Missing Count</th>
                     <th className="px-4 py-3 text-right">Missing %</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-700/50">
                   {distributions?.all_missing_per_column && Object.entries(distributions.all_missing_per_column).sort((a,b) => b[1] - a[1]).map(([col, count]) => {
                     const pct = distributions?.missing_pct_per_column?.[col] || 0;
                     if (count === 0 && pct === 0) return null;
                     return (
                       <tr key={col} className="hover:bg-slate-700/30">
                         <td className="px-4 py-3 font-medium text-slate-200">{col}</td>
                         <td className="px-4 py-3 text-right text-slate-400">{count.toLocaleString()}</td>
                         <td className="px-4 py-3 text-right">
                           <span className={`px-2 py-1 rounded text-xs font-bold ${pct > 30 ? 'bg-rose-500/20 text-rose-400' : pct > 10 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'}`}>
                             {pct}%
                           </span>
                         </td>
                       </tr>
                     );
                   })}
                 </tbody>
               </table>
               {(!distributions?.all_missing_per_column || Object.values(distributions.all_missing_per_column).every(v => v === 0)) && (
                 <p className="text-sm text-slate-400 text-center py-10">No missing data found in any column.</p>
               )}
             </div>
          </div>

          <div className="space-y-8">
            <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 overflow-hidden flex flex-col h-[calc(50%-1rem)]">
               <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                 <Database className="w-5 h-5 text-indigo-400" /> Data Type Validation
               </h3>
               <div className="overflow-auto flex-1">
                 <table className="w-full text-sm text-left">
                   <thead className="bg-slate-900/50 text-xs text-slate-400 uppercase sticky top-0 border-b border-slate-700 z-10">
                     <tr>
                       <th className="px-4 py-3">Column</th>
                       <th className="px-4 py-3">Expected Type</th>
                       <th className="px-4 py-3">Mismatch Count</th>
                     </tr>
                   </thead>
                   <tbody className="divide-y divide-slate-700/50">
                     {anomalies?.type_validation_issues?.length > 0 ? anomalies.type_validation_issues.map((issue, i) => (
                       <tr key={i} className="hover:bg-slate-700/30">
                         <td className="px-4 py-3 font-medium text-slate-200">{issue.column}</td>
                         <td className="px-4 py-3 text-slate-400">{issue.expected}</td>
                         <td className="px-4 py-3 text-rose-400 font-bold">{issue.mismatch_count.toLocaleString()}</td>
                       </tr>
                     )) : (
                       <tr><td colSpan="3" className="px-4 py-6 text-center text-slate-400 font-medium">No type mismatches detected.</td></tr>
                     )}
                   </tbody>
                 </table>
               </div>
            </div>

            <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 overflow-hidden flex flex-col h-[calc(50%-1rem)]">
               <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                 <Search className="w-5 h-5 text-indigo-400" /> Category Consistency
               </h3>
               <div className="overflow-auto flex-1">
                 <ul className="space-y-3">
                   {anomalies?.inconsistent_categories_cols?.length > 0 ? anomalies.inconsistent_categories_cols.map((col, i) => (
                     <li key={i} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                       <span className="font-medium text-slate-200">{col}</span>
                       <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded font-bold">Inconsistent Casing</span>
                     </li>
                   )) : (
                     <li className="text-center text-slate-400 font-medium py-4">All categorical values are consistently cased.</li>
                   )}
                 </ul>
               </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function StatCard({ label, value, pct, icon, color = 'slate', alert = false }) {
  const isAlert = alert && value > 0;
  return (
    <div className={`bg-white rounded-2xl p-5 border ${isAlert ? 'border-amber-200 shadow-amber-100' : 'border-slate-200'} shadow-sm flex flex-col justify-between h-32`}>
      <div className={`flex justify-between items-start`}>
        <div className={`text-${isAlert ? 'amber' : color}-500`}>{icon}</div>
        {pct !== undefined && (
           <div className={`text-xs font-black px-2 py-0.5 rounded bg-${isAlert ? 'amber' : color}-50 text-${isAlert ? 'amber' : color}-600`}>
             {pct}%
           </div>
        )}
      </div>
      <div>
        <div className={`text-2xl font-black ${isAlert ? 'text-amber-600' : 'text-slate-900'}`}>
          {value !== undefined ? value.toLocaleString() : '-'}
        </div>
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wide mt-1">{label}</div>
      </div>
    </div>
  );
}

function ScorePillar({ label, score }) {
  const getGradient = (s) => {
    if (s > 90) return 'from-emerald-400 to-emerald-500';
    if (s > 75) return 'from-amber-400 to-amber-500';
    return 'from-rose-400 to-rose-500';
  };
  
  return (
    <div>
      <div className="flex justify-between items-end mb-2">
        <span className="text-sm font-bold text-slate-600 uppercase">{label}</span>
        <span className="text-lg font-black text-slate-900">{score}%</span>
      </div>
      <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${getGradient(score)} transition-all duration-1000`} style={{ width: `${score}%` }}></div>
      </div>
    </div>
  );
}
