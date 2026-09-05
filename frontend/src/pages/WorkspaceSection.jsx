import { WorkspaceShell } from '../components/WorkspaceShell'
import '../App.css'

export function WorkspaceSection({ eyebrow, title, subtitle, message }) {
  return (
    <WorkspaceShell eyebrow={eyebrow} title={title} subtitle={subtitle}>
      <section className="workspace-empty card">
        <span className="workspace-empty-icon">＋</span>
        <h2>{title}</h2>
        <p>{message}</p>
      </section>
    </WorkspaceShell>
  )
}
