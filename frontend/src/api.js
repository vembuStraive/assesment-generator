import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

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

export const convertAPI = {
  convert: (files, format) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('format', format)
    return api.post('/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default api
