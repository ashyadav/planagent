import type { ExecutionEvent } from '../api'

export default function ExecutionLog({ events }: { events: ExecutionEvent[] }) {
  if (!events.length) return null

  // group by step; non-step events go under their preceding step
  const steps: { label: string; lines: string[] }[] = []
  for (const e of events) {
    const d = e.data
    if (e.type === 'step_started') {
      steps.push({ label: `Step ${d.step}: ${d.description}`, lines: [] })
    } else if (e.type === 'tool_started') {
      steps.at(-1)?.lines.push(`  → ${d.tool}(${JSON.stringify(d.input)})`)
    } else if (e.type === 'tool_finished') {
      steps.at(-1)?.lines.push(`  ← ${d.output}`)
    } else if (e.type === 'step_finished') {
      if (d.output) steps.at(-1)?.lines.push(`  ✓ ${d.output}`)
    } else if (e.type === 'error') {
      steps.at(-1)?.lines.push(`  ✗ ${d.message}`)
    } else if (e.type === 'execution_finished') {
      steps.push({ label: d.success ? '✓ Done' : '✗ Failed', lines: [] })
    }
  }

  return (
    <div>
      {steps.map((s, i) => (
        <div key={i} style={{ marginBottom: '.75rem' }}>
          <strong>{s.label}</strong>
          {s.lines.map((l, j) => <pre key={j}>{l}</pre>)}
        </div>
      ))}
    </div>
  )
}
