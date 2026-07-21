import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import { Search, ArrowUpDown, ArrowUp, ArrowDown, LayoutGrid, Database, DatabaseBackup, AlertTriangle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


export default function TablePage() {
  const { sessionId, activeSheet } = useAppContext();
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [stats, setStats] = useState(null);
  
  const [dataset, setDataset] = useState('raw'); // 'raw' or 'cleaned'
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState('');
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' or 'desc'
  const [loading, setLoading] = useState(true);

  // Virtualization state
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);
  const ROW_HEIGHT = 41; // px

  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const limit = 100;

  useEffect(() => {
    if (!sessionId) return;
    
    setPage(1);
    setHasMore(true);
    
    const delayDebounceFn = setTimeout(() => {
      fetchData(true, 1);
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, dataset, search, sortCol, sortOrder, activeSheet]);

  const fetchData = async (reset = false, currentPage = page) => {
    try {
      if (reset) {
        setLoading(true);
      }
      const res = await axios.get(`${API_URL}/api/table/${sessionId}`, {
        params: { dataset, page: currentPage, limit, search, sort_col: sortCol, sort_order: sortOrder, sheet: activeSheet }
      });
      
      setColumns(res.data.columns.filter(c => c !== '_row_id'));
      
      if (reset) {
        setData(res.data.data);
      } else {
        setData(prev => [...prev, ...res.data.data]);
      }
      
      setHasMore(res.data.data.length === limit);
      setStats(res.data.stats);
      
      if (reset) {
        setScrollTop(0);
        if (containerRef.current) containerRef.current.scrollTop = 0;
      }
      
      setLoading(false);
    } catch (err) {
      console.error("Error fetching table data:", err);
      setLoading(false);
    }
  };

  const handleSort = (col) => {
    if (sortCol === col) {
      if (sortOrder === 'asc') setSortOrder('desc');
      else { setSortCol(''); setSortOrder('asc'); }
    } else {
      setSortCol(col);
      setSortOrder('asc');
    }
  };

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
    
    if (!loading && hasMore) {
      const bottom = e.target.scrollHeight - e.target.scrollTop - e.target.clientHeight < 200;
      if (bottom) {
        setPage(prev => {
          const nextPage = prev + 1;
          fetchData(false, nextPage);
          return nextPage;
        });
      }
    }
  };

  // Virtualization logic
  // Render about ~60 rows (enough to fill a 4K monitor vertically)
  const renderCount = 60;
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 10); // 10 rows buffer top
  const endIndex = Math.min(data.length, startIndex + renderCount);
  
  const visibleData = data.slice(startIndex, endIndex);
  const paddingTop = startIndex * ROW_HEIGHT;
  const paddingBottom = Math.max(0, (data.length - endIndex) * ROW_HEIGHT);

  if (!sessionId) return <Navigate to="/" />;

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header Area */}
      <div className="bg-white border-b border-slate-200 p-4 md:p-6 shrink-0 z-20 shadow-sm relative">
        <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
          
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              <LayoutGrid className="w-6 h-6 text-indigo-600" /> 
              Dataset Explorer
            </h1>
            <p className="text-sm text-slate-500 font-medium mt-1">Virtualization enabled. Instantly browse 100,000+ rows directly in RAM.</p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Toggle Raw/Cleaned */}
            <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button 
                onClick={() => setDataset('raw')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${dataset === 'raw' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}
              >
                <DatabaseBackup className="w-4 h-4" /> Raw Data
              </button>
              <button 
                onClick={() => setDataset('cleaned')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${dataset === 'cleaned' ? 'bg-indigo-500 shadow text-white' : 'text-slate-500 hover:text-slate-700'}`}
              >
                <Database className="w-4 h-4" /> Cleaned Data
              </button>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search all columns..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium text-slate-700 shadow-sm text-sm w-64"
              />
            </div>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="flex flex-wrap gap-3 mt-6">
            <StatBadge label="Total Rows" value={stats.total_rows.toLocaleString()} />
            <StatBadge label="Columns" value={stats.total_columns.toLocaleString()} />
            <StatBadge label="Missing Cells" value={stats.missing_values.toLocaleString()} alert={stats.missing_values > 0} color="rose" />
            <StatBadge label="Empty Cells" value={stats.empty_cells.toLocaleString()} alert={stats.empty_cells > 0} color="orange" />
            <StatBadge label="Duplicate Rows" value={stats.duplicates.toLocaleString()} alert={stats.duplicates > 0} color="amber" />
            <StatBadge label="Outliers" value={stats.outliers ? stats.outliers.toLocaleString() : "0"} alert={stats.outliers > 0} color="yellow" />
          </div>
        )}
      </div>

      {/* Table Area (Virtualized) */}
      <div className="flex-1 overflow-hidden relative bg-white">
        {loading && (
          <div className="absolute inset-0 z-20 bg-white/50 backdrop-blur-sm flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}
        
        <div 
          ref={containerRef}
          onScroll={handleScroll}
          className="h-full overflow-auto relative custom-scrollbar"
        >
          <table className="w-full text-left border-collapse text-sm whitespace-nowrap min-w-max">
            <thead className="sticky top-0 bg-slate-50 text-slate-600 font-bold shadow-sm z-10">
              <tr>
                <th className="px-4 py-3 border-b border-r border-slate-200 w-16 text-center text-slate-400 select-none">#</th>
                {columns.map((col) => (
                  <th 
                    key={col} 
                    className="px-4 py-3 border-b border-r border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors select-none group"
                    onClick={() => handleSort(col)}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span>{col}</span>
                      <span className="text-slate-400 group-hover:text-indigo-500">
                        {sortCol === col ? (sortOrder === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />) : <ArrowUpDown className="w-3 h-3 opacity-0 group-hover:opacity-100" />}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="text-slate-700 divide-y divide-slate-100">
              {paddingTop > 0 && (
                <tr style={{ height: `${paddingTop}px` }}>
                  <td colSpan={columns.length + 1}></td>
                </tr>
              )}
              
              {visibleData.map((row, indexOffset) => {
                const rIdx = startIndex + indexOffset;
                const isDuplicate = row._is_duplicate;
                const outlierCols = row._outlier_cols || [];
                
                return (
                  <tr key={rIdx} style={{ height: `${ROW_HEIGHT}px` }} className={`hover:bg-indigo-50/50 transition-colors ${isDuplicate ? 'bg-amber-50' : ''}`}>
                    <td className="px-4 py-2 border-r border-slate-100 text-center text-slate-400 font-medium w-16 overflow-hidden">
                       <div className="flex flex-col items-center justify-center h-full">
                         <span>{rIdx + 1}</span>
                         {isDuplicate && <span className="text-[9px] text-amber-600 font-bold uppercase leading-none mt-0.5">Dup</span>}
                       </div>
                    </td>
                    {columns.map((col) => {
                      const val = row[col];
                      const isMissing = val === null || val === undefined;
                      const isEmpty = val === '';
                      const isOutlier = outlierCols.includes(col);
                      
                      let cellClass = "px-4 py-2 border-r border-slate-100 max-w-[300px] truncate ";
                      if (isMissing) cellClass += "bg-rose-100 text-rose-700 font-bold italic ";
                      else if (isEmpty) cellClass += "bg-orange-100 text-orange-800 font-bold italic ";
                      else if (isOutlier) cellClass += "bg-yellow-100 text-yellow-800 font-bold ";

                      return (
                        <td key={col} className={cellClass} title={String(val)}>
                          {isMissing ? 'NaN' : isEmpty ? '(Empty)' : String(val)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
              
              {paddingBottom > 0 && (
                <tr style={{ height: `${paddingBottom}px` }}>
                  <td colSpan={columns.length + 1}></td>
                </tr>
              )}
              
              {data.length === 0 && !loading && (
                <tr>
                  <td colSpan={columns.length + 1} className="px-4 py-12 text-center text-slate-500 font-medium">
                    No records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatBadge({ label, value, alert, color = "indigo" }) {
  const baseClasses = "flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-bold transition-colors";
  
  const colors = {
    indigo: "bg-indigo-50 border-indigo-100 text-indigo-700",
    rose: alert ? "bg-rose-100 border-rose-200 text-rose-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    orange: alert ? "bg-orange-100 border-orange-200 text-orange-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    amber: alert ? "bg-amber-100 border-amber-200 text-amber-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    yellow: alert ? "bg-yellow-100 border-yellow-200 text-yellow-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
  };

  return (
    <div className={`${baseClasses} ${colors[color]}`}>
      <span className="opacity-70 font-medium">{label}:</span>
      {value}
      {alert && <AlertTriangle className="w-3.5 h-3.5 ml-1" />}
    </div>
  );
}
