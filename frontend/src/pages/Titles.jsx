import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { titlesAPI } from '../api'
import { WorkspaceShell } from '../components/WorkspaceShell'
import '../App.css'

export function Titles() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [titles, setTitles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAll, setShowAll] = useState(false)

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const visibleTitles = showAll ? titles : titles.slice(0, 3)

  useEffect(() => {
    titlesAPI.list()
      .then(res => setTitles(res.data))
      .catch(() => setError('Unable to load titles. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(id) {
    if (!window.confirm('Delete this title and its uploaded files?')) return
    try {
      await titlesAPI.remove(id)
      setTitles(current => current.filter(title => title.id !== id))
    } catch {
      setError('Unable to delete this title. Please try again.')
    }
  }

  return (
    <WorkspaceShell eyebrow="Workspace overview" title={`${greeting}, ${user?.username || 'there'}`} subtitle="Pick up where you left off.">
      <div className="titles-overview">
        <section className="overview-start">
          <div>
            <p className="eyebrow overview-eyebrow">Start here</p>
            <h2>Convert an assessment package</h2>
            <p>Create a title, add your files, and choose the output format.</p>
          </div>
          <button className="primary-btn overview-cta" onClick={() => navigate('/titles/new')}>＋ New title</button>
        </section>

        <section className="recent-section">
          <div className="recent-heading">
            <div><p className="eyebrow">Your library</p><h2>Recent titles</h2></div>
            {titles.length > 3 && <button className="text-btn recent-toggle" onClick={() => setShowAll(current => !current)}>{showAll ? 'Show less' : 'View all titles'} <span>→</span></button>}
          </div>
          {loading ? (
            <div className="minimal-empty"><div><h3>Loading titles…</h3><p>Fetching your assessment library.</p></div></div>
          ) : error ? (
            <div className="minimal-empty"><div><h3>Something went wrong</h3><p>{error}</p></div></div>
          ) : titles.length === 0 ? (
            <div className="minimal-empty"><span className="empty-icon">＋</span><div><h3>No titles yet</h3><p>Create your first title and upload its assessment files.</p></div><button className="secondary-btn" onClick={() => navigate('/titles/new')}>Create title</button></div>
          ) : (
            <div className="recent-list">
              {visibleTitles.map(title => (
                <article className="recent-row" key={title.id}>
                  <span className="title-badge">AB</span>
                  <div className="recent-title"><h3>{title.name}</h3><p>{title.description || 'No description added.'}</p></div>
                  <time>{new Date(title.created_at).toLocaleDateString()}</time>
                  <button className="text-btn open-link" onClick={() => navigate(`/titles/${title.id}/convert`)}>Open <span>→</span></button>
                  <button className="text-btn danger delete-link" onClick={() => handleDelete(title.id)}>Delete</button>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </WorkspaceShell>
  )
}
