import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts';
import { Database, Hash, Columns, FileText, AlertTriangle, CheckCircle, ShieldAlert, Sparkles, Copy, DownloadCloud, Activity, Bot, Search, LayoutGrid, Cpu, List, FileKey, TerminalSquare } from 'lucide-react';

const A4_HEIGHT = 1123;
const A4_WIDTH = 794;

const SectionHeader = ({ title, icon, subtitle }) => (
  <div className="flex items-center gap-3 mb-6 mt-8 border-b-2 border-indigo-100 pb-4 break-inside-avoid">
    <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">{icon}</div>
    <div>
      <h2 className="text-2xl font-black text-slate-800 tracking-tight">{title}</h2>
      {subtitle && <p className="text-sm font-medium text-slate-500 mt-1">{subtitle}</p>}
    </div>
  </div>
);

const KPICard = ({ label, value, icon, color = 'slate', unit = '' }) => (
  <div className={`bg-white rounded-xl p-4 border border-${color}-200 shadow-sm flex items-center gap-4 break-inside-avoid`}>
    <div className={`p-3 bg-${color}-50 text-${color}-500 rounded-lg shrink-0`}>
      {icon}
    </div>
    <div>
      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</div>
      <div className={`text-xl font-black text-slate-900 mt-0.5`}>
        {value !== undefined ? (typeof value === 'number' ? value.toLocaleString() : value) : '-'} {unit}
      </div>
    </div>
  </div>
);

