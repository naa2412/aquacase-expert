import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HistoryProvider } from './context/HistoryContext';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Diagnosis from './pages/Diagnosis';
import Riwayat from './pages/Riwayat';
import BasisKasus from './pages/BasisKasus';
import BasisAturan from './pages/BasisAturan';

export default function App() {
  return (
    <HistoryProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Landing />} />
            <Route path="/diagnosis" element={<Diagnosis />} />
            <Route path="/riwayat" element={<Riwayat />} />
            <Route path="/basis-kasus" element={<BasisKasus />} />
            <Route path="/basis-aturan" element={<BasisAturan />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </HistoryProvider>
  );
}
