import {useEffect, useRef, useState} from 'react'

const SERVER = 'http://localhost:8000'

const STATUS_DETAILS = {
    PENDING: {color: '#9C27B0', emoji: '⏳'},
    RUNNING: {color: '#3F51B5', emoji: '🏃'},
    SUCCESS: {color: '#2E7D32', emoji: '✅'},
    FAILURE: {color: '#D32F2F', emoji: '❌'},
    EXPIRED: {color: '#616161', emoji: '⌛'},
    ERROR: {color: '#B71C1C', emoji: '⚠️'}
}

function Chip({children, color, onClick, expanded}) {
    return (
        <div
            onClick={onClick}
            style={{
                cursor: onClick ? 'pointer' : 'default',
                backgroundColor: color,
                color: '#fff',
                padding: '6px 12px',
                borderRadius: 16,
                margin: 4,
                fontFamily: "'JetBrains Mono', monospace",
                userSelect: 'none',
                boxShadow: expanded ? `0 0 10px ${color}` : 'none',
                transition: 'box-shadow 0.2s',
                maxWidth: 320,
                overflowWrap: 'break-word',
            }}
        >
            {children}
        </div>
    )
}

export default function App() {
    const [input, setInput] = useState('')
    const [tasks, setTasks] = useState([])
    const [expandedId, setExpandedId] = useState(null)
    const intervalRef = useRef(null)

    const handleSubmit = async () => {
        const videoIds = input
            .split('\n')
            .map((id) => id.trim())
            .filter(Boolean)

        const newTasks = []

        for (const videoId of videoIds) {
            try {
                const res = await fetch(`${SERVER}/api/submit/${videoId}`, {method: 'POST'})
                if (!res.ok) throw new Error(`Erro ${res.status}`)

                const data = await res.json()
                if (!data?.task_id) throw new Error('Resposta inválida da API')

                newTasks.push({
                    videoId: data.video_id,
                    taskId: data.task_id,
                    status: data.status,
                    error: null,
                })
            } catch (e) {
                newTasks.push({
                    videoId,
                    taskId: null,
                    status: 'ERROR',
                    error: e.message || 'Falha ao enviar para API',
                })
            }
        }

        setTasks(newTasks)
        setInput('')
    }

    useEffect(() => {
        if (tasks.length === 0 || intervalRef.current) return

        intervalRef.current = setInterval(async () => {
            const updatedTasks = await Promise.all(
                tasks.map(async (task) => {
                    if (!task.taskId || ['SUCCESS', 'FAILURE', 'EXPIRED', 'ERROR'].includes(task.status))
                        return task

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

                        return {...task, status: data.status, error: data.error || null}
                    } catch (err) {
                        return {...task, error: err.message || 'Erro ao verificar status'}
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

    // Handle input by turning each ID into a chip on Enter or comma
    const [inputBuffer, setInputBuffer] = useState('')
    const [chips, setChips] = useState([])

    const addChip = (value) => {
        const v = value.trim()
        if (v && !chips.includes(v)) {
            setChips([...chips, v])
        }
    }

    const removeChip = (value) => {
        setChips(chips.filter((c) => c !== value))
    }

    const onInputKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            if (inputBuffer.trim()) addChip(inputBuffer)
            setInputBuffer('')
        }
        if (e.key === 'Backspace' && !inputBuffer) {
            setChips(chips.slice(0, -1))
        }
    }

    useEffect(() => {
        setInput(chips.join('\n'))
    }, [chips])

    return (
        <>
            <style>{`
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');

          * {
            box-sizing: border-box;
          }
          body,html,#root {
            margin:0; padding:0; height:100%;
            background: #121212;
            color: #E0E0E0;
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 24px;
          }
          #app {
            width: 100%;
            max-width: 900px;
            height: 100%;
            display: flex;
            flex-direction: column;
            background: #1E1E2F;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 0 30px #4A148C;
          }
          h2 {
            margin: 0 0 16px 0;
            font-weight: 700;
            font-size: 1.8rem;
            color: #9C27B0;
            user-select: none;
          }
          h3 {
            color: #9C27B0;
            margin-bottom: 12px;
            user-select: none;
          }
          label {
            font-weight: 600;
            color: #B39DDB;
            margin-bottom: 8px;
            user-select: none;
          }
          .input-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            background: #2C2C3E;
            border-radius: 12px;
            padding: 8px 12px;
            min-height: 50px;
            max-height: 150px;
            overflow-y: auto;
            border: 1.5px solid #9C27B0;
          }
          .input-container:focus-within {
            border-color: #CE93D8;
            box-shadow: 0 0 8px #CE93D8;
          }
          .input-buffer {
            flex-grow: 1;
            border: none;
            background: transparent;
            color: #E0E0E0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1rem;
            outline: none;
            min-width: 60px;
          }
          button {
            margin-top: 16px;
            padding: 12px 24px;
            background: #9C27B0;
            border: none;
            border-radius: 16px;
            color: white;
            font-weight: 700;
            cursor: pointer;
            transition: background-color 0.2s;
            user-select: none;
            font-family: 'JetBrains Mono', monospace;
          }
          button:hover {
            background: #BA68C8;
          }
          button:active {
            background: #7B1FA2;
          }
          .tasks-list {
            margin-top: 32px;
            overflow-y: auto;
            flex-grow: 1;
          }
          .task-chip {
            user-select: none;
          }
          .error-text {
            color: #EF5350;
            font-size: 0.85rem;
            margin-top: 4px;
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', monospace;
          }
        `}</style>
            <div id="app" role="main">
                <h2>Separador de Áudio do YouTube</h2>

                <label htmlFor="id-input">IDs do YouTube (digite e pressione Enter):</label>
                <div className="input-container" onClick={() => document.getElementById('id-input').focus()}>
                    {chips.map((chip) => (
                        <Chip key={chip} color="#9C27B0" onClick={() => removeChip(chip)}>
                            {chip} &times;
                        </Chip>
                    ))}
                    <input
                        id="id-input"
                        className="input-buffer"
                        value={inputBuffer}
                        onChange={(e) => setInputBuffer(e.target.value)}
                        onKeyDown={onInputKeyDown}
                        placeholder="Cole ou digite um ID"
                        spellCheck={false}
                        autoComplete="off"
                        autoCorrect="off"
                        autoCapitalize="none"
                    />
                </div>

                <button onClick={handleSubmit} disabled={chips.length === 0}>
                    Enviar IDs
                </button>

                <div className="tasks-list" aria-live="polite" aria-label="Status dos vídeos">
                    {tasks.length > 0 && (
                        <>
                            <h3>Progresso</h3>
                            {tasks.map((task) => {
                                const isExpanded = expandedId === task.videoId
                                const {color, emoji} = STATUS_DETAILS[task.status] || {color: '#666', emoji: ''}

                                return (
                                    <div key={task.videoId} style={{marginBottom: 12}}>
                                        <Chip
                                            className="task-chip"
                                            color={color}
                                            onClick={() => setExpandedId(isExpanded ? null : task.videoId)}
                                            expanded={isExpanded}
                                        >
                                            {task.videoId} → {emoji} {task.status}
                                        </Chip>
                                        {isExpanded && task.error && (
                                            <div className="error-text" role="alert">
                                                Erro: {task.error}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </>
                    )}
                </div>

                <footer
                    style={{
                        textAlign: 'center',
                        color: '#9C27B0',
                        fontSize: 12,
                        padding: '12px 0',
                        userSelect: 'none',
                        fontFamily: "'JetBrains Mono', monospace",
                    }}
                >
                    © Francisco Lucas, 2025
                </footer>
            </div>
        </>
    )
}
