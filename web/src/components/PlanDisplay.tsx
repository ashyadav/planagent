import type { Plan } from '../api'

// ponytail: no animated reveal, add when waiting >2s feels slow
export default function PlanDisplay({ plan }: { plan: Plan | null }) {
  if (!plan) return <p className="dim">Generating plan…</p>
  return (
    <ol>
      {plan.steps.map(s => <li key={s.step}>{s.description}</li>)}
    </ol>
  )
}
