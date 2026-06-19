import type { ExecutionEvent } from '../api'

export default function ResultCard({ events }: { events: ExecutionEvent[] }) {
  const finished = events.find(e => e.type === 'execution_finished')
  if (!finished) return null

  const success = finished.data.success as boolean

  // last step_finished output is the agent's final answer
  const lastOutput = [...events]
    .reverse()
    .find(e => e.type === 'step_finished' && e.data.output)
    ?.data.output as string | undefined

  const cardStyle: React.CSSProperties = {
    margin: '1rem 0',
    padding: '1rem',
    borderRadius: 6,
    border: `1px solid ${success ? '#b7e1b7' : '#f5c6c6'}`,
    background: success ? '#f0fbf0' : '#fff5f5',
  }

  return (
    <div style={cardStyle}>
      <strong style={{ color: success ? '#2a7a2a' : '#c00' }}>
        {success ? '✓ Result' : '✗ Failed'}
      </strong>
      {lastOutput && <p style={{ margin: '.5rem 0 0', whiteSpace: 'pre-wrap' }}>{lastOutput}</p>}
    </div>
  )
}
