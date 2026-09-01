import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { ProtectedRoute } from './ProtectedRoute'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Convert } from './pages/Convert'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/convert"
            element={
              <ProtectedRoute>
                <Convert />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/convert" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
