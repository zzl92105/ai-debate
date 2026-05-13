export type DebateStyle = 'serious' | 'academic' | 'sharp' | 'humorous'
export type DebateRole = 'affirmative' | 'negative'
export type Winner = DebateRole | 'draw'

export interface DebateRequest {
  topic: string
  rounds: number
  style: DebateStyle
}

export interface DebateMessage {
  role: DebateRole
  round: number
  phase: string
  content: string
}

export interface JudgeResult {
  winner: Winner
  score: {
    affirmative: number
    negative: number
  }
  reason: string
  best_argument: string
  logic_flaws: string[]
}

export interface DebateResponse {
  topic: string
  style: DebateStyle
  rounds: number
  messages: DebateMessage[]
  judge: JudgeResult
  model: string
  mock: boolean
}

export async function runDebate(payload: DebateRequest): Promise<DebateResponse> {
  const response = await fetch('/api/debate/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  return response.json()
}

