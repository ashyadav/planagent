import type { ExecutionEvent } from '../api'

interface Step { label: string; lines: string[] }

export function buildSteps(events: ExecutionEvent[]): Step[] {
  const steps: Step[] = []
  for (const e of events) {
    const d = e.data
    if (e.type === 'step_started') {
      steps.push({ label: `Step ${d.step}: ${d.description}`, lines: [] })
    } else if (e.type === 'tool_started') {
      steps.at(-1)?.lines.push(`→ ${d.tool}(${JSON.stringify(d.input)})`)
    } else if (e.type === 'tool_finished') {
      steps.at(-1)?.lines.push(`← ${d.output}`)
    } else if (e.type === 'step_finished') {
      if (d.output) steps.at(-1)?.lines.push(`✓ ${d.output}`)
    } else if (e.type === 'error') {
      steps.at(-1)?.lines.push(`✗ ${d.message}`)
    }
    // ponytail: execution_finished handled by ResultCard, not shown here
  }
  return steps
}

// ponytail: <details>/<summary> for collapse — no JS, no state
export default function ExecutionLog({ events, done }: { events: ExecutionEvent[]; done: boolean }) {
  if (!events.length) return null
  const steps = buildSteps(events)

  return (
    <details open={!done} style={{ margin: '1rem 0', border: '1px solid #ddd', borderRadius: 4, padding: '.5rem' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
        Execution trace ({steps.length} step{steps.length !== 1 ? 's' : ''})
      </summary>
      <div style={{ marginTop: '.5rem' }}>
        {steps.map((s, i) => (
          <div key={i} style={{ marginBottom: '.75rem' }}>
            <strong>{s.label}</strong>
            {s.lines.map((l, j) => <pre key={j}>{l}</pre>)}
          </div>
        ))}
      </div>
    </details>
  )
}
