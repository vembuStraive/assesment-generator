import { useEffect, useState } from 'react'
import { WorkspaceShell } from '../components/WorkspaceShell'
import { activityAPI } from '../api'
import '../App.css'

export function Activity({ kind }) {
  const isDownloads = kind === 'downloads'
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function handleDownload(item) {
    try {
      const response = await activityAPI.file(item.id)
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = item.filename
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Unable to download this package.')
    }
  }

  useEffect(() => {
    const request = isDownloads ? activityAPI.downloads() : activityAPI.conversions()
    request.then(res => setItems(res.data)).catch(() => setError(`Unable to load ${isDownloads ? 'downloads' : 'conversion history'}.`)).finally(() => setLoading(false))
  }, [isDownloads])

  return (
    <WorkspaceShell eyebrow="Activity" title={isDownloads ? 'Downloads' : 'Recent conversions'} subtitle={isDownloads ? 'Access your converted assessment packages.' : 'Review your latest conversion activity.'}>
      <section className="activity-panel card">
        {loading ? <p className="activity-message">Loading activity…</p> : error ? <p className="activity-message error-text">{error}</p> : items.length === 0 ? <p className="activity-message">{isDownloads ? 'Your converted packages will appear here after a successful conversion.' : 'Conversion history will appear here after you convert an assessment package.'}</p> : (
          <div className="activity-list">
            {items.map(item => <article className="activity-row" key={item.id}>
              <span className="title-badge">{isDownloads ? '↓' : '↻'}</span>
              <div className="activity-title"><h3>{item.title_name}</h3><p>{isDownloads ? item.filename : `${item.file_count} file${item.file_count === 1 ? '' : 's'} · ${item.output_format}`}</p></div>
              <span className={`activity-status ${item.status || 'completed'}`}>{item.status || 'available'}</span>
              <time>{new Date(isDownloads ? item.downloaded_at : item.created_at).toLocaleDateString()}</time>
              {isDownloads && <button className="activity-download" onClick={() => handleDownload(item)}>Download →</button>}
            </article>)}
          </div>
        )}
      </section>
    </WorkspaceShell>
  )
}
