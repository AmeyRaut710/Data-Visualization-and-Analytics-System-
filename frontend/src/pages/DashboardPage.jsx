import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import { Database, Hash, Columns, FileText, AlertTriangle, CheckCircle, ShieldAlert, Sparkles, Copy, DownloadCloud, Activity, Bot, Search, LayoutGrid, CheckCircle2, AlertOctagon } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import html2pdf from 'html2pdf.js';
import PDFReportTemplate from '../components/PDFReportTemplate';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";

export default function DashboardPage() {
  const { sessionId, overview, activeSheet } = useAppContext();
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [copying, setCopying] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const reportTemplateRef = useRef(null);

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
      }, 3500);
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (sessionId) {
      setLoading(true);
      const sheetParam = activeSheet ? `?sheet=${encodeURIComponent(activeSheet)}` : '';
      axios.get(`${API_URL}/api/quality/${sessionId}${sheetParam}`)
        .then(res => {
          setQuality(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          alert("Session expired or data not found. Please upload your file again.");
          window.location.href = "/";
        });
    }
  }, [sessionId, activeSheet]);

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

  const { metrics, scores, distributions, anomalies, ai_health_report, score_breakdown, outlier_summary, dataset_summary, ai_recommendations, ai_summary, performance } = quality || {};
  
  const gaugeData = [
    { name: 'Score', value: scores?.overall_cleanliness || 0 },
    { name: 'Missing', value: 100 - (scores?.overall_cleanliness || 0) }
  ];
  const GAUGE_COLORS = [
    (scores?.overall_cleanliness || 0) > 90 ? '#10b981' : (scores?.overall_cleanliness || 0) > 70 ? '#f59e0b' : '#ef4444', 
    '#334155'
  ];

  const missingChartData = Object.entries(distributions?.all_missing_per_column || {}).map(([col, count]) => ({
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


  const handleCopySummary = () => {
    if (ai_summary) {
      navigator.clipboard.writeText(ai_summary);
      setCopying(true);
      setTimeout(() => setCopying(false), 2000);
    }
  };

  const handleDownloadPDF = () => {
    setIsGeneratingPDF(true);
    
    setTimeout(() => {
      const element = reportTemplateRef.current;
      const opt = {
        margin:       0,
        filename:     `${overview?.filename || 'Data_Quality'}_Report.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, logging: false },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
      };

      html2pdf().set(opt).from(element).save().then(() => {
        setIsGeneratingPDF(false);
      });
    }, 500);
  };

  return (
    <>
      {isGeneratingPDF && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm">
          <div className="bg-white p-8 rounded-2xl shadow-2xl flex flex-col items-center max-w-sm text-center">
            <div className="w-16 h-16 relative mb-4">
              <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-black text-slate-800 mb-2">Generating Professional Report...</h3>
            <p className="text-slate-500 text-sm">Rendering high-resolution charts and applying AI insights. This may take a few seconds.</p>
          </div>
        </div>
      )}
      
      <div style={{ position: 'absolute', top: '-9999px', left: '-9999px' }}>
        <PDFReportTemplate ref={reportTemplateRef} quality={quality} overview={overview} />
      </div>

    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-20 print:p-0 print:max-w-full">
      {/* Header Profile */}
      <div className="bg-slate-900 rounded-3xl p-8 shadow-2xl text-white relative overflow-hidden print:bg-white print:text-slate-900 print:shadow-none print:border print:border-slate-300">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 rounded-full mix-blend-screen filter blur-[80px] opacity-30 print:hidden"></div>
        <div className="flex flex-col md:flex-row justify-between items-center relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-bold uppercase tracking-wider mb-4 print:hidden">
              <Sparkles className="w-4 h-4 text-indigo-400" /> Dynamic Profiling Output
            </div>
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-1">
              {dataset_summary?.dataset_type || "General Tabular Dataset"}
            </div>
            <h1 className="text-4xl font-black mb-2 tracking-tight">Data Quality Dashboard</h1>
            <p className="text-slate-400 print:text-slate-500">
              {overview?.filename} • {(overview?.file_size_bytes / 1024 / 1024).toFixed(2)} MB
            </p>
            
            {/* Column types indicator chips */}
            {dataset_summary && (
              <div className="flex flex-wrap gap-2 mt-4">
                <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded-md text-xs font-medium border border-slate-700">
                  {dataset_summary.numeric_columns_count} Numeric
                </span>
                <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded-md text-xs font-medium border border-slate-700">
                  {dataset_summary.categorical_columns_count} Categorical
                </span>
                <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded-md text-xs font-medium border border-slate-700">
                  {dataset_summary.date_columns_count} Date
                </span>
                <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded-md text-xs font-medium border border-slate-700">
                  {dataset_summary.text_columns_count} Text
                </span>
              </div>
            )}
          </div>
          
          <div className="mt-6 md:mt-0 flex flex-col items-center gap-4">
            <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 p-6 rounded-2xl flex items-center gap-6 print:border-slate-300">
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
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Cleanliness Meter</div>
                <div className={`font-bold text-sm flex items-center gap-1 ${
                  scores?.overall_cleanliness > 90 ? 'text-emerald-400' : scores?.overall_cleanliness > 70 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  <CheckCircle className="w-4 h-4" /> 
                  {scores?.overall_cleanliness > 90 ? 'Excellent Status' : scores?.overall_cleanliness > 70 ? 'Good Health' : 'Needs Cleaning'}
                </div>
              </div>
            </div>

            <button 
              onClick={handleDownloadPDF}
              disabled={isGeneratingPDF}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-lg transition-colors border border-indigo-500/20 print:hidden self-end disabled:opacity-50"
            >
              <DownloadCloud className="w-4 h-4" /> {isGeneratingPDF ? 'Generating PDF...' : 'Download PDF Report'}
            </button>
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

      {/* Executive Summary paragraph & Performance profiling */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Executive summary details */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-black text-slate-800 mb-3 flex items-center gap-2">
              <Bot className="w-5 h-5 text-indigo-500" /> Executive Quality Summary
            </h3>
            <p className="text-slate-600 text-sm leading-relaxed font-medium">
              {ai_summary || "Analyzing dataset parameters..."}
            </p>
          </div>
          <button 
            onClick={handleCopySummary}
            className={`mt-4 px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 border w-fit self-end transition-colors ${
              copying 
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <Copy className="w-4 h-4" /> 
            {copying ? 'Summary Copied!' : 'Copy Executive Summary'}
          </button>
        </div>

        {/* Polars Engine Performance Profile */}
        {performance && (
          <div className="bg-slate-900 rounded-3xl p-6 border border-slate-800 text-slate-100 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-indigo-400">
                <Activity className="w-5 h-5" /> Engine Performance Profile
              </h3>
              <div className="space-y-3 mt-4">
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-xs text-slate-400 font-bold uppercase">Profiling Speed</span>
                  <span className="text-sm font-mono text-emerald-400 font-bold">
                    {performance.processing_speed_rows_per_sec.toLocaleString()} rows/sec
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-xs text-slate-400 font-bold uppercase">Analysis Duration</span>
                  <span className="text-sm font-mono text-white font-bold">{performance.analysis_time_sec}s</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-xs text-slate-400 font-bold uppercase">Memory Footprint</span>
                  <span className="text-sm font-mono text-white font-bold">{performance.memory_used_mb} MB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-slate-400 font-bold uppercase">Engine Backend</span>
                  <span className="text-xs font-black text-indigo-400 uppercase tracking-widest bg-indigo-500/10 px-2 py-0.5 rounded">Polars Vectorized</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pillars of Quality & Explainable Score Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quality Pillars */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-8 border border-slate-200 shadow-sm space-y-6">
          <h2 className="text-2xl font-black text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-indigo-500" /> Five Pillars of Data Quality
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 md:gap-6">
            <ScorePillar label="Completeness" score={scores?.completeness} tooltip="Degree to which all required data cells contain present values rather than missing indicators." />
            <ScorePillar label="Consistency" score={scores?.consistency} tooltip="Absence of casing inconsistencies, format discrepancies, or syntax anomalies." />
            <ScorePillar label="Validity" score={scores?.validity} tooltip="Values conforming strictly to mathematical, range boundaries, and schema data types." />
            <ScorePillar label="Uniqueness" score={scores?.uniqueness} tooltip="Degree of structural redundancy or exact duplicated row values in the dataset." />
            <ScorePillar label="Accuracy" score={scores?.accuracy} tooltip="Statistical confidence, mapping accuracy, and absence of extreme outliers." />
          </div>
        </div>

        {/* Explainable score deductions card */}
        {score_breakdown && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold mb-1 flex items-center gap-2 text-rose-400">
                <AlertTriangle className="w-5 h-5" /> Cleanliness Score Breakdown
              </h3>
              <p className="text-[10px] text-slate-400 uppercase font-black tracking-widest mb-4">Step-by-step deductions</p>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between font-bold border-b border-slate-800 pb-1.5 text-slate-400">
                  <span>Base Score</span>
                  <span>{score_breakdown.base_score}%</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Missing values deduction</span>
                  <span className="font-mono text-rose-400">{score_breakdown.missing_values_impact}%</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Exact duplicates deduction</span>
                  <span className="font-mono text-rose-400">{score_breakdown.duplicates_impact}%</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Statistical outliers deduction</span>
                  <span className="font-mono text-rose-400">{score_breakdown.outliers_impact}%</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Type mismatches deduction</span>
                  <span className="font-mono text-rose-400">{score_breakdown.invalid_data_impact}%</span>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between items-end">
              <span className="text-xs font-bold text-slate-400 uppercase">Cleanliness Score</span>
              <span className="text-3xl font-black text-white">{scores?.overall_cleanliness}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Exact Duplicate Module */}
      <div className="bg-amber-50/30 border border-amber-200 rounded-3xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-amber-100 text-amber-600 rounded-xl"><Copy className="w-6 h-6" /></div>
          <div>
            <h2 className="text-2xl font-black text-slate-800">Exact Duplicate Detection</h2>
            <p className="text-slate-500 font-medium">Character-for-character comparison using hash-based vectorization.</p>
          </div>
        </div>

        {/* Duplicate Method Description Box */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
            <input type="checkbox" checked readOnly className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4" />
            <div>
              <div className="text-xs font-bold text-slate-800">Trim Whitespace</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Leading/trailing spaces ignored</div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
            <input type="checkbox" checked readOnly className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4" />
            <div>
              <div className="text-xs font-bold text-slate-800">Case Sensitivity</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Strict casing matches respected</div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
            <input type="checkbox" checked readOnly className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4" />
            <div>
              <div className="text-xs font-bold text-slate-800">Hash Vectors</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Vectorized comparison scale-speed</div>
            </div>
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
                 <span className="font-bold text-amber-800">Repeated Values (Expected):</span> The column <b>{anomalies.col_duplicates_details[0].column}</b> contains duplicate values. For example, the value <b>"{anomalies.col_duplicates_details[0].value}"</b> appears {anomalies.col_duplicates_details[0].total_appearances} times, including in rows {anomalies.col_duplicates_details[0].rows.slice(0, 4).join(', ')}.
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

        {/* AI Recommendations List */}
        {ai_recommendations && ai_recommendations.length > 0 && (
          <div className="bg-slate-800 rounded-2xl p-6 mb-8 border border-slate-700 shadow-inner">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-indigo-300">
              <Bot className="w-5 h-5" /> AI Cleaning Recommendations
            </h3>
            
            <div className="grid grid-cols-1 gap-3">
              {ai_recommendations.map((rec, i) => (
                <div key={i} className="flex justify-between items-center bg-slate-950/40 p-4 rounded-xl border border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 flex items-center justify-center bg-indigo-500/20 text-indigo-400 text-xs font-bold rounded-full">
                      {rec.priority}
                    </span>
                    <span className="text-sm font-medium text-slate-200">{rec.action}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-slate-500">Predicted Score Improvement</div>
                    <div className="text-sm font-mono text-emerald-400 font-bold">{rec.improvement}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Missing Data Heatmap */}
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
                           <div 
                             key={j} 
                             style={{ width: '4px', height: '4px', flexShrink: 0, backgroundColor: row[k] === 1 ? '#ef4444' : '#1e293b' }} 
                             className="hover:scale-125 transition-transform cursor-crosshair relative group"
                             title={`Column: ${k}\nStatus: ${row[k] === 1 ? 'Missing (Null)' : 'Present'}\nColumn Null Rate: ${distributions?.missing_pct_per_column?.[k] || 0}%`} 
                           />
                         ))}
                       </div>
                     ))}
                   </div>
                 </div>
               </div>
             ) : (
               <p className="text-sm text-slate-400 text-center py-10">No missing data heatmap available.</p>
             )}
             
             {/* Rows affected by missing values */}
             <div className="grid grid-cols-2 gap-3 mt-6">
                <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                  <div className="text-[10px] text-slate-400 uppercase font-black mb-1">Rows Affected</div>
                  <div className="text-white font-black text-lg">
                    {metrics?.total_missing_rows_count?.toLocaleString()} Rows
                  </div>
                </div>
                <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                  <div className="text-[10px] text-slate-400 uppercase font-black mb-1">Columns Affected</div>
                  <div className="text-white font-black text-lg">
                    {metrics?.columns_affected_by_missing} Columns
                  </div>
                </div>
             </div>
          </div>

          {/* Column Profile Health Scores */}
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 overflow-hidden flex flex-col">
             <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
               <Search className="w-5 h-5 text-indigo-400" /> Column Profile Health Scores
             </h3>
             <div className="overflow-auto flex-1 max-h-[300px]">
               <table className="w-full text-sm text-left">
                 <thead className="bg-slate-900/50 text-xs text-slate-400 uppercase sticky top-0 border-b border-slate-700 z-10">
                   <tr>
                     <th className="px-4 py-3">Column</th>
                     <th className="px-4 py-3">Unique Vals</th>
                     <th className="px-4 py-3">Health status</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-700/50">
                   {distributions?.unique_counts_by_col && Object.entries(distributions.unique_counts_by_col).map(([col, count]) => {
                     const healthInfo = distributions?.column_importance?.[col] || "Good (90/100)";
                     const isCritical = healthInfo.includes("Critical") || healthInfo.includes("Needs Attention");
                     
                     return (
                       <tr key={col} className="hover:bg-slate-700/30">
                         <td className="px-4 py-3 font-medium text-slate-200">{col}</td>
                         <td className="px-4 py-3 text-slate-400">{count.toLocaleString()}</td>
                         <td className="px-4 py-3">
                           <span className={`px-2 py-1 rounded text-xs font-bold ${
                             isCritical ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                           }`}>
                             {healthInfo}
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
                        <th className="px-4 py-3">Expected</th>
                        <th className="px-4 py-3">Detected</th>
                        <th className="px-4 py-3">Mismatches</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                      {anomalies?.type_validation_issues?.length > 0 ? anomalies.type_validation_issues.map((issue, i) => (
                        <tr key={i} className="hover:bg-slate-700/30">
                          <td className="px-4 py-3 font-medium text-slate-200">{issue.column}</td>
                          <td className="px-4 py-3 text-slate-400">{issue.expected}</td>
                          <td className="px-4 py-3 text-slate-400 font-mono text-xs">{issue.detected || "string"}</td>
                          <td className="px-4 py-3 text-rose-400 font-bold">{issue.mismatch_count.toLocaleString()}</td>
                        </tr>
                      )) : (
                        <tr><td colSpan="4" className="px-4 py-6 text-center text-slate-400 font-medium">No type mismatches detected.</td></tr>
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

        {/* Outlier Profile Details */}
        {outlier_summary && (
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 mt-8">
             <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
               <AlertTriangle className="w-5 h-5 text-indigo-400" /> Outlier Profile Details
             </h3>
             <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
               <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700">
                 <div className="text-[10px] text-slate-400 uppercase font-black">Detection Method</div>
                 <div className="font-black text-white text-base mt-1">{outlier_summary.detection_method}</div>
               </div>
               <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700">
                 <div className="text-[10px] text-slate-400 uppercase font-black">Columns Checked</div>
                 <div className="font-black text-white text-lg mt-1">{outlier_summary.columns_checked} Columns</div>
               </div>
               <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700">
                 <div className="text-[10px] text-slate-400 uppercase font-black">Affected Columns</div>
                 <div className="font-medium text-slate-200 mt-1.5 flex flex-wrap gap-1">
                   {outlier_summary.affected_columns.length > 0 ? (
                     outlier_summary.affected_columns.map(col => (
                       <span key={col} className="px-2 py-0.5 bg-rose-500/20 text-rose-400 rounded text-xs font-bold">{col}</span>
                     ))
                   ) : <span className="text-slate-400 text-xs">None</span>}
                 </div>
               </div>
               <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700 flex flex-col justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase font-black">Min / Max Outlier</div>
                    {outlier_summary.minimum_outlier_column !== "None" ? (
                      <div className="flex justify-between items-baseline mt-1 text-xs">
                        <span className="font-semibold text-slate-300 truncate max-w-[80px]">{outlier_summary.minimum_outlier_column} (Min)</span>
                        <span className="font-mono text-rose-400 font-bold">{outlier_summary.minimum_outlier_value}</span>
                      </div>
                    ) : null}
                    {outlier_summary.largest_outlier_column !== "None" ? (
                      <div className="flex justify-between items-baseline mt-1 text-xs">
                        <span className="font-semibold text-slate-300 truncate max-w-[80px]">{outlier_summary.largest_outlier_column} (Max)</span>
                        <span className="font-mono text-rose-400 font-bold">{outlier_summary.largest_outlier_value}</span>
                      </div>
                    ) : null}
                    {outlier_summary.largest_outlier_column === "None" && outlier_summary.minimum_outlier_column === "None" && (
                      <span className="text-slate-400 text-xs mt-1 block">None detected</span>
                    )}
                  </div>
                </div>
             </div>
          </div>
        )}

      </div>
    </div>
    </>
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

function ScorePillar({ label, score, tooltip }) {
  const getGradient = (s) => {
    if (s > 90) return 'from-emerald-400 to-emerald-500';
    if (s > 75) return 'from-amber-400 to-amber-500';
    return 'from-rose-400 to-rose-500';
  };
  
  return (
    <div className="relative group cursor-help bg-slate-50 p-4 rounded-2xl border border-slate-100 hover:border-indigo-100 hover:shadow-sm transition-all">
      <div className="flex flex-col mb-3">
        <span className="text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 truncate">{label}</span>
        <span className="text-xl sm:text-2xl font-black text-slate-900 leading-none">{score}%</span>
      </div>
      <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${getGradient(score)} transition-all duration-1000`} style={{ width: `${score}%` }}></div>
      </div>

      {/* Custom hover tooltip */}
      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-slate-950 text-white text-[11px] p-2.5 rounded-lg border border-slate-800 shadow-xl opacity-0 scale-95 pointer-events-none group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 z-50 w-48 text-center leading-normal">
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-slate-950"></div>
        {tooltip}
      </div>
    </div>
  );
}
