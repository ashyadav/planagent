import type { Plan } from '../api'

export default function PlanDisplay({ plan, done }: { plan: Plan | null; done: boolean }) {
  if (!plan) return <p className="dim">Generating plan…</p>
  return (
    <details open={!done} style={{ margin: '1rem 0', border: '1px solid #ddd', borderRadius: 4, padding: '.5rem' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
        Plan ({plan.steps.length} step{plan.steps.length !== 1 ? 's' : ''})
      </summary>
      <ol style={{ marginTop: '.5rem' }}>
        {plan.steps.map(s => <li key={s.step}>{s.description}</li>)}
      </ol>
    </details>
  )
}
