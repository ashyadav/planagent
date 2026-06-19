import { useRef, useState } from 'react'
import { postPlan, streamExecute } from './api'
import type { ExecutionEvent, Plan } from './api'
import ExecutionLog from './components/ExecutionLog'
import PlanDisplay from './components/PlanDisplay'
import ResultCard from './components/ResultCard'
import TaskComposer from './components/TaskComposer'

type State = 'idle' | 'planning' | 'executing' | 'done' | 'error'

export default function App() {
  const [state, setState] = useState<State>('idle')
  const [plan, setPlan] = useState<Plan | null>(null)
  const [events, setEvents] = useState<ExecutionEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const cancelRef = useRef<(() => void) | null>(null)

  async function handleTask(task: string) {
    setState('planning')
    setPlan(null)
    setEvents([])
    setError(null)

    let p: Plan
    try {
      p = await postPlan(task)
    } catch (e) {
      setError(String(e))
      setState('error')
      return
    }

    setPlan(p)
    setState('executing')

    cancelRef.current = streamExecute(
      task,
      p,
      (ev) => {
        setEvents(prev => [...prev, ev])
        if (ev.type === 'execution_finished') setState('done')
      },
      (err) => { setError(err.message); setState('error') },
    )
  }

  const busy = state === 'planning' || state === 'executing'

  return (
    <div style={{ padding: '1rem' }}>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '1rem' }}>PlanAgent</h1>
      <TaskComposer onSubmit={handleTask} disabled={busy} />
      {state !== 'idle' && <PlanDisplay plan={plan} />}
      <ExecutionLog events={events} done={state === 'done' || state === 'error'} />
      <ResultCard events={events} />
      {error && <p className="err">{error}</p>}
    </div>
  )
}
