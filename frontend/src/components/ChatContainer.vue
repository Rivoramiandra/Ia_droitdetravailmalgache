<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'  // Ajout de watch
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import Loader from './Loader.vue'
import { askQuestion } from '../services/api.js'

// Ajout d'une prop pour recevoir l'ID de conversation
const props = defineProps({
    conversationId: {
        type: [String, Number],
        default: null
    }
})

const messages = ref([
  {
    role: 'assistant',
    text: "Bonjour ! Je suis votre assistant IA. Posez-moi une question pour commencer.",
  },
])

const loading = ref(false)
const scrollEl = ref(null)

// Surveiller les changements de conversationId pour réinitialiser
watch(() => props.conversationId, (newId, oldId) => {
    if (newId !== oldId) {
        // Réinitialiser les messages
        messages.value = [
            {
                role: 'assistant',
                text: "Bonjour ! Je suis votre assistant IA. Posez-moi une question pour commencer.",
            },
        ]
        // Scroller en haut
        nextTick(() => {
            if (scrollEl.value) scrollEl.value.scrollTop = 0
        })
    }
})

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}

async function send(question) {
  if (!question.trim() || loading.value) return

  messages.value.push({ role: 'user', text: question })
  loading.value = true
  await scrollToBottom()

  try {
    const answer = await askQuestion(question)
    messages.value.push({ role: 'assistant', text: answer })
  } catch {
    messages.value.push({
      role: 'assistant',
      text: "Désolé, une erreur est survenue. Réessayez plus tard.",
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

onMounted(scrollToBottom)
</script>

<template>
  <div class="chat-container">
    <div ref="scrollEl" class="messages">
      <ChatMessage
        v-for="(m, i) in messages"
        :key="i"
        :role="m.role"
        :text="m.text"
      />
      <Loader v-if="loading" />
    </div>

    <ChatInput :disabled="loading" @send="send" />
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  min-height: 480px;
  max-width: 95%;
  margin: 0 auto;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 18px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  scroll-behavior: smooth;
}

@media (max-width: 600px) {
  .chat-container { height: 78vh; border-radius: 14px; }
  .messages { padding: 0.9rem; }
}
</style>