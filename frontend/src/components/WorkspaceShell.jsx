import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import straiveLogo from '../assets/straive-logo.webp'

export function WorkspaceShell({ children, eyebrow, title, subtitle }) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="workspace-layout">
      <aside className="workspace-sidebar">
        <button className="sidebar-brand" onClick={() => navigate('/titles')} aria-label="Go to titles">
          <span className="sidebar-brand-copy"><img className="straive-logo sidebar-logo" src={straiveLogo} alt="Straive" /><strong>AssessBridge</strong><small>Assessment workspace</small></span>
        </button>
        <nav className="sidebar-nav" aria-label="Workspace navigation">
          <div className="sidebar-section">
            <p className="sidebar-label">Workspace</p>
            <NavLink to="/titles" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} end><span className="nav-icon">▦</span>All titles</NavLink>
            <NavLink to="/titles/new" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">＋</span>New title</NavLink>
          </div>
          <div className="sidebar-section">
            <p className="sidebar-label">Activity</p>
            <NavLink to="/conversions" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">↻</span>Recent conversions</NavLink>
            <NavLink to="/downloads" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">↓</span>Downloads</NavLink>
          </div>
          <div className="sidebar-section">
            <p className="sidebar-label">Resources</p>
            <NavLink to="/help" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">?</span>Help &amp; guides</NavLink>
            <NavLink to="/settings" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">⚙</span>Settings</NavLink>
          </div>
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip"><span className="user-avatar">{user?.username?.slice(0, 1).toUpperCase() || 'U'}</span><span><strong>{user?.username}</strong><small>{user?.email}</small></span></div>
          <button className="sidebar-logout" onClick={handleLogout}>Sign out <span>↗</span></button>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-topbar">
          <div className="workspace-topbar-inner">
            <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{subtitle && <p className="page-subtitle">{subtitle}</p>}</div>
            <span className="topbar-brand"><img className="straive-logo topbar-logo" src={straiveLogo} alt="Straive" /><strong>AssessBridge</strong></span>
          </div>
        </header>
        <main className="workspace-main">{children}</main>
      </div>
    </div>
  )
}
