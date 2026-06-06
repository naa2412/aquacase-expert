import axios from 'axios';

// Saat development: VITE_API_URL tidak di-set
// Saat production:  VITE_API_URL diisi URL Railway
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor untuk error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error — server down
      error.userMessage = 'Gagal menghubungi server. Pastikan backend berjalan di port 8000.';
    } else if (error.response.status === 422) {
      const detail = error.response.data?.detail;
      error.userMessage = typeof detail === 'string'
        ? detail
        : 'Data yang dikirim tidak valid.';
    } else if (error.response.status === 404) {
      error.userMessage = error.response.data?.detail || 'Data tidak ditemukan.';
    } else {
      error.userMessage = 'Terjadi kesalahan pada server.';
    }
    return Promise.reject(error);
  }
);

// API Functions
export const getIkan = () => api.get('/api/v1/ikan');
export const getGejala = (kodeIkan) => api.get('/api/v1/gejala', { params: kodeIkan ? { kode_ikan: kodeIkan } : {} });
export const getPenyakit = () => api.get('/api/v1/penyakit');
export const postDiagnose = (data) => api.post('/api/v1/diagnose', data);
export const getKasus = () => api.get('/api/v1/kasus');
export const getAturan = () => api.get('/api/v1/aturan');
export const healthCheck = () => api.get('/');

export default api;
