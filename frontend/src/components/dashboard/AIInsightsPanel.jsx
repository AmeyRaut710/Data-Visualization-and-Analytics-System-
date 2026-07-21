import React from 'react';
import { Lightbulb, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function AIInsightsPanel({ insights, isDark }) {
  if (!insights || insights.length === 0) return null;

  return (
    <div className={`${isDark ? 'bg-slate-800 border-slate-700' : 'bg-gradient-to-br from-indigo-50 to-white border-indigo-100'} rounded-3xl p-6 shadow-sm border`}>
      <div className="flex items-center gap-2 mb-4">
        <div className={`p-2 rounded-xl ${isDark ? 'bg-slate-700' : 'bg-indigo-100'}`}>
          <Sparkles className={`w-5 h-5 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
        </div>
        <h3 className={`text-lg font-black tracking-tight ${isDark ? 'text-slate-100' : 'text-slate-800'}`}>AI Insights</h3>
      </div>
      
      <div className="space-y-4">
        {insights.map((insight, idx) => (
          <div key={idx} className={`flex gap-3 items-start p-3 rounded-2xl border shadow-sm backdrop-blur-sm ${isDark ? 'bg-slate-700/60 border-slate-600' : 'bg-white/60 border-white/50'}`}>
            <Lightbulb className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div className={`font-medium text-sm ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              <ReactMarkdown>{insight}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
