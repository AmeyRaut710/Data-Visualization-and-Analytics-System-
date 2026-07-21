import React, { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronUp, Download, Table as TableIcon } from 'lucide-react';

export default function DashboardTable({ data, isDark }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;

  const columns = data && data.length > 0 ? Object.keys(data[0]) : [];

  const filteredData = useMemo(() => {
    if (!data) return [];
    let processed = [...data];

    // Search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      processed = processed.filter(row => 
        Object.values(row).some(val => 
          String(val).toLowerCase().includes(term)
        )
      );
    }

    // Sort
    if (sortCol) {
      processed.sort((a, b) => {
        let valA = a[sortCol];
        let valB = b[sortCol];
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';
        
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortAsc ? valA - valB : valB - valA;
        }
        
        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortAsc ? -1 : 1;
        if (strA > strB) return sortAsc ? 1 : -1;
        return 0;
      });
    }

    return processed;
  }, [data, searchTerm, sortCol, sortAsc]);

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const paginatedData = filteredData.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
  };

  const handleExport = () => {
    if (!filteredData.length) return;
    const csvContent = "data:text/csv;charset=utf-8," 
      + columns.join(",") + "\n"
      + filteredData.map(e => columns.map(c => JSON.stringify(e[c] ?? '')).join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "dashboard_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!data || data.length === 0) return null;

  const bgClass = isDark ? 'bg-slate-800' : 'bg-white';
  const borderClass = isDark ? 'border-slate-700' : 'border-slate-200';
  const textClass = isDark ? 'text-slate-200' : 'text-slate-800';
  const mutedTextClass = isDark ? 'text-slate-400' : 'text-slate-500';

  return (
    <div className={`${bgClass} border ${borderClass} rounded-2xl shadow-sm flex flex-col overflow-hidden`}>
      <div className={`p-4 border-b ${borderClass} flex flex-col sm:flex-row justify-between items-center gap-4`}>
        <h3 className={`font-bold flex items-center gap-2 ${textClass}`}>
          <TableIcon className="w-5 h-5 text-indigo-500" />
          Interactive Data Table
        </h3>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className={`w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 ${mutedTextClass}`} />
            <input 
              type="text" 
              placeholder="Search data..." 
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className={`pl-9 pr-4 py-2 text-sm rounded-lg border ${borderClass} outline-none focus:ring-2 focus:ring-indigo-500 ${isDark ? 'bg-slate-900 text-slate-200 placeholder-slate-500' : 'bg-slate-50 text-slate-700'}`}
            />
          </div>
          <button onClick={handleExport} className={`flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-lg border ${borderClass} hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 transition-colors ${isDark ? 'text-slate-300 hover:bg-slate-700' : 'text-slate-600'}`}>
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className={`text-xs uppercase bg-slate-50 ${isDark ? 'bg-slate-900 text-slate-400' : 'text-slate-500'} border-b ${borderClass}`}>
            <tr>
              {columns.map(col => (
                <th 
                  key={col} 
                  onClick={() => handleSort(col)}
                  className="px-6 py-3 font-bold cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                >
                  <div className="flex items-center gap-1">
                    {col}
                    {sortCol === col && (
                      sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={`divide-y ${borderClass}`}>
            {paginatedData.map((row, idx) => (
              <tr key={idx} className={`hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors`}>
                {columns.map(col => (
                  <td key={col} className={`px-6 py-3 whitespace-nowrap ${mutedTextClass}`}>
                    {row[col] !== null ? String(row[col]) : <span className="text-slate-300 italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
            {paginatedData.length === 0 && (
              <tr>
                <td colSpan={columns.length} className={`px-6 py-8 text-center ${mutedTextClass}`}>
                  No matching records found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className={`p-4 border-t ${borderClass} flex justify-between items-center text-sm ${mutedTextClass}`}>
        <div>
          Showing {Math.min((page - 1) * rowsPerPage + 1, filteredData.length)} to {Math.min(page * rowsPerPage, filteredData.length)} of {filteredData.length} records
        </div>
        <div className="flex gap-2">
          <button 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className={`px-3 py-1 rounded-md border ${borderClass} disabled:opacity-50 hover:bg-slate-100 dark:hover:bg-slate-700`}
          >
            Prev
          </button>
          <button 
            disabled={page === totalPages || totalPages === 0}
            onClick={() => setPage(p => p + 1)}
            className={`px-3 py-1 rounded-md border ${borderClass} disabled:opacity-50 hover:bg-slate-100 dark:hover:bg-slate-700`}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
