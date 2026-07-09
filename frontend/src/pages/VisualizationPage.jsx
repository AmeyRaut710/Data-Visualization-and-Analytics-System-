import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, LineChart, Line, AreaChart, Area
} from 'recharts';
import { Activity, LayoutGrid, Info, Zap, Search, Filter } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


const COLORS = [
  '#2563eb', // Royal Blue
  '#f97316', // Orange
  '#10b981', // Emerald Green
  '#d946ef', // Magenta
  '#06b6d4', // Teal/Cyan
  '#8b5cf6', // Violet
  '#ef4444', // Red
  '#eab308', // Yellow
];

const GRADIENTS = [
  { stop1: '#3b82f6', stop2: '#60a5fa', border: '#2563eb' }, // Blue
  { stop1: '#ea580c', stop2: '#f97316', border: '#ea580c' }, // Orange
  { stop1: '#059669', stop2: '#10b981', border: '#059669' }, // Emerald Green
  { stop1: '#d01c6a', stop2: '#ec4899', border: '#db2777' }, // Pink
  { stop1: '#7c3aed', stop2: '#a78bfa', border: '#8b5cf6' }, // Violet
  { stop1: '#0891b2', stop2: '#22d3ee', border: '#06b6d4' }, // Teal
  { stop1: '#ca8a04', stop2: '#facc15', border: '#eab308' }, // Yellow
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/90 backdrop-blur-md p-4 border border-slate-200/60 shadow-xl rounded-2xl">
        <p className="font-bold text-slate-800 text-sm mb-2">{label}</p>
        {payload.map((pld, index) => (
          <div key={index} className="flex items-center gap-2 text-sm font-medium">
            <div className="w-3 h-3 rounded-full shadow-inner" style={{ backgroundColor: pld.color || pld.fill }} />
            <span className="text-slate-600 capitalize">{pld.name || pld.dataKey}:</span>
            <span className="text-slate-900 font-black">
              {typeof pld.value === 'number' ? pld.value.toLocaleString() : pld.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function VisualizationPage() {
  const { sessionId } = useAppContext();
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (sessionId) {
      axios.get(`${API_URL}/api/visualizations/${sessionId}`)
        .then(res => {
          setCharts(res.data.visualizations || []);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [sessionId]);

  if (!sessionId) return <Navigate to="/" />;

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center">
      <div className="relative">
        <div className="absolute inset-0 bg-indigo-500 blur-2xl opacity-20 rounded-full animate-pulse"></div>
        <LayoutGrid className="w-16 h-16 text-indigo-500 mb-6 relative z-10 animate-bounce" />
      </div>
      <div className="text-2xl font-black text-slate-800 tracking-tight">Designing Visual Architecture...</div>
      <p className="text-slate-500 mt-2 font-medium">Analyzing multidimensional arrays to construct optimal geometric mappings.</p>
    </div>
  );

  return (
    <div className="p-4 md:p-10 max-w-7xl mx-auto space-y-8">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500 rounded-full mix-blend-screen filter blur-[100px] opacity-20 animate-pulse"></div>
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-pink-500 rounded-full mix-blend-screen filter blur-[80px] opacity-20"></div>
        
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-bold uppercase tracking-wider mb-4">
            <Activity className="w-4 h-4" /> Machine Learning Engine
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-2">
            Data Topography
          </h1>
          <p className="text-indigo-200 text-lg max-w-2xl">
            Our AI has mathematically derived these optimal visual representations based on the statistical variance and cardinality of your dataset.
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search by column or insight..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium text-slate-700 shadow-sm transition-all"
          />
        </div>
        <div className="relative w-full sm:w-64">
          <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <select 
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="w-full pl-12 pr-10 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium text-slate-700 shadow-sm appearance-none cursor-pointer"
          >
            <option value="All">All Chart Types</option>
            <option value="bar">Bar Chart</option>
            <option value="stacked_bar">Stacked Bar</option>
            <option value="grouped_bar">Grouped Bar</option>
            <option value="line">Line / Trend</option>
            <option value="area">Area Chart</option>
            <option value="scatter">Scatter Plot</option>
            <option value="pie">Pie / Donut</option>
            <option value="heatmap">Heatmap</option>
            <option value="histogram">Histogram</option>
          </select>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {charts.filter(chart => {
            if (chart.error) return true;
            const matchesType = filterType === 'All' || (chart.chart_type && chart.chart_type.toLowerCase() === filterType.toLowerCase());
            const searchLower = searchTerm.toLowerCase();
            const matchesSearch = !searchTerm || 
                (chart.x_axis_column && String(chart.x_axis_column).toLowerCase().includes(searchLower)) || 
                (chart.y_axis_column && String(chart.y_axis_column).toLowerCase().includes(searchLower)) ||
                (chart.chart_purpose && String(chart.chart_purpose).toLowerCase().includes(searchLower));
            return matchesType && matchesSearch;
        }).map((chart, idx) => {
          if (chart.error) return null;
          if (!chart.data || !Array.isArray(chart.data) || chart.data.length === 0) return (
            <div key={idx} className="bg-rose-50/50 backdrop-blur-sm p-6 rounded-3xl border border-rose-200/50 shadow-sm text-rose-600 flex items-center gap-4">
              <Info className="w-8 h-8 text-rose-500 shrink-0" />
              <div>
                <h3 className="font-bold text-rose-800">Geometry Generation Failed</h3>
                <p className="text-sm text-rose-600/80 mt-1">{chart.data_error || 'Insufficient variance to plot this metric.'}</p>
              </div>
            </div>
          );

          const yCol = chart.y_axis_column || 'count';
          
          const renderChart = () => {
            if (chart.chart_type === 'bar' || chart.chart_type === 'histogram') {
              const grad = GRADIENTS[idx % GRADIENTS.length];
              return (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={chart.data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`colorBar${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={grad.stop1} stopOpacity={1} />
                        <stop offset="95%" stopColor={grad.stop2} stopOpacity={0.8} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey={chart.x_axis_column} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dy={10} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dx={-10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                    <Tooltip cursor={{ fill: '#f8fafc' }} content={<CustomTooltip />} />
                    <Bar dataKey={yCol} fill={`url(#colorBar${idx})`} radius={[6, 6, 0, 0]} barSize={40} animationDuration={1500} />
                  </BarChart>
                </ResponsiveContainer>
              );
            } else if (chart.chart_type === 'pie' || chart.chart_type === 'donut') {
              return (
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={chart.data}
                      dataKey={yCol}
                      nameKey={chart.x_axis_column}
                      cx="50%"
                      cy="50%"
                      innerRadius={chart.chart_type === 'donut' ? 80 : 0}
                      outerRadius={120}
                      paddingAngle={chart.chart_type === 'donut' ? 5 : 0}
                      stroke="none"
                      animationDuration={1500}
                    >
                      {chart.data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} className="hover:opacity-80 transition-opacity duration-300 cursor-pointer" />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontWeight: 600, color: '#475569' }} />
                  </PieChart>
                </ResponsiveContainer>
              );
            } else if (chart.chart_type === 'scatter') {
              return (
                <ResponsiveContainer width="100%" height={320}>
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" />
                    <XAxis type="number" dataKey={chart.x_axis_column} name={chart.x_axis_column} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dy={10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                    <YAxis type="number" dataKey={yCol} name={yCol} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dx={-10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                    <Tooltip cursor={{ strokeDasharray: '3 3', stroke: '#cbd5e1' }} content={<CustomTooltip />} />
                    <Scatter name="Data Point" data={chart.data} fill="#ec4899" animationDuration={1500}>
                      {chart.data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[(index * 2) % COLORS.length]} opacity={0.7} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              );
            } else if (chart.chart_type === 'line') {
              const grad = GRADIENTS[idx % GRADIENTS.length];
               return (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={chart.data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`colorArea${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={grad.stop1} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={grad.stop2} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey={chart.x_axis_column} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dy={10} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dx={-10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey={yCol} stroke={grad.border} strokeWidth={4} fillOpacity={1} fill={`url(#colorArea${idx})`} animationDuration={1500} />
                  </AreaChart>
                </ResponsiveContainer>
              );
            } else if (chart.chart_type === 'heatmap') {
              const xLabels = [...new Set(chart.data.map(d => d.x))];
              const yLabels = [...new Set(chart.data.map(d => d.y))];
              
              return (
                <div className="w-full h-[320px] overflow-auto border border-slate-100 rounded-xl bg-white p-2 shadow-inner">
                   <div style={{ display: 'grid', gridTemplateColumns: `auto repeat(${xLabels.length}, minmax(60px, 1fr))` }} className="gap-1 text-xs">
                      <div /> 
                      {xLabels.map(xl => <div key={xl} className="font-bold truncate text-center text-slate-500 pb-2" title={xl}>{xl.length > 8 ? xl.substring(0,8)+'..' : xl}</div>)}
                      {yLabels.map(yl => (
                         <React.Fragment key={yl}>
                            <div className="font-bold truncate text-right pr-3 text-slate-500 flex items-center justify-end" title={yl}>{yl.length > 10 ? yl.substring(0,10)+'..' : yl}</div>
                            {xLabels.map(xl => {
                               const cell = chart.data.find(d => d.x === xl && d.y === yl);
                               const val = cell ? cell.value : 0;
                               const intensity = Math.abs(val);
                               const bgColor = val >= 0 ? `rgba(16, 185, 129, ${intensity})` : `rgba(244, 63, 94, ${intensity})`;
                               return (
                                  <div key={`${xl}-${yl}`} className="flex items-center justify-center h-10 rounded text-xs font-bold text-slate-900 shadow-sm border border-black/5 cursor-pointer hover:scale-105 transition-transform" style={{ backgroundColor: bgColor }} title={`${xl} vs ${yl}: ${val}`}>
                                      {val.toFixed(2)}
                                  </div>
                               )
                            })}
                         </React.Fragment>
                      ))}
                   </div>
                </div>
              );
            } else if (chart.chart_type === 'stacked_bar' || chart.chart_type === 'grouped_bar') {
                return (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={chart.data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
                      <XAxis dataKey={chart.x_axis_column} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dy={10} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} dx={-10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                      <Tooltip cursor={{ fill: '#f8fafc' }} content={<CustomTooltip />} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontWeight: 600, color: '#475569' }} />
                      {chart.sub_categories?.map((cat, i) => (
                          <Bar key={cat} dataKey={cat} stackId={chart.chart_type === 'stacked_bar' ? "a" : undefined} fill={COLORS[i % COLORS.length]} radius={chart.chart_type === 'stacked_bar' ? 0 : [4,4,0,0]} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                );
            }
            return null;
          };

          return (
            <div key={idx} className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/40 flex flex-col group hover:shadow-2xl hover:shadow-indigo-200/40 transition-all duration-500 overflow-hidden">
              
              <div className="p-6 md:p-8 border-b border-slate-100 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-slate-800 text-xl tracking-tight group-hover:text-indigo-600 transition-colors">
                      {chart.title || chart.chart_purpose || 'Visualization'}
                    </h3>
                    {chart.relevance_score && (
                      <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold shadow-sm whitespace-nowrap" title="AI Relevance Score">
                        Score: {chart.relevance_score}/100
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-500 leading-relaxed">
                    {chart.key_findings || 'Analyzing spatial correlations.'}
                  </p>
                </div>
                <div className="bg-slate-50 text-slate-400 p-3 rounded-2xl group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-colors">
                  <Zap className="w-5 h-5" />
                </div>
              </div>

              <div className="flex-1 w-full p-6 md:p-8 bg-slate-50/30">
                {renderChart()}
              </div>
              
              {(chart.business_meaning || chart.trend_summary) && (
                <div className="bg-slate-50 px-6 py-4 border-t border-slate-100 flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></div>
                  <span className="text-xs font-bold text-slate-600 uppercase tracking-widest">AI Insight</span>
                  <span className="text-sm font-medium text-slate-700 ml-auto flex-1 text-right">
                    {chart.trend_summary || chart.business_meaning}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
