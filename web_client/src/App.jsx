import { useEffect, useRef, useState } from 'react'

const SERVER = 'http://localhost:8000'

export default function App() {
  const [input, setInput] = useState('')
  const [tasks, setTasks] = useState([])
  const intervalRef = useRef(null)

  const handleSubmit = async () => {
    const videoIds = input
      .split('\n')
      .map((id) => id.trim())
      .filter(Boolean)

    const newTasks = []

    for (const videoId of videoIds) {
      try {
        const res = await fetch(`${SERVER}/api/submit/${videoId}`, { method: 'POST' })
        if (!res.ok) throw new Error(`Erro ${res.status}`)

        const data = await res.json()
        if (!data?.task_id) throw new Error('Resposta inválida da API')

        newTasks.push({
          videoId: data.video_id,
          taskId: data.task_id,
          status: data.status,
          error: null
        })
      } catch (e) {
        newTasks.push({
          videoId,
          taskId: null,
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
          if (!task.taskId || ['SUCCESS', 'FAILURE', 'EXPIRED', 'ERROR'].includes(task.status)) return task

          try {
            const res = await fetch(`${SERVER}/api/status/${task.taskId}`)
            if (!res.ok) throw new Error(`Erro ${res.status}`)
            const data = await res.json()

            if (data.status === 'SUCCESS') {
              const fileRes = await fetch(`${SERVER}/api/download/${task.taskId}`)
              const blob = await fileRes.blob()
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${task.videoId}.zip`
              document.body.appendChild(a)
              a.click()
              a.remove()
              URL.revokeObjectURL(url)
            }

            return { ...task, status: data.status, error: data.error || null }
          } catch (err) {
            return { ...task, error: err.message || 'Erro ao verificar status' }
          }
        })
      )

      setTasks(updatedTasks)

      const running = updatedTasks.some(
        (t) => !['SUCCESS', 'FAILURE', 'EXPIRED', 'ERROR'].includes(t.status)
      )
      if (!running) {
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
      <h2>Separador de Áudio do YouTube</h2>
      <label>
        IDs do YouTube (1 por linha):
        <textarea
          rows={6}
          style={{ width: '100%', marginTop: 8 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
      </label>
      <button style={{ marginTop: 12 }} onClick={handleSubmit}>Enviar IDs</button>

      <div style={{ marginTop: 24 }}>
        <h3>Progresso</h3>
        <ul>
          {tasks.map((task) => (
            <li key={task.videoId}>
              {task.videoId} → {task.status}
              {task.error && <span style={{ color: 'red' }}> Erro: {task.error}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

/*
worker-1  | [2025-07-10 21:54:15,814: WARNING/MainProcess] Exception ignored in:
worker-1  | [2025-07-10 21:54:15,829: WARNING/MainProcess] <generator object Estimator.predict at 0x7f07606d85f0>
worker-1  | [2025-07-10 21:54:15,830: WARNING/MainProcess] Traceback (most recent call last):
worker-1  | [2025-07-10 21:54:15,830: WARNING/MainProcess]   File "/app/.venv/lib/python3.10/site-packages/tensorflow_estimator/python/estimator/estimator.py", line 618, in predict
worker-1  | [2025-07-10 21:54:15,836: WARNING/MainProcess] with tf.Graph().as_default() as g:
worker-1  | [2025-07-10 21:54:15,836: WARNING/MainProcess]   File "/usr/local/lib/python3.10/contextlib.py", line 153, in __exit__
worker-1  | [2025-07-10 21:54:15,837: WARNING/MainProcess] self.gen.throw(typ, value, traceback)
worker-1  | [2025-07-10 21:54:15,837: WARNING/MainProcess]   File "/app/.venv/lib/python3.10/site-packages/tensorflow/python/framework/ops.py", line 5821, in get_controller
worker-1  | [2025-07-10 21:54:15,841: WARNING/MainProcess] with super(_DefaultGraphStack,
worker-1  | [2025-07-10 21:54:15,841: WARNING/MainProcess]   File "/usr/local/lib/python3.10/contextlib.py", line 153, in __exit__
worker-1  | [2025-07-10 21:54:15,841: WARNING/MainProcess]
worker-1  | [2025-07-10 21:54:15,841: WARNING/MainProcess] self.gen.throw(typ, value, traceback)
worker-1  | [2025-07-10 21:54:15,841: WARNING/MainProcess]   File "/app/.venv/lib/python3.10/site-packages/tensorflow/python/framework/ops.py", line 5633, in get_controller
worker-1  | [2025-07-10 21:54:15,842: WARNING/MainProcess]
worker-1  | [2025-07-10 21:54:15,842: WARNING/MainProcess] raise AssertionError(
worker-1  | [2025-07-10 21:54:15,843: WARNING/MainProcess] AssertionError
worker-1  | [2025-07-10 21:54:15,843: WARNING/MainProcess] :
worker-1  | [2025-07-10 21:54:15,843: WARNING/MainProcess] Nesting violated for default stack of <class 'tensorflow.python.framework.ops.Graph'> objects
worker-1  | [2025-07-10 21:54:15,887: WARNING/MainProcess] [ERROR] Separation failed: When eager execution is enabled, use_resource cannot be set to false.
worker-1  | [2025-07-10 21:54:15,892: ERROR/MainProcess] Task server.celery_worker.heavy_processing_entrypoint[4a7b671f-2d07-41dd-80e0-9f32d277b31d] raised unexpected: RuntimeError('Separation failed')
worker-1  | RuntimeError: Separation failed
*/