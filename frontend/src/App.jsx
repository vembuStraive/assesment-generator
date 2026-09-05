import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { ProtectedRoute } from './ProtectedRoute'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Convert } from './pages/Convert'
import { Titles } from './pages/Titles'
import { CreateTitle } from './pages/CreateTitle'
import { WorkspaceSection } from './pages/WorkspaceSection'
import { HelpGuides } from './pages/HelpGuides'
import { Activity } from './pages/Activity'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/titles" element={<ProtectedRoute><Titles /></ProtectedRoute>} />
          <Route path="/titles/new" element={<ProtectedRoute><CreateTitle /></ProtectedRoute>} />
          <Route path="/titles/:titleId/convert" element={<ProtectedRoute><Convert /></ProtectedRoute>} />
          <Route path="/conversions" element={<ProtectedRoute><Activity kind="conversions" /></ProtectedRoute>} />
          <Route path="/downloads" element={<ProtectedRoute><Activity kind="downloads" /></ProtectedRoute>} />
          <Route path="/help" element={<ProtectedRoute><HelpGuides /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><WorkspaceSection eyebrow="Resources" title="Settings" subtitle="Manage your workspace preferences." message="Workspace settings will be available here soon." /></ProtectedRoute>} />
          <Route path="/convert" element={<Navigate to="/titles" replace />} />
          <Route path="/" element={<Navigate to="/titles" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
