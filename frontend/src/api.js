import axios from 'axios'

// Match the backend's explicit IPv4 bind address. On some macOS setups,
// `localhost` resolves to IPv6 first while Uvicorn is listening on 127.0.0.1.
const API_URL = 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

export const authAPI = {
  register: (email, username, password) =>
    api.post('/auth/register', { email, username, password }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  getCurrentUser: () => api.get('/auth/me'),
}

export const titlesAPI = {
  list: () => api.get('/titles'),
  create: (name, description) => api.post('/titles', { name, description }),
  remove: id => api.delete(`/titles/${id}`),
  files: id => api.get(`/titles/${id}/files`),
}

export const convertAPI = {
  convert: (files, format, titleId, sourceFileIds = []) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('format', format)
    formData.append('title_id', titleId)
    formData.append('source_file_ids', JSON.stringify(sourceFileIds))
    return api.post('/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      // ZIP responses must stay binary. Axios otherwise tries to decode the
      // response as text, corrupting non-UTF-8 ZIP bytes on download.
      responseType: 'blob',
    })
  },
}

export const activityAPI = {
  conversions: () => api.get('/activity/conversions'),
  downloads: () => api.get('/activity/downloads'),
  file: id => api.get(`/activity/downloads/${id}/file`, { responseType: 'blob' }),
}

export default api
