import { useState } from 'react';
import axios from 'axios';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { saveSession, setOverview } = useAppContext();
  const navigate = useNavigate();

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post('http://localhost:8000/api/upload', formData);
      saveSession(res.data.session_id);
      setOverview(res.data.overview);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto mt-10">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-black text-slate-900 mb-4">Upload Your Dataset</h1>
        <p className="text-lg text-slate-600">CSV, XLS, XLSX, or TSV formats supported. Data is processed strictly in-memory.</p>
      </div>
      
      <form onSubmit={handleUpload} className="bg-white p-10 rounded-3xl border border-slate-200 shadow-xl text-center">
        <div className="border-2 border-dashed border-indigo-200 rounded-2xl p-12 bg-indigo-50/50 hover:bg-indigo-50 transition-colors cursor-pointer relative">
          <input 
            type="file" 
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            accept=".csv,.xls,.xlsx,.tsv"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <UploadCloud className="w-16 h-16 text-indigo-500 mx-auto mb-4" />
          <p className="text-xl font-bold text-slate-700">Drag & drop your file here</p>
          <p className="text-slate-500 mt-2">or click to browse</p>
        </div>
        
        {file && (
          <div className="mt-6 flex items-center justify-center gap-3 text-emerald-600 bg-emerald-50 py-3 rounded-lg border border-emerald-200">
            <File className="w-5 h-5" />
            <span className="font-medium">{file.name}</span>
          </div>
        )}
        
        {error && (
          <div className="mt-6 flex items-center justify-center gap-3 text-rose-600 bg-rose-50 py-3 rounded-lg border border-rose-200">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        <button 
          type="submit" 
          disabled={!file || loading}
          className="mt-8 w-full bg-indigo-600 text-white font-bold text-lg py-4 rounded-xl shadow-lg shadow-indigo-200 hover:bg-indigo-700 hover:scale-[1.02] transition-all disabled:opacity-50 disabled:hover:scale-100"
        >
          {loading ? 'Processing Data securely in RAM...' : 'Analyze Dataset'}
        </button>
      </form>
    </div>
  );
}
