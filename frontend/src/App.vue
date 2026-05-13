<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { runDebate, type DebateMessage, type DebateResponse, type DebateStyle } from './api'

interface DebateSession {
  id: string
  title: string
  createdAt: string
  debate: DebateResponse
}

const styleOptions: Array<{ value: DebateStyle; label: string }> = [
  { value: 'serious', label: '严肃' },
  { value: 'academic', label: '学术' },
  { value: 'sharp', label: '犀利' },
  { value: 'humorous', label: '幽默' }
]

const topic = ref('AI 是否会取代程序员？')
const rounds = ref(3)
const style = ref<DebateStyle>('serious')
const loading = ref(false)
const error = ref('')
const sessions = ref<DebateSession[]>(loadSessions())
const activeSessionId = ref(sessions.value[0]?.id ?? '')

const activeSession = computed(() => {
  return sessions.value.find((session) => session.id === activeSessionId.value) ?? sessions.value[0] ?? null
})

const activeDebate = computed(() => activeSession.value?.debate ?? null)
const conversationMessages = computed(() => activeDebate.value?.messages ?? [])

const winnerLabel = computed(() => {
  if (!activeDebate.value) return ''
  const winner = activeDebate.value.judge.winner
  if (winner === 'affirmative') return '正方胜'
  if (winner === 'negative') return '反方胜'
  return '平局'
})

function getMessageKey(message: DebateMessage) {
  return `${message.role}-${message.round}`
}

function getRoleLabel(role: DebateMessage['role']) {
  return role === 'affirmative' ? '正方' : '反方'
}

function getSessionTime(session: DebateSession) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(session.createdAt))
}

function getSessionPreview(session: DebateSession) {
  const lastMessage = session.debate.messages[session.debate.messages.length - 1]
  return session.debate.judge.reason || lastMessage?.content || '暂无内容'
}

function loadSessions(): DebateSession[] {
  const stored = localStorage.getItem('ai-debate-sessions')
  if (!stored) return []

  try {
    const parsed = JSON.parse(stored)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

async function startDebate() {
  error.value = ''
  const cleanTopic = topic.value.trim()
  if (cleanTopic.length < 2) {
    error.value = '请输入至少 2 个字符的辩题。'
    return
  }

  loading.value = true
  try {
    const debate = await runDebate({
      topic: cleanTopic,
      rounds: rounds.value,
      style: style.value
    })
    const session: DebateSession = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title: cleanTopic,
      createdAt: new Date().toISOString(),
      debate
    }
    sessions.value = [session, ...sessions.value]
    activeSessionId.value = session.id
  } catch (err) {
    error.value = err instanceof Error ? err.message : '生成辩论失败'
  } finally {
    loading.value = false
  }
}

watch(
  sessions,
  (value) => {
    localStorage.setItem('ai-debate-sessions', JSON.stringify(value.slice(0, 30)))
  },
  { deep: true }
)
</script>

<template>
  <main class="app-shell">
    <div class="ambient-grid" aria-hidden="true"></div>

    <section class="control-panel">
      <div class="brand">
        <div>
          <p class="eyebrow">AI Debate Studio</p>
          <h1>AI 辩论场</h1>
        </div>
        <div class="system-status" aria-label="系统状态">
          <span></span>
          Online
        </div>
      </div>

      <div class="form-grid">
        <label class="field topic-field">
          <span>辩题</span>
          <input v-model="topic" :disabled="loading" placeholder="输入一个值得争论的问题" />
        </label>

        <label class="field">
          <span>轮数</span>
          <select v-model.number="rounds" :disabled="loading">
            <option :value="1">1 轮</option>
            <option :value="2">2 轮</option>
            <option :value="3">3 轮</option>
            <option :value="4">4 轮</option>
            <option :value="5">5 轮</option>
          </select>
        </label>

        <label class="field">
          <span>风格</span>
          <select v-model="style" :disabled="loading">
            <option v-for="option in styleOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <button class="primary-button" :disabled="loading" @click="startDebate">
          <span>{{ loading ? '生成中...' : '开始辩论' }}</span>
        </button>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section v-if="activeDebate" class="meta-bar">
      <span>{{ activeDebate.topic }}</span>
      <span>{{ activeDebate.rounds }} 轮</span>
      <span>{{ activeDebate.model }}</span>
      <span v-if="activeDebate.mock">模拟数据</span>
    </section>

    <section class="workspace-panel">
      <aside class="conversation-sidebar">
        <div class="panel-heading">
          <p>Debates</p>
          <h2>辩论记录</h2>
        </div>

        <div v-if="sessions.length" class="conversation-list">
          <button
            v-for="session in sessions"
            :key="session.id"
            class="conversation-item"
            :class="{ active: session.id === activeSession?.id }"
            @click="activeSessionId = session.id"
          >
            <span class="session-avatar">辩</span>
            <span class="item-main">
              <strong>{{ session.title }}</strong>
              <small>{{ getSessionPreview(session) }}</small>
            </span>
            <time>{{ getSessionTime(session) }}</time>
          </button>
        </div>

        <div v-else class="conversation-list skeleton-list" aria-hidden="true">
          <div class="conversation-item placeholder">
            <span class="session-avatar">辩</span>
            <span class="item-main">
              <strong>新的辩论会显示在这里</strong>
              <small>像微信会话一样保存历史记录</small>
            </span>
            <time>现在</time>
          </div>
        </div>
      </aside>

      <article class="chat-panel">
        <template v-if="activeDebate">
          <header>
            <div>
              <span>{{ activeDebate.rounds }} 轮 · {{ styleOptions.find((item) => item.value === activeDebate?.style)?.label }}</span>
              <h2>{{ activeDebate.topic }}</h2>
            </div>
          </header>

          <div class="chat-thread">
            <div
              v-for="message in conversationMessages"
              :key="getMessageKey(message)"
              class="chat-row"
              :class="message.role"
            >
              <div class="chat-avatar">{{ message.role === 'affirmative' ? '正' : '反' }}</div>
              <div class="chat-bubble">
                <div class="speech-meta">
                  <span>{{ getRoleLabel(message.role) }}</span>
                  <small>第 {{ message.round }} 轮 · {{ message.phase }}</small>
                </div>
                <p>{{ message.content }}</p>
              </div>
            </div>

            <div class="judge-message">
              <div class="chat-avatar judge-avatar">裁</div>
              <div class="chat-bubble judge-bubble">
                <div class="speech-meta">
                  <span>裁判结果 · {{ winnerLabel }}</span>
                  <small>正方 {{ activeDebate.judge.score.affirmative }} : {{ activeDebate.judge.score.negative }} 反方</small>
                </div>
                <p>{{ activeDebate.judge.reason }}</p>
                <div class="judge-mini">
                  <strong>最佳论点</strong>
                  <p>{{ activeDebate.judge.best_argument }}</p>
                  <strong>逻辑漏洞</strong>
                  <ul>
                    <li v-for="flaw in activeDebate.judge.logic_flaws" :key="flaw">{{ flaw }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="empty-detail">
          <span></span>
          <h2>等待一场新辩论</h2>
          <p>输入辩题并开始后，左侧会保存每一场辩论记录，右侧展示选中记录的完整对话内容。</p>
        </div>
      </article>
    </section>
  </main>
</template>
