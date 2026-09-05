import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { convertAPI, titlesAPI } from '../api'
import { WorkspaceShell } from '../components/WorkspaceShell'
import '../App.css'

const FORMATS = [
  { value: 'moodle_xml',  label: 'Moodle XML' },
  { value: 'qti',         label: 'QTI 1.2' },
  { value: 'blackboard',  label: 'Blackboard' },
]

export function Convert() {
  const navigate = useNavigate()
  const { titleId } = useParams()
  const [title, setTitle] = useState(null)
  const [files, setFiles] = useState([])
  const [selectedNames, setSelectedNames] = useState([])
  const [format, setFormat] = useState('moodle_xml')
  const [status, setStatus] = useState('idle') // idle | converting | done | error
  const [errorMsg, setErrorMsg] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    Promise.all([titlesAPI.list(), titlesAPI.files(titleId)])
      .then(([titlesRes, filesRes]) => {
        setTitle(titlesRes.data.find(item => String(item.id) === titleId) || null)
        const existingFiles = filesRes.data.map(item => ({
          ...item,
          name: item.original_name,
          size: item.size_bytes,
          existing: true,
        }))
        setFiles(existingFiles)
        setSelectedNames(existingFiles.map(file => file.name))
      })
  }, [titleId])

  function handleFileChange(e) {
    const chosen = Array.from(e.target.files).filter(f => f.name.endsWith('.docx'))
    const names = new Set(files.map(f => f.name))
    const added = chosen.filter(f => !names.has(f.name))
    setFiles(prev => [...prev, ...added.map(file => ({ file, name: file.name, size: file.size, existing: false }))])
    setSelectedNames(selected => [...new Set([...selected, ...added.map(file => file.name)])])
    e.target.value = ''
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.docx'))
    const names = new Set(files.map(f => f.name))
    const added = dropped.filter(f => !names.has(f.name))
    setFiles(prev => [...prev, ...added.map(file => ({ file, name: file.name, size: file.size, existing: false }))])
    setSelectedNames(selected => [...new Set([...selected, ...added.map(file => file.name)])])
  }

  function removeFile(name) {
    setFiles(prev => prev.filter(f => f.name !== name))
    setSelectedNames(prev => prev.filter(item => item !== name))
  }

  function toggleFile(name) {
    setSelectedNames(prev => prev.includes(name) ? prev.filter(item => item !== name) : [...prev, name])
  }

  async function handleConvert() {
    const selectedItems = files.filter(file => selectedNames.includes(file.name))
    const selectedFiles = selectedItems.filter(file => !file.existing).map(item => item.file)
    const selectedExistingIds = selectedItems.filter(file => file.existing).map(item => item.id)
    if (!selectedFiles.length && !selectedExistingIds.length) return
    setStatus('converting')
    setErrorMsg('')

    try {
      const res = await convertAPI.convert(selectedFiles, format, titleId, selectedExistingIds)
      const blob = new Blob([res.data], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const nameMatch = res.headers['content-disposition']?.match(/filename="([^"]+)"/)
      const fallbackName = selectedItems.length > 1
        ? `${(title?.short_name || title?.name || 'assessment').replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, '_')}.zip`
        : `${(title?.short_name || 'assessment').replace(/[\\/:*?"<>|]+/g, '_')}_${(selectedItems[0]?.name || 'assessment').replace(/\.[^.]+$/, '')}_${format === 'blackboard' ? 'blackboard' : format}.zip`
      a.download = nameMatch ? nameMatch[1] : fallbackName
      a.href = url
      a.click()
      URL.revokeObjectURL(url)
      setStatus('done')
      setFiles(current => current.filter(item => item.existing))
      setSelectedNames(files.filter(item => item.existing).map(item => item.name))
    } catch (err) {
      let errorMsg = err.message || 'Conversion failed.'
      if (err.response?.data instanceof Blob) {
        try {
          const responseText = await err.response.data.text()
          const responseBody = JSON.parse(responseText)
          errorMsg = responseBody.detail || errorMsg
        } catch {
          // Keep the Axios message when the response is not JSON.
        }
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail
      }
      setErrorMsg(errorMsg)
      setStatus('error')
    }
  }

  const canConvert = files.length > 0 && status !== 'converting'

  return (
    <WorkspaceShell eyebrow="Conversion" title={title?.name || 'Assessment conversion'} subtitle="Upload source files, choose a format, and download your package.">
      <div className="conversion-main">
        <button className="back-link" onClick={() => navigate('/titles')}>← Back to all titles</button>
        {/* ── Step 1: Upload ── */}
        <section className="card">
          <h2><span className="step">1</span> Upload source files</h2>
          <p className="section-help">Upload one or more DOCX files. If you add multiple files, choose which ones to include below.</p>

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
                  <input type="checkbox" checked={selectedNames.includes(f.name)} onChange={() => toggleFile(f.name)} aria-label={`Include ${f.name}`} />
                  <span className="file-name">{f.name}</span>
                  <span className="file-size">{f.existing ? 'Saved · ' : ''}{(f.size / 1024).toFixed(1)} KB</span>
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
          <p className="section-help">{selectedNames.length} of {files.length} file{files.length === 1 ? '' : 's'} selected for conversion.</p>
          <button
            className="convert-btn"
            onClick={handleConvert}
            disabled={!selectedNames.length || !canConvert}
          >
            {status === 'converting' ? (
              <><span className="spinner" />Converting…</>
            ) : (
              <>Convert {selectedNames.length > 0 ? `${selectedNames.length} file${selectedNames.length > 1 ? 's' : ''}` : ''} </>
            )}
          </button>

          {status === 'done' && (
            <p className="status-msg success">Download started! Check your Downloads folder.</p>
          )}
          {status === 'error' && (
            <p className="status-msg error">{errorMsg}</p>
          )}
        </section>
      </div>
    </WorkspaceShell>
  )
}