const PDFReportTemplate = React.forwardRef(({ quality, overview }, ref) => {
  if (!quality || !overview) return null;

  const { metrics, scores, distributions, anomalies, ai_health_report, score_breakdown, outlier_summary, dataset_summary, ai_recommendations, ai_summary, performance } = quality;

  // Generate a unique report ID for this render
  const reportId = useMemo(() => `RPT-${Math.random().toString(36).substr(2, 9).toUpperCase()}`, []);
  const generatedDate = useMemo(() => new Date().toLocaleString(), []);

  const GAUGE_COLORS = [
    (scores?.overall_cleanliness || 0) > 90 ? '#10b981' : (scores?.overall_cleanliness || 0) > 70 ? '#f59e0b' : '#ef4444', 
    '#f1f5f9'
  ];
  const gaugeData = [
    { name: 'Score', value: scores?.overall_cleanliness || 0 },
    { name: 'Missing', value: 100 - (scores?.overall_cleanliness || 0) }
  ];

  const duplicateCountChartData = Object.entries(distributions?.duplicate_count_by_col || {})
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([col, count]) => ({ name: col, Count: count }));

  const missingChartData = Object.entries(distributions?.all_missing_per_column || {})
    .filter(([_, count]) => count > 0)
    .sort((a,b) => b[1]-a[1])
    .slice(0,10)
    .map(([col, count]) => ({ name: col, Missing: count }));

  const PageFooter = ({ pageNum, totalPages }) => (
    <div className="absolute bottom-8 left-12 right-12 flex justify-between items-end border-t border-slate-200 pt-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
      <div>
        <span className="text-indigo-600 font-black">AI Analyst</span> • {overview?.filename}
      </div>
      <div className="text-center">
        {generatedDate} • ID: {reportId}
      </div>
      <div>
        Page {pageNum} of {totalPages}
      </div>
    </div>
  );

  const PageWrapper = ({ children, pageNum, totalPages = 10, bg = 'white' }) => (
    <>
      {pageNum > 1 && <div className="html2pdf__page-break"></div>}
      <div className={`w-[794px] bg-${bg} relative p-12 overflow-hidden box-border`} style={{ pageBreakInside: 'avoid' }}>
        {children}
        {pageNum === totalPages && <PageFooter pageNum={pageNum} totalPages={totalPages} />}
      </div>
    </>
  );

  const TOTAL_PAGES = 10;

  return (
    <div ref={ref} className="bg-slate-200 text-slate-900 mx-auto pdf-report-container" style={{ width: '794px' }}>
      
      {/* SECTION 1: COVER PAGE */}
      <PageWrapper pageNum={1} totalPages={TOTAL_PAGES} bg="slate-50">
        <div className="flex flex-col justify-between pb-8 pt-12">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                <Activity className="text-white w-6 h-6" />
              </div>
              <span className="font-black text-2xl tracking-tight text-slate-800">Vista Data</span>
            </div>
            
            <div className="mt-32 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-black uppercase tracking-widest mb-6">
                <Sparkles className="w-4 h-4" /> Comprehensive Data Profiling Report
              </div>
              
              <h1 className="text-5xl font-black mb-6 tracking-tight text-slate-900 leading-[1.1]">
                Intelligent Data Visualization & Analytics Engine
              </h1>
              <p className="text-lg text-slate-500 font-medium">Automated exploratory data analysis, quality assessment, and AI-driven cleaning recommendations.</p>
            </div>
          </div>
          
          <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
            <h3 className="font-black text-slate-800 text-lg mb-6 border-b border-slate-100 pb-4 flex justify-between items-center">
              Dataset Profile
              <span className="text-xs font-bold bg-slate-100 text-slate-500 px-3 py-1 rounded-full">{reportId}</span>
            </h3>
            <div className="grid grid-cols-2 gap-y-6 gap-x-8 text-sm">
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">Project Title</span><span className="font-bold text-slate-800">Vista Analytics Initiative</span></div>
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">System Version</span><span className="font-bold text-slate-800">v2.4.0 Enterprise</span></div>
              
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">Dataset Name</span><span className="font-bold text-slate-800 break-words">{overview?.filename}</span></div>
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">Dataset Type</span><span className="font-bold text-slate-800">{dataset_summary?.dataset_type || "Tabular Data"}</span></div>
              
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">Shape</span><span className="font-bold text-slate-800">{metrics?.total_rows?.toLocaleString()} Rows × {metrics?.total_cols?.toLocaleString()} Columns</span></div>
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">File Size</span><span className="font-bold text-slate-800">{(overview?.file_size_bytes / 1024 / 1024).toFixed(2)} MB</span></div>
              
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">Processing Time</span><span className="font-bold text-slate-800">{performance?.analysis_time_sec} seconds</span></div>
              <div><span className="block text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-1">AI Engine Used</span><span className="font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">Polars + Agentic AI</span></div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={gaugeData} cx="50%" cy="50%" innerRadius={28} outerRadius={40} startAngle={90} endAngle={-270} dataKey="value" stroke="none">
                        {gaugeData.map((entry, index) => <Cell key={`cell-${index}`} fill={GAUGE_COLORS[index]} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className="text-lg font-black leading-none text-slate-800">{scores?.overall_cleanliness}%</span>
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Cleanliness Status</div>
                  <div className={`text-lg font-black flex items-center gap-1 mt-1 ${
                        scores?.overall_cleanliness > 90 ? 'text-emerald-600' : scores?.overall_cleanliness > 70 ? 'text-amber-600' : 'text-rose-600'
                      }`}>
                    <CheckCircle className="w-5 h-5" /> 
                    {scores?.overall_cleanliness > 90 ? 'Excellent Health' : scores?.overall_cleanliness > 70 ? 'Good Health' : 'Needs Cleaning'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 2: EXECUTIVE SUMMARY & OVERVIEW */}
      <PageWrapper pageNum={2} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Executive Summary" icon={<Bot className="w-6 h-6" />} subtitle="High-level overview and AI-generated assessment" />
          
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-lg border border-slate-800 relative overflow-hidden break-inside-avoid">
               <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500 rounded-full mix-blend-screen filter blur-[40px] opacity-40"></div>
               <div className="relative z-10">
                 <div className="text-[10px] uppercase tracking-widest font-bold text-indigo-300 mb-2">Overall Quality Score</div>
                 <div className="text-5xl font-black mb-2">{scores?.overall_cleanliness}%</div>
                 <div className="text-sm font-medium text-slate-300">
                   Readiness: {scores?.overall_cleanliness > 90 ? 'Ready for production analysis' : scores?.overall_cleanliness > 70 ? 'Requires minor cleaning' : 'Requires major cleaning'}
                 </div>
               </div>
            </div>
            <div className="bg-rose-50 text-rose-900 p-6 rounded-2xl shadow-sm border border-rose-100 flex flex-col justify-center break-inside-avoid">
               <div className="text-[10px] uppercase tracking-widest font-bold text-rose-400 mb-2">Total Issues Detected</div>
               <div className="text-5xl font-black mb-2">{(metrics?.total_missing_values + metrics?.total_exact_duplicates + metrics?.total_outliers).toLocaleString()}</div>
               <div className="text-sm font-medium text-rose-700/80">
                 Across {metrics?.columns_affected_by_missing} columns and {metrics?.total_missing_rows_count} rows
               </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 mb-8 break-inside-avoid">
          <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2"><Sparkles className="w-4 h-4 text-indigo-500"/> AI Analyst Summary</h3>
          <p className="text-slate-700 leading-relaxed text-sm">
            {ai_summary || `The uploaded dataset contains ${metrics?.total_rows?.toLocaleString()} rows and ${metrics?.total_cols?.toLocaleString()} columns. The profiling engine identified ${metrics?.total_missing_values?.toLocaleString()} missing values, ${metrics?.total_exact_duplicates?.toLocaleString()} duplicate rows, and ${metrics?.total_outliers?.toLocaleString()} outliers. The overall cleanliness score is ${scores?.overall_cleanliness}%. This report provides a detailed assessment of data quality, structural consistency, and recommendations for further improvement.`}
          </p>
        </div>

        <div className="break-inside-avoid">
          <SectionHeader title="Dataset KPI Overview" icon={<LayoutGrid className="w-6 h-6" />} subtitle="Core metrics and structural dimensions" />
          <div className="grid grid-cols-2 gap-4">
            <KPICard label="Total Rows" value={metrics?.total_rows} icon={<Hash className="w-5 h-5"/>} color="indigo" />
            <KPICard label="Total Columns" value={metrics?.total_cols} icon={<Columns className="w-5 h-5"/>} color="indigo" />
            <KPICard label="Missing Values" value={metrics?.total_missing_values} icon={<FileText className="w-5 h-5"/>} color="rose" />
            <KPICard label="Duplicate Rows" value={metrics?.total_exact_duplicates} icon={<Copy className="w-5 h-5"/>} color="amber" />
            <KPICard label="Total Outliers" value={metrics?.total_outliers} icon={<AlertTriangle className="w-5 h-5"/>} color="rose" />
            <KPICard label="Dataset Size" value={(overview?.file_size_bytes / 1024 / 1024).toFixed(2)} unit="MB" icon={<Database className="w-5 h-5"/>} color="slate" />
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 3: PILLARS & BREAKDOWN */}
      <PageWrapper pageNum={3} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid mb-8">
          <SectionHeader title="Five Pillars of Data Quality" icon={<ShieldAlert className="w-6 h-6" />} subtitle="Dimensional scoring of dataset health" />
          
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <div className="space-y-6">
              {[
                { label: 'Completeness', score: scores?.completeness, desc: 'Degree to which all required data cells contain present values.', color: 'indigo' },
                { label: 'Consistency', score: scores?.consistency, desc: 'Absence of format discrepancies or syntax anomalies.', color: 'blue' },
                { label: 'Validity', score: scores?.validity, desc: 'Values conforming strictly to mathematical/range boundaries.', color: 'emerald' },
                { label: 'Uniqueness', score: scores?.uniqueness, desc: 'Degree of structural redundancy or duplicated values.', color: 'amber' },
                { label: 'Accuracy', score: scores?.accuracy, desc: 'Absence of extreme outliers and statistical anomalies.', color: 'rose' }
              ].map((pillar, idx) => (
                 <div key={idx} className="break-inside-avoid">
                   <div className="flex justify-between items-end mb-2">
                     <div>
                       <span className="text-sm font-bold text-slate-800">{pillar.label}</span>
                       <span className="text-xs text-slate-400 ml-2 font-medium">{pillar.desc}</span>
                     </div>
                     <span className="text-lg font-black text-slate-900">{pillar.score || 0}%</span>
                   </div>
                   <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                     <div className={`h-full bg-${pillar.color}-500 rounded-full`} style={{ width: `${pillar.score || 0}%` }}></div>
                   </div>
                 </div>
              ))}
            </div>
          </div>
        </div>

        <div className="break-inside-avoid">
          <SectionHeader title="Cleanliness Score Breakdown" icon={<Activity className="w-6 h-6" />} subtitle="Explainable step-by-step deductions" />
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="space-y-3 text-sm">
              <div className="flex justify-between font-bold border-b border-slate-200 pb-2 text-slate-800">
                <span>Base Score</span>
                <span>{score_breakdown?.base_score || 100}%</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Missing values deduction</span>
                <span className="font-mono text-rose-500 font-bold">{score_breakdown?.missing_values_impact || 0}%</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Exact duplicates deduction</span>
                <span className="font-mono text-rose-500 font-bold">{score_breakdown?.duplicates_impact || 0}%</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Statistical outliers deduction</span>
                <span className="font-mono text-rose-500 font-bold">{score_breakdown?.outliers_impact || 0}%</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Type mismatches deduction</span>
                <span className="font-mono text-rose-500 font-bold">{score_breakdown?.invalid_data_impact || 0}%</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-200 flex justify-between items-end">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Final Cleanliness Score</span>
              <span className="text-3xl font-black text-indigo-600">{scores?.overall_cleanliness}%</span>
            </div>
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 4: MISSING VALUES */}
      <PageWrapper pageNum={4} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Missing Value Analysis" icon={<LayoutGrid className="w-6 h-6" />} subtitle="Distribution of null or empty cells" />
          
          <div className="grid grid-cols-3 gap-4 mb-8">
            <KPICard label="Columns Affected" value={metrics?.columns_affected_by_missing} icon={<Columns />} color="rose" />
            <KPICard label="Rows Affected" value={metrics?.total_missing_rows_count} icon={<Hash />} color="rose" />
            <KPICard label="Missing Percentage" value={scores?.missing_pct} unit="%" icon={<Activity />} color="rose" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-8 break-inside-avoid">
          <h3 className="font-bold text-slate-800 mb-6 text-sm uppercase tracking-widest">Top Columns with Missing Data</h3>
          <div className="h-[250px] w-full">
              {missingChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={missingChartData} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" tick={{fontSize: 10, fill: '#64748b'}} width={120} />
                    <RechartsTooltip cursor={{fill: '#f8fafc'}} />
                    <Bar dataKey="Missing" fill="#ef4444" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <div className="h-full flex items-center justify-center text-slate-400 font-medium bg-slate-50 rounded-xl">No missing data found in dataset.</div>}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden break-inside-avoid">
           <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
             <h3 className="font-bold text-slate-800 text-xs uppercase tracking-widest">Column-wise Details</h3>
           </div>
           <table className="w-full text-sm text-left">
             <thead className="bg-white text-xs text-slate-400 uppercase border-b border-slate-200">
               <tr>
                 <th className="px-6 py-3 font-bold">Column Name</th>
                 <th className="px-6 py-3 font-bold text-right">Missing Count</th>
                 <th className="px-6 py-3 font-bold text-right">Missing %</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-slate-100">
               {distributions?.all_missing_per_column && Object.entries(distributions.all_missing_per_column)
                 .sort((a,b)=>b[1]-a[1]).filter(x => x[1] > 0).slice(0, 10).map(([col, count], i) => (
                 <tr key={i}>
                   <td className="px-6 py-3 font-medium text-slate-700">{col}</td>
                   <td className="px-6 py-3 text-right text-rose-500 font-bold">{count.toLocaleString()}</td>
                   <td className="px-6 py-3 text-right font-mono text-xs">{distributions?.missing_pct_per_column?.[col]}%</td>
                 </tr>
               ))}
               {Object.values(distributions?.all_missing_per_column || {}).every(v => v === 0) && (
                 <tr><td colSpan="3" className="px-6 py-8 text-center text-slate-400 italic">No missing values to display.</td></tr>
               )}
             </tbody>
           </table>
        </div>
      </PageWrapper>

      {/* PAGE 5: DUPLICATES */}
      <PageWrapper pageNum={5} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Duplicate Analysis" icon={<Copy className="w-6 h-6" />} subtitle="Exact row and column-level redundancy" />
          
          <div className="grid grid-cols-2 gap-4 mb-8">
            <KPICard label="Total Duplicate Rows" value={metrics?.total_exact_duplicates} icon={<Copy />} color="amber" />
            <KPICard label="Columns w/ Duplicates" value={anomalies?.columns_containing_duplicates} icon={<Columns />} color="amber" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-8 break-inside-avoid">
          <h3 className="font-bold text-slate-800 mb-6 text-sm uppercase tracking-widest">Columns by Duplicate Values Count</h3>
          <div className="h-[280px] w-full">
              {duplicateCountChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={duplicateCountChartData} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" tick={{fontSize: 10, fill: '#64748b'}} width={120} />
                    <RechartsTooltip cursor={{fill: '#f8fafc'}} />
                    <Bar dataKey="Count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <div className="h-full flex items-center justify-center text-slate-400 font-medium bg-slate-50 rounded-xl">No column-level duplicates detected.</div>}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden break-inside-avoid">
           <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
             <h3 className="font-bold text-slate-800 text-xs uppercase tracking-widest">Duplicate Value Examples</h3>
           </div>
           <table className="w-full text-sm text-left">
             <thead className="bg-white text-xs text-slate-400 uppercase border-b border-slate-200">
               <tr>
                 <th className="px-6 py-3 font-bold">Column</th>
                 <th className="px-6 py-3 font-bold">Repeated Value</th>
                 <th className="px-6 py-3 font-bold text-right">Appearances</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-slate-100">
               {anomalies?.col_duplicates_details?.length > 0 ? anomalies.col_duplicates_details.slice(0, 8).map((col, i) => (
                 <tr key={i}>
                   <td className="px-6 py-3 font-medium text-slate-700">{col.column}</td>
                   <td className="px-6 py-3 font-mono text-xs text-slate-500 truncate max-w-[200px]">"{col.value}"</td>
                   <td className="px-6 py-3 text-right text-amber-600 font-bold">{col.total_appearances.toLocaleString()}</td>
                 </tr>
               )) : (
                 <tr><td colSpan="3" className="px-6 py-8 text-center text-slate-400 italic">No duplicate values to detail.</td></tr>
               )}
             </tbody>
           </table>
        </div>
      </PageWrapper>

      {/* PAGE 6: OUTLIERS & VALIDATION */}
      <PageWrapper pageNum={6} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Outlier Analysis" icon={<AlertTriangle className="w-6 h-6" />} subtitle="Statistical anomalies and extremes" />
          
          <div className="grid grid-cols-3 gap-4 mb-6">
            <KPICard label="Total Outliers" value={metrics?.total_outliers} icon={<AlertTriangle />} color="rose" />
            <KPICard label="Detection Method" value={outlier_summary?.detection_method || "IQR / Z-Score"} icon={<Search />} color="slate" />
            <KPICard label="Columns Checked" value={outlier_summary?.columns_checked} icon={<Columns />} color="slate" />
          </div>
          
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-sm mb-12 flex flex-col gap-3">
            <div className="font-black text-slate-800 text-sm uppercase tracking-widest mb-1 border-b border-slate-200 pb-2">Outlier Extremes</div>
            <div className="flex justify-between items-center bg-white p-3 rounded-lg border border-slate-100">
              <span className="font-bold text-slate-600">Minimum Outlier Detected</span>
              <span className="font-mono bg-rose-50 text-rose-600 px-2 py-1 rounded text-xs font-bold">{outlier_summary?.minimum_outlier_column}: {outlier_summary?.minimum_outlier_value}</span>
            </div>
            <div className="flex justify-between items-center bg-white p-3 rounded-lg border border-slate-100">
              <span className="font-bold text-slate-600">Maximum Outlier Detected</span>
              <span className="font-mono bg-rose-50 text-rose-600 px-2 py-1 rounded text-xs font-bold">{outlier_summary?.largest_outlier_column}: {outlier_summary?.largest_outlier_value}</span>
            </div>
          </div>
        </div>

        <div className="break-inside-avoid">
          <SectionHeader title="Data Type Validation" icon={<Database className="w-6 h-6" />} subtitle="Schema conformity and structural integrity" />
          
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
             <table className="w-full text-sm text-left">
               <thead className="bg-slate-50 text-xs text-slate-400 uppercase border-b border-slate-200">
                 <tr>
                   <th className="px-6 py-4 font-bold">Column</th>
                   <th className="px-6 py-4 font-bold">Expected Type</th>
                   <th className="px-6 py-4 font-bold">Detected Type</th>
                   <th className="px-6 py-4 font-bold text-right">Mismatches</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-100">
                 {anomalies?.type_validation_issues?.length > 0 ? anomalies.type_validation_issues.map((issue, i) => (
                   <tr key={i}>
                     <td className="px-6 py-4 font-bold text-slate-700">{issue.column}</td>
                     <td className="px-6 py-4 text-slate-500 bg-slate-50/50">{issue.expected}</td>
                     <td className="px-6 py-4 font-mono text-xs text-slate-600">{issue.detected || 'string'}</td>
                     <td className="px-6 py-4 text-right text-rose-500 font-black">{issue.mismatch_count.toLocaleString()}</td>
                   </tr>
                 )) : (
                   <tr><td colSpan="4" className="px-6 py-12 text-center text-slate-500 bg-emerald-50/30 font-medium"><CheckCircle className="w-5 h-5 text-emerald-500 inline mr-2"/> All column data types match their expected schemas perfectly.</td></tr>
                 )}
               </tbody>
             </table>
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 7: AI INSIGHTS */}
      <PageWrapper pageNum={7} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="AI Insights" icon={<Sparkles className="w-6 h-6" />} subtitle="Automated intelligence and observations" />
          
          <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-start gap-4 break-inside-avoid">
              <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg shrink-0 mt-1"><CheckCircle className="w-5 h-5"/></div>
              <div>
                <h4 className="font-bold text-slate-800 text-lg">Dataset Readiness</h4>
                <p className="text-slate-600 mt-1">
                  {scores?.overall_cleanliness > 90 ? 'The dataset is fully prepared for analysis with excellent structural integrity.' : scores?.overall_cleanliness > 70 ? 'The dataset is mostly ready, but requires some targeted cleaning before deployment.' : 'The dataset requires significant cleaning and normalization before it can be used for analysis.'}
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 break-inside-avoid">
              <div className="p-2 bg-amber-100 text-amber-600 rounded-lg shrink-0 mt-1"><Copy className="w-5 h-5"/></div>
              <div>
                <h4 className="font-bold text-slate-800 text-lg">Redundancy Check</h4>
                <p className="text-slate-600 mt-1">
                  {metrics?.total_exact_duplicates === 0 ? 'No exact duplicate rows were detected, ensuring entity uniqueness.' : `${metrics?.total_exact_duplicates.toLocaleString()} duplicate rows were found, which may skew aggregate analysis and model training.`}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 break-inside-avoid">
              <div className="p-2 bg-rose-100 text-rose-600 rounded-lg shrink-0 mt-1"><LayoutGrid className="w-5 h-5"/></div>
              <div>
                <h4 className="font-bold text-slate-800 text-lg">Missing Data Profile</h4>
                <p className="text-slate-600 mt-1">
                  {metrics?.total_missing_values === 0 ? 'Data completeness is perfect with 0 missing cells.' : `Missing values are concentrated in ${metrics?.columns_affected_by_missing} columns, affecting a total of ${metrics?.total_missing_rows_count.toLocaleString()} rows.`}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 break-inside-avoid">
              <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg shrink-0 mt-1"><Database className="w-5 h-5"/></div>
              <div>
                <h4 className="font-bold text-slate-800 text-lg">Type Consistency</h4>
                <p className="text-slate-600 mt-1">
                  {anomalies?.type_validation_issues?.length === 0 ? 'Data types are strictly valid across all columns.' : 'Several columns contain mixed data types or violate their expected schemas.'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-indigo-50 p-6 rounded-2xl border border-indigo-100 break-inside-avoid">
            <h4 className="font-black text-indigo-900 mb-3 text-sm uppercase tracking-widest flex items-center gap-2">
              <Bot className="w-4 h-4"/> Analyst Note
            </h4>
            <p className="text-indigo-800 text-sm leading-relaxed whitespace-pre-wrap">
              {ai_health_report || "The data quality profile suggests a stable underlying structure. Any identified outliers should be treated carefully as they may represent true anomalies rather than errors. Proceed with exploratory analysis while keeping the cleaning recommendations in mind."}
            </p>
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 8: RECOMMENDATIONS */}
      <PageWrapper pageNum={8} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Cleaning Recommendations" icon={<List className="w-6 h-6" />} subtitle="Prioritized actionable steps for data engineering" />
          
          <div className="space-y-6">
             {ai_recommendations && ai_recommendations.length > 0 ? (
               <>
                 {/* High Priority */}
                 {ai_recommendations.filter(r => r.priority === 'Critical' || r.priority === 'High').length > 0 && (
                   <div className="break-inside-avoid">
                     <h3 className="font-black text-rose-600 text-sm uppercase tracking-widest mb-3 border-b border-rose-100 pb-2">High Priority</h3>
                     <div className="space-y-3">
                       {ai_recommendations.filter(r => r.priority === 'Critical' || r.priority === 'High').map((rec, i) => (
                         <div key={`high-${i}`} className="flex items-center justify-between p-4 bg-rose-50 border border-rose-100 rounded-xl break-inside-avoid">
                           <span className="font-bold text-slate-800 text-sm">{rec.action}</span>
                           <span className="text-xs font-black text-emerald-600 bg-white px-2 py-1 rounded shadow-sm">+{rec.improvement}</span>
                         </div>
                       ))}
                     </div>
                   </div>
                 )}
                 
                 {/* Medium Priority */}
                 {ai_recommendations.filter(r => r.priority === 'Medium').length > 0 && (
                   <div className="break-inside-avoid">
                     <h3 className="font-black text-amber-600 text-sm uppercase tracking-widest mb-3 border-b border-amber-100 pb-2 mt-6">Medium Priority</h3>
                     <div className="space-y-3">
                       {ai_recommendations.filter(r => r.priority === 'Medium').map((rec, i) => (
                         <div key={`med-${i}`} className="flex items-center justify-between p-4 bg-amber-50 border border-amber-100 rounded-xl break-inside-avoid">
                           <span className="font-bold text-slate-800 text-sm">{rec.action}</span>
                           <span className="text-xs font-black text-emerald-600 bg-white px-2 py-1 rounded shadow-sm">+{rec.improvement}</span>
                         </div>
                       ))}
                     </div>
                   </div>
                 )}
  
                 {/* Low Priority */}
                 {ai_recommendations.filter(r => r.priority === 'Low').length > 0 && (
                   <div className="break-inside-avoid">
                     <h3 className="font-black text-slate-500 text-sm uppercase tracking-widest mb-3 border-b border-slate-200 pb-2 mt-6">Low Priority</h3>
                     <div className="space-y-3">
                       {ai_recommendations.filter(r => r.priority === 'Low').map((rec, i) => (
                         <div key={`low-${i}`} className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-xl break-inside-avoid">
                           <span className="font-bold text-slate-700 text-sm">{rec.action}</span>
                           <span className="text-xs font-black text-emerald-600 bg-white px-2 py-1 rounded shadow-sm">+{rec.improvement}</span>
                         </div>
                       ))}
                     </div>
                   </div>
                 )}
               </>
             ) : (
               <div className="p-8 bg-slate-50 rounded-2xl border border-slate-200 text-center break-inside-avoid">
                 <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                 <h3 className="text-lg font-bold text-slate-800">No Action Required</h3>
                 <p className="text-sm text-slate-500 mt-1">The dataset meets all quality thresholds. No cleaning steps are recommended.</p>
               </div>
             )}
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 9: PERFORMANCE */}
      <PageWrapper pageNum={9} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Performance Profile" icon={<Cpu className="w-6 h-6" />} subtitle="Engine metrics and computational efficiency" />
          
          <div className="grid grid-cols-2 gap-6 mb-8">
            <div className="bg-slate-900 text-white p-8 rounded-3xl shadow-xl flex flex-col justify-center">
               <div className="text-[10px] uppercase tracking-widest font-bold text-indigo-400 mb-2">Processing Speed</div>
               <div className="text-4xl font-black mb-1">{performance?.processing_speed_rows_per_sec?.toLocaleString()}</div>
               <div className="text-sm font-medium text-slate-400">Rows analyzed per second</div>
            </div>
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm flex flex-col justify-center">
               <div className="text-[10px] uppercase tracking-widest font-bold text-slate-400 mb-2">Analysis Duration</div>
               <div className="text-4xl font-black mb-1 text-slate-800">{performance?.analysis_time_sec}s</div>
               <div className="text-sm font-medium text-slate-500">Total profiling execution time</div>
            </div>
          </div>
  
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-8">
             <table className="w-full text-sm text-left">
               <tbody className="divide-y divide-slate-100">
                 <tr>
                   <td className="px-6 py-4 font-bold text-slate-600 bg-slate-50 w-1/2">Backend Engine</td>
                   <td className="px-6 py-4 font-black text-indigo-600">Polars Vectorized (Rust)</td>
                 </tr>
                 <tr>
                   <td className="px-6 py-4 font-bold text-slate-600 bg-slate-50">Memory Footprint</td>
                   <td className="px-6 py-4 font-bold text-slate-800">{performance?.memory_used_mb} MB</td>
                 </tr>
                 <tr>
                   <td className="px-6 py-4 font-bold text-slate-600 bg-slate-50">Multi-threading</td>
                   <td className="px-6 py-4 font-bold text-slate-800">Enabled (Automatic)</td>
                 </tr>
                 <tr>
                   <td className="px-6 py-4 font-bold text-slate-600 bg-slate-50">Dataset Size</td>
                   <td className="px-6 py-4 font-bold text-slate-800">{(overview?.file_size_bytes / 1024 / 1024).toFixed(2)} MB</td>
                 </tr>
               </tbody>
             </table>
          </div>
          
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-sm text-slate-600 flex items-start gap-4">
            <TerminalSquare className="w-6 h-6 text-slate-400 shrink-0" />
            <p>
              The analysis was executed using the high-performance Polars DataFrame engine, resulting in extremely fast vectorized operations across {metrics?.total_cols} dimensions. Memory usage was optimized to stream operations without out-of-memory errors.
            </p>
          </div>
        </div>
      </PageWrapper>

      {/* PAGE 10: APPENDIX */}
      <PageWrapper pageNum={10} totalPages={TOTAL_PAGES}>
        <div className="break-inside-avoid">
          <SectionHeader title="Appendix: Column Metadata" icon={<FileKey className="w-6 h-6" />} subtitle="Detailed statistical health and metadata per column" />
          
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mt-4">
             <table className="w-full text-xs text-left break-inside-avoid">
               <thead className="bg-slate-900 text-white font-bold uppercase tracking-widest border-b border-slate-200">
                 <tr>
                   <th className="px-4 py-3">Column Name</th>
                   <th className="px-4 py-3 text-right">Unique</th>
                   <th className="px-4 py-3 text-right">Missing %</th>
                   <th className="px-4 py-3 text-right">Duplicate %</th>
                   <th className="px-4 py-3">Health Status</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-100">
                 {distributions?.unique_counts_by_col && Object.entries(distributions.unique_counts_by_col).slice(0, 20).map(([col, count], i) => {
                    const healthInfo = distributions?.column_importance?.[col] || "Good";
                    const missingPct = distributions?.missing_pct_per_column?.[col] || 0;
                    const dupPct = distributions?.duplicate_pct_by_col?.[col] || 0;
                    const isCritical = healthInfo.includes("Critical") || healthInfo.includes("Needs Attention");
                    
                    return (
                      <tr key={i} className="hover:bg-slate-50 break-inside-avoid">
                        <td className="px-4 py-3 font-bold text-slate-700 truncate max-w-[150px]">{col}</td>
                        <td className="px-4 py-3 text-right text-slate-500 font-mono">{count.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono text-slate-500">{missingPct}%</td>
                        <td className="px-4 py-3 text-right font-mono text-slate-500">{dupPct}%</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded font-bold whitespace-nowrap ${
                            isCritical ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'
                          }`}>
                            {healthInfo}
                          </span>
                        </td>
                      </tr>
                    );
                 })}
               </tbody>
             </table>
             {Object.keys(distributions?.unique_counts_by_col || {}).length > 20 && (
               <div className="bg-slate-50 px-4 py-3 text-center text-xs font-bold text-slate-500 border-t border-slate-200 break-inside-avoid">
                 Showing top 20 columns. Refer to the interactive dashboard for the complete metadata catalog.
               </div>
             )}
          </div>
        </div>
      </PageWrapper>
      
    </div>
  );
});

export default PDFReportTemplate;
