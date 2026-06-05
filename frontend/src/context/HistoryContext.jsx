import { createContext, useContext, useState, useEffect } from 'react';

const HistoryContext = createContext();

const STORAGE_KEY = 'aquacase_riwayat';

export function HistoryProvider({ children }) {
  const [riwayat, setRiwayat] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(riwayat));
  }, [riwayat]);

  const tambahRiwayat = (entry) => {
    const newEntry = {
      id: Date.now().toString(),
      tanggal: new Date().toISOString(),
      ...entry,
    };
    setRiwayat((prev) => [newEntry, ...prev]);
    return newEntry;
  };

  const hapusRiwayat = (id) => {
    setRiwayat((prev) => prev.filter((r) => r.id !== id));
  };

  const hapusSemua = () => {
    setRiwayat([]);
  };

  return (
    <HistoryContext.Provider value={{ riwayat, tambahRiwayat, hapusRiwayat, hapusSemua }}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory() {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error('useHistory harus digunakan di dalam HistoryProvider');
  }
  return context;
}
