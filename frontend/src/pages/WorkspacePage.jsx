import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import { ArrowLeft, Search, Filter, Download, Save, RefreshCw, X, Check, Eye, Trash2, BrainCircuit, ArrowUpDown, ArrowUp, ArrowDown, Eraser, AlertTriangle, Undo2, History, Loader2 } from 'lucide-react';

export default function WorkspacePage() {
  const { sessionId } = useAppContext();
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [stats, setStats] = useState(null);
  
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState('');
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' or 'desc'
  const [loading, setLoading] = useState(true);

  // History state
  const [historyLogs, setHistoryLogs] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Cleaning Popup state
  const [selectedIssue, setSelectedIssue] = useState(null); // { col: 'Age', type: 'Missing Values' }
  const [showPopup, setShowPopup] = useState(false);

  // Bulk Selection state
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [selectedColumns, setSelectedColumns] = useState(new Set());

  // Checkbox toggle functions
  const toggleRow = (rowId) => {
    const newSet = new Set(selectedRows);
    if (newSet.has(rowId)) newSet.delete(rowId);
    else newSet.add(rowId);
    setSelectedRows(newSet);
  };

  const toggleColumn = (col) => {
    const newSet = new Set(selectedColumns);
    if (newSet.has(col)) newSet.delete(col);
    else newSet.add(col);
    setSelectedColumns(newSet);
  };

  const handleBulkRemove = async (type) => {
    if (type === 'rows' && selectedRows.size === 0) return;
    if (type === 'columns' && selectedColumns.size === 0) return;
    
    const confirmMsg = type === 'rows' 
      ? `Are you sure you want to delete ${selectedRows.size} selected row(s)?` 
      : `Are you sure you want to delete ${selectedColumns.size} selected column(s)?`;
      
    if (!window.confirm(confirmMsg)) return;

    setIsProcessing(true);
    setProcessMessage("Cleaning data...");
    try {
      if (type === 'rows') {
        const rowIds = Array.from(selectedRows).join(',');
        await axios.post(`http://localhost:8000/api/clean/${sessionId}/apply`, {
          issue: 'Manual Removal',
          columns: ['all'],
          method: 'Drop Row',
          custom_value: rowIds
        });
        setSelectedRows(new Set());
      } else if (type === 'columns') {
        await axios.post(`http://localhost:8000/api/clean/${sessionId}/apply`, {
          issue: 'Manual Removal',
          columns: Array.from(selectedColumns),
          method: 'Drop Column',
          custom_value: null
        });
        setSelectedColumns(new Set());
      }
      
      setPage(1);
      await fetchData(true, 1);
      await fetchHistory();
      setIsProcessing(false);
    } catch (error) {
      console.error("Failed to bulk remove", error);
      alert("Failed to apply bulk removal");
      setIsProcessing(false);
    }
  };

  // Virtualization state
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);
  const ROW_HEIGHT = 41; // px

  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState("Analyzing...");
  const limit = 100;

  const fetchData = async (reset = false, currentPage = page) => {
    try {
      if (reset) {
        setLoading(true);
      }
      const res = await axios.get(`http://localhost:8000/api/table/${sessionId}`, {
        params: { page: currentPage, limit, search, sort_col: sortCol, sort_order: sortOrder }
      });
      
      setColumns(res.data.columns.filter(c => c !== '_row_id'));
      
      if (reset) {
        setData(res.data.data);
      } else {
        setData(prev => [...prev, ...res.data.data]);
      }
      
      setHasMore(res.data.data.length === limit);
      setStats(res.data.stats);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching table data:", err);
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/api/clean/${sessionId}/history`);
      setHistoryLogs(res.data.history || []);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  };

  useEffect(() => {
    if (!sessionId) return;
    setPage(1);
    setHasMore(true);
    const delayDebounceFn = setTimeout(() => {
      fetchData(true, 1);
      fetchHistory();
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, search, sortCol, sortOrder]);

  const handleUndo = async () => {
    try {
      setIsProcessing(true);
      setProcessMessage("Undoing changes...");
      await axios.post(`http://localhost:8000/api/clean/${sessionId}/undo`);
      setPage(1);
      await fetchData(true, 1);
      await fetchHistory();
      setIsProcessing(false);
    } catch (err) {
      alert(err.response?.data?.detail || "Nothing to undo or error occurred.");
      setIsProcessing(false);
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
    
    // Infinite scroll detection
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

  const handleCellClick = (col, issueType) => {
    if (!issueType) return;
    setSelectedIssue({ col, type: issueType });
    setShowPopup(true);
  };

  const handleManualRemove = async (method, col, rowId = null) => {
    if (!window.confirm(`Are you sure you want to drop this ${method === 'Drop Column' ? 'column' : 'row'}?`)) return;
    
    setIsProcessing(true);
    setProcessMessage("Cleaning data...");
    try {
      await axios.post(`http://localhost:8000/api/clean/${sessionId}/apply`, {
        issue: 'Manual Removal',
        columns: [col],
        method: method,
        custom_value: rowId !== null ? String(rowId) : null
      });
      setPage(1);
      await fetchData(true, 1);
      await fetchHistory();
      setIsProcessing(false);
    } catch (error) {
      console.error("Failed to remove", error);
      alert("Failed to apply removal");
      setIsProcessing(false);
    }
  };

  // Virtualization logic
  const renderCount = 60;
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 10);
  const endIndex = Math.min(data.length, startIndex + renderCount);
  
  const visibleData = data.slice(startIndex, endIndex);
  const paddingTop = startIndex * ROW_HEIGHT;
  const paddingBottom = Math.max(0, (data.length - endIndex) * ROW_HEIGHT);

  if (!sessionId) return <Navigate to="/" />;

  return (
    <div className="h-full flex flex-col bg-slate-50 relative">
      {/* Background Processing Overlay */}
      {isProcessing && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 animate-in zoom-in-95 duration-200">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
            <h3 className="text-xl font-bold text-slate-800">{processMessage}</h3>
            <p className="text-sm text-slate-500">Please wait while the engine processes the dataset...</p>
          </div>
        </div>
      )}

      {/* Header Area */}
      <div className="bg-white border-b border-slate-200 p-4 md:p-6 shrink-0 z-20 shadow-sm relative">
        <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
          
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              <Eraser className="w-6 h-6 text-indigo-600" /> 
              Interactive Workspace
            </h1>
            <p className="text-sm text-slate-500 font-medium mt-1">Click highlighted cells to securely clean data in real-time RAM.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {selectedRows.size > 0 && (
              <button 
                onClick={() => handleBulkRemove('rows')}
                className="flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all border bg-red-50 hover:bg-red-100 text-red-600 border-red-200 shadow-sm"
              >
                <Trash2 className="w-4 h-4" /> Delete Rows ({selectedRows.size})
              </button>
            )}
            {selectedColumns.size > 0 && (
              <button 
                onClick={() => handleBulkRemove('columns')}
                className="flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all border bg-red-50 hover:bg-red-100 text-red-600 border-red-200 shadow-sm"
              >
                <Trash2 className="w-4 h-4" /> Delete Cols ({selectedColumns.size})
              </button>
            )}
            <button 
              onClick={handleUndo}
              disabled={historyLogs.length <= 1}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all border ${historyLogs.length > 1 ? 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 shadow-sm' : 'bg-slate-50 text-slate-400 border-transparent cursor-not-allowed'}`}
            >
              <Undo2 className="w-4 h-4" /> Undo
            </button>
            <button 
              onClick={() => setShowHistory(!showHistory)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all border shadow-sm ${showHistory ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'}`}
            >
              <History className="w-4 h-4" /> History
              <span className="bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5 rounded-md ml-1">{historyLogs.length - 1}</span>
            </button>

            {/* Search */}
            <div className="relative ml-2">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search all columns..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-slate-100 border border-transparent focus:bg-white focus:border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium text-slate-700 shadow-inner focus:shadow-sm text-sm w-64 transition-all"
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
            <StatBadge label="Outliers" value={stats.outliers ? stats.outliers.toLocaleString() : "0"} alert={stats.outliers > 0} color="purple" />
          </div>
        )}
      </div>

      {/* History Panel (Absolute) */}
      {showHistory && (
        <div className="absolute top-32 right-6 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 z-30 flex flex-col max-h-[60vh] overflow-hidden animate-in slide-in-from-top-4 fade-in">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 className="font-bold text-slate-800 flex items-center gap-2"><History className="w-4 h-4" /> Audit Trail</h3>
            <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
          </div>
          <div className="overflow-y-auto p-4 flex-1">
            <ol className="relative border-l border-slate-200 ml-3 space-y-5">
              {historyLogs.map((log, idx) => (
                <li key={idx} className="mb-2 ml-4">
                  <div className={`absolute w-3 h-3 rounded-full mt-1 -left-1.5 border border-white ${idx === historyLogs.length - 1 ? 'bg-indigo-500 ring-4 ring-indigo-50' : 'bg-slate-300'}`}></div>
                  <time className="mb-1 text-xs font-bold leading-none text-slate-400 uppercase">Version {idx}</time>
                  <p className="text-sm font-medium text-slate-700 mt-1">{log}</p>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}

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
                <th className="px-4 py-3 border-b border-r border-slate-200 w-24 text-center text-slate-400 select-none">
                  <div className="flex items-center justify-center gap-2">
                    <input 
                      type="checkbox" 
                      onChange={(e) => {
                        const visibleRowIds = visibleData.map((row, i) => row._row_id !== undefined ? row._row_id : startIndex + i);
                        const allSelected = visibleRowIds.length > 0 && visibleRowIds.every(id => selectedRows.has(id));
                        const newSet = new Set(selectedRows);
                        if (allSelected) {
                          visibleRowIds.forEach(id => newSet.delete(id));
                        } else {
                          visibleRowIds.forEach(id => newSet.add(id));
                        }
                        setSelectedRows(newSet);
                      }}
                      checked={visibleData.length > 0 && visibleData.every((row, i) => {
                        const id = row._row_id !== undefined ? row._row_id : startIndex + i;
                        return selectedRows.has(id);
                      })}
                      className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                    />
                    <span>#</span>
                  </div>
                </th>
                {columns.map((col) => (
                  <th 
                    key={col} 
                    className="px-4 py-3 border-b border-r border-slate-200 hover:bg-slate-100 transition-colors select-none group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <input 
                          type="checkbox"
                          checked={selectedColumns.has(col)}
                          onChange={() => toggleColumn(col)}
                          className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                        />
                        <span className="cursor-pointer" onClick={() => handleSort(col)}>{col}</span>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-slate-400 hover:text-indigo-500 cursor-pointer" onClick={() => handleSort(col)}>
                          {sortCol === col ? (sortOrder === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />) : <ArrowUpDown className="w-3 h-3" />}
                        </span>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleManualRemove('Drop Column', col); }}
                          className="p-1 hover:bg-red-100 text-red-400 hover:text-red-600 rounded transition-colors"
                          title="Drop Column"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
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
                const missingCols = row._missing_cols || [];
                const emptyCols = row._empty_cols || [];
                const invalidTypeCols = row._invalid_type_cols || [];
                const inconsistentCatCols = row._inconsistent_category_cols || [];
                
                return (
                  <tr key={rIdx} style={{ height: `${ROW_HEIGHT}px` }} className={`hover:bg-indigo-50/50 transition-colors ${isDuplicate ? 'bg-yellow-50 cursor-pointer' : ''}`} onClick={() => isDuplicate ? handleCellClick('all', 'Duplicate Rows') : null}>
                    <td className="px-4 py-2 border-r border-slate-100 text-center text-slate-400 font-medium w-24 overflow-hidden group/row relative">
                       <div className="flex flex-row items-center justify-center gap-2 h-full group-hover/row:opacity-0 transition-opacity">
                         <input 
                           type="checkbox"
                           checked={selectedRows.has(row._row_id !== undefined ? row._row_id : rIdx)}
                           onChange={() => toggleRow(row._row_id !== undefined ? row._row_id : rIdx)}
                           onClick={(e) => e.stopPropagation()}
                           className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                         />
                         <div className="flex flex-col items-center">
                           <span>{row._row_id !== undefined ? row._row_id : rIdx + 1}</span>
                           {isDuplicate && <span className="text-[9px] text-yellow-600 font-bold uppercase leading-none mt-0.5">Dup</span>}
                         </div>
                       </div>
                       <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity bg-white/90 gap-1">
                         <input 
                           type="checkbox"
                           checked={selectedRows.has(row._row_id !== undefined ? row._row_id : rIdx)}
                           onChange={() => toggleRow(row._row_id !== undefined ? row._row_id : rIdx)}
                           onClick={(e) => e.stopPropagation()}
                           className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                         />
                         <button 
                           onClick={(e) => { e.stopPropagation(); handleManualRemove('Drop Row', 'all', row._row_id !== undefined ? row._row_id : rIdx); }}
                           className="p-1.5 hover:bg-red-100 text-red-500 rounded-md transition-colors shadow-sm bg-white"
                           title="Drop Row"
                         >
                           <Trash2 className="w-4 h-4" />
                         </button>
                       </div>
                    </td>
                    {columns.map((col) => {
                      const val = row[col];
                      const isMissing = missingCols.includes(col);
                      const isEmpty = emptyCols.includes(col);
                      const isOutlier = outlierCols.includes(col);
                      const isInvalidType = invalidTypeCols.includes(col);
                      const isInconsistent = inconsistentCatCols.includes(col);
                      
                      let cellClass = "px-4 py-2 border-r border-slate-100 max-w-[300px] truncate transition-colors ";
                      let issueType = null;
                      
                      if (isMissing) { cellClass += "bg-red-100 text-red-800 font-bold cursor-pointer hover:bg-red-200 "; issueType = 'Missing Values'; }
                      else if (isEmpty) { cellClass += "bg-orange-100 text-orange-800 font-bold cursor-pointer hover:bg-orange-200 "; issueType = 'Empty Cells'; }
                      else if (isInvalidType) { cellClass += "bg-blue-100 text-blue-800 font-bold cursor-pointer hover:bg-blue-200 "; issueType = 'Invalid Data Types'; }
                      else if (isInconsistent) { cellClass += "bg-teal-100 text-teal-800 font-bold cursor-pointer hover:bg-teal-200 "; issueType = 'Inconsistent Categories'; }
                      else if (isOutlier) { cellClass += "bg-purple-100 text-purple-800 font-bold cursor-pointer hover:bg-purple-200 "; issueType = 'Outliers'; }

                      return (
                        <td key={col} className={cellClass} title={String(val)} onClick={(e) => {
                          if (issueType) {
                            e.stopPropagation();
                            handleCellClick(col, issueType);
                          }
                        }}>
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

      {/* Cleaning Popup */}
      {showPopup && selectedIssue && (
        <CleaningPopup 
          sessionId={sessionId}
          issue={selectedIssue}
          onClose={() => setShowPopup(false)}
          onApply={() => {
            setShowPopup(false);
            fetchData();
            fetchHistory();
          }}
        />
      )}
    </div>
  );
}

function CleaningPopup({ sessionId, issue, onClose, onApply }) {
  const [method, setMethod] = useState('');
  const [customValue, setCustomValue] = useState('');
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    const fetchRec = async () => {
      try {
        const res = await axios.post(`http://localhost:8000/api/clean/${sessionId}/recommend`, { issue: issue.type, columns: [issue.col] });
        setRecommendation(res.data);
      } catch(err) {
        console.error("No recs");
      }
    };
    fetchRec();
  }, [sessionId, issue]);

  const getExplanation = (type) => {
    switch(type) {
      case 'Missing Values': return 'These cells contain null, NaN, or completely missing data.';
      case 'Empty Cells': return 'These cells contain invisible whitespace or empty strings ("").';
      case 'Outliers': return 'These cells deviate significantly from the rest of the column distribution.';
      case 'Invalid Data Types': return 'These cells contain data that does not match the expected type (e.g., text in a numeric column).';
      case 'Inconsistent Categories': return 'These cells use different capitalization for the same category (e.g., "Apple" vs "apple").';
      case 'Duplicate Rows': return 'These rows are exact copies of other rows in the dataset.';
      default: return 'Actionable data quality issue detected.';
    }
  };

  // Available methods based on data_cleaning.py
  const methods = {
    'Missing Values': ['Mean Imputation', 'Median Imputation', 'Mode Imputation', 'Forward Fill', 'Backward Fill', 'Interpolate', 'Replace with Unknown', 'Drop Rows', 'Drop Column'],
    'Empty Cells': ['Replace with Default Value', 'Replace with Mode', 'Replace with Custom User Value', 'Remove Rows'],
    'Outliers': ['Remove Outliers', 'Cap to Upper Bound', 'Replace with Median', 'Replace with Mean', 'Keep Outliers'],
    'Duplicate Rows': ['Keep First Occurrence', 'Keep Latest Occurrence', 'Merge Records'],
    'Invalid Data Types': ['Convert to Numeric', 'Convert to String'],
    'Inconsistent Categories': ['Standardize Format']
  };

  const availableMethods = methods[issue.type] || [];

  const handlePreview = async () => {
    if (!method) return alert("Select a cleaning method.");
    setLoading(true);
    try {
      const res = await axios.post(`http://localhost:8000/api/clean/${sessionId}/preview`, {
        issue: issue.type,
        columns: [issue.col],
        method: method,
        custom_value: customValue
      });
      setPreviewData(res.data);
      setLoading(false);
    } catch (err) {
      alert("Error generating preview.");
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!method) return alert("Select a cleaning method.");
    setApplying(true);
    try {
      const res = await axios.post(`http://localhost:8000/api/clean/${sessionId}/apply`, {
        issue: issue.type,
        columns: [issue.col],
        method: method,
        custom_value: customValue
      });
      setApplying(false);
      onApply(); // Refresh workspace
    } catch (err) {
      alert("Error applying cleaning.");
      setApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <div>
            <h2 className="text-lg font-black text-slate-800 tracking-tight flex items-center gap-2">
              <Eraser className="w-5 h-5 text-indigo-600" /> Resolution Planner
            </h2>
            <p className="text-xs font-bold text-slate-400 mt-1 uppercase tracking-wider">
              {issue.type} in <span className="text-indigo-600">{issue.col}</span>
            </p>
          </div>
          <button onClick={onClose} className="p-2 bg-white border border-slate-200 rounded-full text-slate-400 hover:text-slate-600 shadow-sm"><X className="w-4 h-4" /></button>
        </div>

        {/* Content */}
        <div className="p-6 flex flex-col md:flex-row gap-8 max-h-[70vh] overflow-y-auto bg-white">
          
          {/* Controls */}
          <div className="w-full md:w-1/3 flex flex-col gap-6">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <h4 className="font-bold text-slate-800 text-sm mb-1">Issue Explanation</h4>
              <p className="text-sm text-slate-600">{getExplanation(issue.type)}</p>
            </div>
            
            {recommendation && (
              <div className="bg-indigo-50 p-4 rounded-2xl border border-indigo-100">
                <h4 className="font-bold text-indigo-900 text-sm mb-1 flex items-center gap-1.5"><BrainCircuit className="w-4 h-4" /> AI Recommendation</h4>
                <div className="mt-2 space-y-2">
                  <div><span className="text-xs font-bold text-indigo-400 uppercase">Method</span> <p className="text-sm font-medium text-indigo-800 bg-white px-2 py-1 inline-block rounded shadow-sm border border-indigo-50 mt-0.5">{recommendation.recommended_method}</p></div>
                  <div><span className="text-xs font-bold text-indigo-400 uppercase">Reasoning</span> <p className="text-sm text-indigo-700 leading-snug mt-0.5">{recommendation.reason}</p></div>
                  <div><span className="text-xs font-bold text-indigo-400 uppercase">Confidence</span> <span className="text-sm font-bold text-indigo-600 block">{recommendation.confidence}</span></div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Select Method</label>
              <div className="space-y-2">
                {availableMethods.map(m => (
                  <label key={m} className={`flex items-center p-3 rounded-xl border cursor-pointer transition-all ${method === m ? 'border-indigo-500 bg-indigo-50/50 ring-1 ring-indigo-500' : 'border-slate-200 hover:border-slate-300'}`}>
                    <input type="radio" name="method" value={m} checked={method === m} onChange={(e) => setMethod(e.target.value)} className="text-indigo-600 focus:ring-indigo-500 mr-3" />
                    <span className={`text-sm font-medium ${method === m ? 'text-indigo-900' : 'text-slate-600'}`}>{m}</span>
                  </label>
                ))}
              </div>
            </div>

            {method === 'Replace with Custom User Value' && (
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Custom Value</label>
                <input type="text" value={customValue} onChange={(e) => setCustomValue(e.target.value)} className="w-full p-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm shadow-sm" placeholder="e.g. N/A or 0" />
              </div>
            )}

            <button onClick={handlePreview} disabled={!method || loading} className="w-full py-3 bg-white border border-slate-200 text-slate-700 font-bold rounded-xl shadow-sm hover:bg-slate-50 transition-colors flex justify-center items-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Preview Impact"}
            </button>
          </div>

          {/* Preview */}
          <div className="w-full md:w-2/3 bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-200 bg-white">
              <h3 className="text-sm font-bold text-slate-800">Transformation Preview</h3>
              <p className="text-xs text-slate-500 font-medium">Top 5 affected rows</p>
            </div>
            
            <div className="flex-1 p-4 overflow-auto">
              {!previewData && !loading && (
                 <div className="h-full flex items-center justify-center text-sm font-medium text-slate-400">Select a method and click Preview.</div>
              )}
              {loading && (
                 <div className="h-full flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
              )}
              {previewData && (
                <div className="space-y-4">
                  {previewData.metrics && (
                    <div className="grid grid-cols-2 gap-3 text-sm font-medium text-slate-600 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                       <div className="bg-slate-50 p-2 rounded border border-slate-100"><span className="font-bold text-slate-400 block mb-1">Rows Affected</span> <span className="text-indigo-600 font-bold text-lg">{previewData.metrics.rows_affected}</span></div>
                       <div className="bg-slate-50 p-2 rounded border border-slate-100"><span className="font-bold text-slate-400 block mb-1">Values Changed</span> <span className="text-amber-600 font-bold text-lg">{previewData.metrics.values_changed}</span></div>
                       <div className="bg-slate-50 p-2 rounded border border-slate-100"><span className="font-bold text-slate-400 block mb-1">Rows Removed</span> <span className="text-red-600 font-bold text-lg">{previewData.metrics.rows_removed}</span></div>
                       <div className="bg-emerald-50 p-2 rounded border border-emerald-100"><span className="font-bold text-emerald-500 block mb-1">Est. Quality Imprv.</span> <span className="text-emerald-700 font-bold text-lg">{previewData.metrics.estimated_quality_improvement}</span></div>
                    </div>
                  )}
                  
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                        <tr>
                          <th className="p-3">Row #</th>
                          <th className="p-3">Original Value</th>
                          <th className="p-3">Cleaned Value</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {previewData.original_preview.slice(0, 5).map((origRow, i) => {
                          const cleanRow = previewData.cleaned_preview[i];
                          const origVal = origRow[issue.col];
                          const cleanVal = cleanRow[issue.col];
                          const changed = origVal !== cleanVal;
                          
                          // Don't show unchanged rows to keep preview focused
                          if (!changed && previewData.original_preview.length > 5) return null;
                          
                          return (
                            <tr key={i} className={changed ? 'bg-indigo-50/30' : ''}>
                              <td className="p-3 font-medium text-slate-400">{i + 1}</td>
                              <td className={`p-3 ${origVal === null ? 'text-red-500 font-bold' : origVal === '' ? 'text-orange-500 font-bold' : 'text-slate-600'}`}>{origVal === null ? 'NaN' : origVal === '' ? '(Empty)' : String(origVal)}</td>
                              <td className={`p-3 font-bold ${changed ? 'text-emerald-600' : 'text-slate-600'}`}>{cleanVal === null ? 'NaN' : cleanVal === '' ? '(Empty)' : String(cleanVal)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
          <button onClick={onClose} className="px-6 py-2.5 font-bold text-slate-500 hover:bg-slate-200/50 rounded-xl transition-colors">Cancel</button>
          <button onClick={handleApply} disabled={applying || !method} className="px-6 py-2.5 font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50">
            {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Apply Transformation
          </button>
        </div>

      </div>
    </div>
  );
}

function StatBadge({ label, value, alert, color = "indigo" }) {
  const baseClasses = "flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-bold transition-colors";
  
  const colors = {
    indigo: "bg-indigo-50 border-indigo-100 text-indigo-700",
    rose: alert ? "bg-red-100 border-red-200 text-red-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    orange: alert ? "bg-orange-100 border-orange-200 text-orange-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    amber: alert ? "bg-yellow-100 border-yellow-200 text-yellow-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
    purple: alert ? "bg-purple-100 border-purple-200 text-purple-800 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-600",
  };

  return (
    <div className={`${baseClasses} ${colors[color]}`}>
      <span className="opacity-70 font-medium">{label}:</span>
      {value}
      {alert && <AlertTriangle className="w-3.5 h-3.5 ml-1" />}
    </div>
  );
}
