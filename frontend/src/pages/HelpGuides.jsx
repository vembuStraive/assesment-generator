import { WorkspaceShell } from '../components/WorkspaceShell'
import '../App.css'

const formats = [
  {
    name: 'Moodle XML',
    description: 'Use this format to import your question bank into Moodle.',
    file: 'A ZIP package containing Moodle XML question files.',
  },
  {
    name: 'QTI 1.2',
    description: 'Use this standard format for platforms that support QTI 1.2 question banks.',
    file: 'A ZIP package containing QTI 1.2 XML files.',
  },
  {
    name: 'Blackboard',
    description: 'Use this format to import assessments into Blackboard.',
    file: 'A Blackboard package ready for import.',
  },
]

export function HelpGuides() {
  return (
    <WorkspaceShell eyebrow="Resources" title="Help & guides" subtitle="Prepare your files and choose the right conversion format.">
      <div className="help-guide">
        <section className="card help-intro">
          <p className="help-kicker">QUICK START</p>
          <h2>Convert an assessment package</h2>
          <p>AssessBridge accepts DOCX source files. Upload one or more files under a title, select the files to include, choose an output format, and download the converted ZIP package.</p>
        </section>

        <section className="card help-section">
          <div className="help-section-heading">
            <span className="step">1</span>
            <div><h2>Supported input formats</h2><p>AssessBridge accepts two DOCX question-bank layouts.</p></div>
          </div>
          <div className="help-format-list help-input-formats">
            <article className="help-format"><h3>Respondus-style DOCX</h3><p>Questions use numbered markers and lettered choices.</p><code>1) Question text<br />A) Choice text<br />Answer: A<br />Diff: 1 Type: MC</code></article>
            <article className="help-format"><h3>Bracketed test-bank DOCX</h3><p>Questions use bracketed markers and four plain choices.</p><code>[Q1]<br />Question text<br />Choice 1 (correct)<br />Choice 2</code></article>
          </div>
          <p className="help-muted">Keep each question, answer choice, and correct answer in separate paragraphs. Unsupported layouts or missing answer markers may be skipped during conversion.</p>
        </section>

        <section className="card help-section">
          <div className="help-section-heading">
            <span className="step">2</span>
            <div><h2>Choose an output format</h2><p>Select the platform where you will use the converted assessment.</p></div>
          </div>
          <div className="help-format-list">
            {formats.map(format => <article className="help-format" key={format.name}><h3>{format.name}</h3><p>{format.description}</p><small>{format.file}</small></article>)}
          </div>
        </section>

        <section className="card help-section">
          <div className="help-section-heading">
            <span className="step">3</span>
            <div><h2>Conversion checklist</h2><p>Follow these steps for a reliable import.</p></div>
          </div>
          <ol className="help-checklist">
            <li>Create or open a title.</li>
            <li>Upload one or more DOCX files. Previously uploaded files remain available for that title.</li>
            <li>Select the files you want to convert and choose Moodle XML, QTI 1.2, or Blackboard.</li>
            <li>Click Convert and download the ZIP package.</li>
            <li>Import the ZIP file in the selected learning platform.</li>
          </ol>
          <p className="help-muted">If Blackboard shows an empty assessment, confirm that you downloaded a newly generated package and that the source DOCX contains supported question and answer content.</p>
        </section>
      </div>
    </WorkspaceShell>
  )
}
