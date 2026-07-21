import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function KPICard({ title, value, type, format, isDark }) {
  
  const formattedValue = () => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
    }
    if (format === 'number') {
      return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value);
    }
    return value;
  };

  const getIcon = () => {
    if (type === 'sum') return <TrendingUp className="w-5 h-5 text-emerald-500" />;
    if (type === 'average') return <Minus className="w-5 h-5 text-indigo-500" />;
    return <TrendingUp className="w-5 h-5 text-indigo-500" />;
  };

  return (
    <div className={`${isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} rounded-3xl p-6 shadow-sm border hover:shadow-md transition-all flex flex-col justify-between h-full`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{title}</h3>
        <div className={`p-2 rounded-xl ${isDark ? 'bg-slate-700' : 'bg-slate-50'}`}>
          {getIcon()}
        </div>
      </div>
      <div>
        <p className={`text-3xl font-black tracking-tight ${isDark ? 'text-slate-100' : 'text-slate-800'}`}>{formattedValue()}</p>
      </div>
    </div>
  );
}
