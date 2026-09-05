import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { titlesAPI } from '../api'
import { WorkspaceShell } from '../components/WorkspaceShell'
import '../App.css'

export function CreateTitle() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const res = await titlesAPI.create(name.trim(), description.trim() || null)
      navigate(`/titles/${res.data.id}/convert`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to create title. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <WorkspaceShell eyebrow="New title" title="Set up your assessment" subtitle="Add title information before uploading source DOCX files.">
      <div className="form-main">
        <button className="back-link" onClick={() => navigate('/titles')}>← Back to all titles</button>
        <form className="card title-form" onSubmit={handleSubmit}>
          {error && <p className="status-msg error">{error}</p>}
          <div className="form-group"><label htmlFor="title-name">Title name <span>*</span></label><input id="title-name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Business Communication Essentials" required autoFocus /><small>Use a clear name you will recognize later.</small></div>
          <div className="form-group"><label htmlFor="title-description">Description <em>(optional)</em></label><textarea id="title-description" rows="4" value={description} onChange={e => setDescription(e.target.value)} placeholder="Add course, semester, or other helpful details." /></div>
          <div className="form-actions"><button type="button" className="secondary-btn" onClick={() => navigate('/titles')}>Cancel</button><button type="submit" className="primary-btn" disabled={!name.trim() || saving}>{saving ? 'Creating…' : <>Continue to upload <span>→</span></>}</button></div>
        </form>
      </div>
    </WorkspaceShell>
  )
}
