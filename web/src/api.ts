export interface PlanStep {
  step: number
  description: string
}

export interface Plan {
  steps: PlanStep[]
}

export type ExecutionEventType =
  | 'step_started'
  | 'tool_started'
  | 'tool_finished'
  | 'step_finished'
  | 'error'
  | 'execution_finished'

export interface ExecutionEvent {
  type: ExecutionEventType
  data: Record<string, unknown>
}

export async function postPlan(task: string): Promise<Plan> {
  const res = await fetch('/api/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Failed to generate plan')
  }
  return res.json()
}

export function streamExecute(
  task: string,
  plan: Plan,
  onEvent: (event: ExecutionEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const url = new URL('/api/execute', window.location.origin)
  const body = JSON.stringify({ task, plan })

  let cancelled = false
  let es: EventSource | null = null

  fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  }).then(async (res) => {
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      onError(new Error(err.detail ?? 'Execution failed'))
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (!cancelled) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event: ExecutionEvent = JSON.parse(line.slice(6))
            onEvent(event)
          } catch {
            // skip malformed line
          }
        }
      }
    }
  }).catch(onError)

  return () => { cancelled = true; es?.close() }
}
