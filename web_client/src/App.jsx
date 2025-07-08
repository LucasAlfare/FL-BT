import { useEffect, useRef, useState } from 'react'

const SERVER = 'http://localhost:8000'

export default function App() {
  const [input, setInput] = useState('')
  const [tasks, setTasks] = useState([])
  const intervalRef = useRef(null)

  const handleSubmit = async () => {
    const ids = input
      .split('\n')
      .map((id) => id.trim())
      .filter(Boolean)

    const newTasks = []

    for (const id of ids) {
      try {
        const res = await fetch(`${SERVER}/api/request/${id}`, {
          method: 'POST'
        })

        if (!res.ok) {
          throw new Error(`Erro ${res.status}`)
        }

        const data = await res.json()

        if (!data || !data.video_id) {
          throw new Error('Resposta inválida da API')
        }

        newTasks.push({
          id: data.video_id,
          status: data.status,
          error: null
        })
      } catch (e) {
        newTasks.push({
          id,
          status: 'ERROR',
          error: e.message || 'Falha ao enviar para API'
        })
      }
    }

    setTasks(newTasks)
  }

  useEffect(() => {
    if (tasks.length === 0 || intervalRef.current) return

    intervalRef.current = setInterval(async () => {
      const updatedTasks = await Promise.all(
        tasks.map(async (task) => {
          if (['SUCCESS', 'FAILURE', 'EXPIRED', 'ERROR'].includes(task.status)) return task

          try {
            const res = await fetch(`${SERVER}/api/status/${task.id}`)
            if (!res.ok) throw new Error(`Erro ${res.status}`)
            const data = await res.json()

            if (data.status === 'SUCCESS') {
              const fileRes = await fetch(`${SERVER}/api/download/${task.id}`)
              const blob = await fileRes.blob()
              const url = URL.createObjectURL(blob)

              const a = document.createElement('a')
              a.href = url
              a.download = `${task.id}.zip`
              document.body.appendChild(a)
              a.click()
              a.remove()
              URL.revokeObjectURL(url)
            }

            return {
              ...task,
              status: data.status,
              error: data.error || null
            }
          } catch (err) {
            return {
              ...task,
              error: err.message || 'Erro ao verificar status'
            }
          }
        })
      )

      setTasks(updatedTasks)

      const stillRunning = updatedTasks.some(
        (t) => !['SUCCESS', 'FAILURE', 'EXPIRED', 'ERROR'].includes(t.status)
      )

      if (!stillRunning) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }, 2000)

    return () => {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [tasks])

  return (
    <div style={{ padding: 16, maxWidth: 800, margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h2>Separador de Áudio YouTube</h2>

      <label>
        IDs do YouTube (1 por linha):
        <br />
        <textarea
          rows={6}
          style={{ width: '100%', marginTop: 8 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
      </label>

      <button style={{ marginTop: 12 }} onClick={handleSubmit}>
        Enviar IDs
      </button>

      <div style={{ marginTop: 24 }}>
        <h3>Progresso</h3>
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              {task.id} → {task.status}{' '}
              {task.error && <span style={{ color: 'red' }}>Erro: {task.error}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}