import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { convertAPI } from '../api'
import { useAuth } from '../AuthContext'
import '../App.css'

const FORMATS = [
  { value: 'moodle_xml',  label: 'Moodle XML' },
  { value: 'qti',         label: 'QTI 1.2' },
  { value: 'blackboard',  label: 'Blackboard' },
]

export function Convert() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [files, setFiles] = useState([])
  const [format, setFormat] = useState('moodle_xml')
  const [status, setStatus] = useState('idle') // idle | converting | done | error
  const [errorMsg, setErrorMsg] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  function handleFileChange(e) {
    const chosen = Array.from(e.target.files).filter(f => f.name.endsWith('.docx'))
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...chosen.filter(f => !names.has(f.name))]
    })
    e.target.value = ''
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.docx'))
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...dropped.filter(f => !names.has(f.name))]
    })
  }

  function removeFile(name) {
    setFiles(prev => prev.filter(f => f.name !== name))
  }

  async function handleConvert() {
    if (!files.length) return
    setStatus('converting')
    setErrorMsg('')

    try {
      const res = await convertAPI.convert(files, format)
      const blob = new Blob([res.data], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const nameMatch = res.headers['content-disposition']?.match(/filename="([^"]+)"/)
      a.download = nameMatch ? nameMatch[1] : `assessbridge_${format}.zip`
      a.href = url
      a.click()
      URL.revokeObjectURL(url)
      setStatus('done')
      setFiles([])
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Conversion failed.'
      setErrorMsg(errorMsg)
      setStatus('error')
    }
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const canConvert = files.length > 0 && status !== 'converting'

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <div className="logo-mark">AB</div>
          <div>
            <h1>AssessBridge</h1>
            <p className="tagline">Convert assessment DOCX files to LMS formats</p>
          </div>
        </div>
        <div className="header-user">
          <span>Welcome, {user?.username}</span>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="app-main">
        {/* ── Step 1: Upload ── */}
        <section className="card">
          <h2><span className="step">1</span> Upload DOCX files</h2>

          <div
            className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
            onClick={() => inputRef.current.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16v-8m0 0-3 3m3-3 3 3M4.5 19.5h15A2.25 2.25 0 0 0 21.75 17V7.5A2.25 2.25 0 0 0 19.5 5.25H15M4.5 19.5A2.25 2.25 0 0 1 2.25 17V7.5A2.25 2.25 0 0 1 4.5 5.25H9" />
            </svg>
            <p>Drag & drop <code>.docx</code> files here, or <span className="link">browse</span></p>
            <input
              ref={inputRef}
              type="file"
              accept=".docx"
              multiple
              hidden
              onChange={handleFileChange}
            />
          </div>

          {files.length > 0 && (
            <ul className="file-list">
              {files.map(f => (
                <li key={f.name} className="file-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="16" height="16">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                  </svg>
                  <span className="file-name">{f.name}</span>
                  <span className="file-size">{(f.size / 1024).toFixed(1)} KB</span>
                  <button className="remove-btn" onClick={() => removeFile(f.name)} title="Remove">✕</button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ── Step 2: Format ── */}
        <section className="card">
          <h2><span className="step">2</span> Select output format</h2>
          <div className="format-grid">
            {FORMATS.map(f => (
              <label key={f.value} className={`format-option ${format === f.value ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="format"
                  value={f.value}
                  checked={format === f.value}
                  onChange={() => setFormat(f.value)}
                  hidden
                />
                {f.label}
              </label>
            ))}
          </div>
        </section>

        {/* ── Step 3: Convert ── */}
        <section className="card convert-card">
          <h2><span className="step">3</span> Convert & download</h2>
          <button
            className="convert-btn"
            onClick={handleConvert}
            disabled={!canConvert}
          >
            {status === 'converting' ? (
              <><span className="spinner" />Converting…</>
            ) : (
              <>Convert {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : ''} </>
            )}
          </button>

          {status === 'done' && (
            <p className="status-msg success">Download started! Check your Downloads folder.</p>
          )}
          {status === 'error' && (
            <p className="status-msg error">{errorMsg}</p>
          )}
        </section>
      </main>
    </div>
  )
}
