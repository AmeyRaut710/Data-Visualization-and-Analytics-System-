import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAppContext } from '../context/AppContext';
import { Navigate } from 'react-router-dom';
import { Send, Bot, User } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


export default function ChatPage() {
  const { sessionId } = useAppContext();
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Hello! I am your AI Data Analyst. Ask me anything about your dataset.' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (!sessionId) return <Navigate to="/" />;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/api/chat/${sessionId}`, { message: userMsg });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: 'Sorry, I encountered an error. Is GEMINI_API_KEY configured?' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto p-4 md:p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-slate-900">Conversational Analytics</h1>
        <p className="text-slate-500 mt-1">Chat securely with your data. Session memory is destroyed when you leave.</p>
      </div>

      <div className="flex-1 bg-white rounded-t-3xl border-x border-t border-slate-200 shadow-sm overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-indigo-600'}`}>
              {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>
            <div className={`max-w-[75%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-50 text-slate-800 border border-slate-100 rounded-tl-none'}`}>
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-slate-100 text-indigo-600">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-slate-50 border border-slate-100 p-4 rounded-2xl rounded-tl-none text-slate-500 animate-pulse">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="bg-white p-4 border border-slate-200 rounded-b-3xl shadow-sm flex gap-3">
        <input 
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about your dataset..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50"
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
          className="bg-indigo-600 text-white p-3 px-6 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition-colors disabled:opacity-50"
        >
          Send <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
