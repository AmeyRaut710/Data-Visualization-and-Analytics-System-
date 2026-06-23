import { createContext, useContext, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || "https://data-analytics-backend-gc9m.onrender.com";


const AppContext = createContext();

export function AppProvider({ children }) {
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem('sessionId') || null);
  const [overview, setOverview] = useState(null);

  const saveSession = (id) => {
    setSessionId(id);
    sessionStorage.setItem('sessionId', id);
  };

  const clearSession = () => {
    if (sessionId) {
      fetch(`${API_URL}/api/session/${sessionId}`, { method: 'DELETE', keepalive: true }).catch(() => {});
    }
    setSessionId(null);
    setOverview(null);
    sessionStorage.removeItem('sessionId');
  };

  // Zero-Storage: Destroy session immediately if tab is closed or refreshed
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (sessionId) {
        // Use fetch with keepalive: true to securely transmit a DELETE signal as the tab unloads
        fetch(`${API_URL}/api/session/${sessionId}`, { method: 'DELETE', keepalive: true }).catch(() => {});
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sessionId]);

  return (
    <AppContext.Provider value={{ sessionId, saveSession, clearSession, overview, setOverview }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);
}
