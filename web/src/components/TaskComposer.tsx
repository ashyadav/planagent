interface Props {
  onSubmit: (task: string) => void
  disabled: boolean
}

export default function TaskComposer({ onSubmit, disabled }: Props) {
  let value = ''
  return (
    <form onSubmit={e => { e.preventDefault(); if (value.trim()) onSubmit(value.trim()) }}>
      <textarea
        rows={3}
        placeholder="Describe a task…"
        onChange={e => { value = e.target.value }}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>Generate Plan</button>
    </form>
  )
}
