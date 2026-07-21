<script setup>
import { ref } from 'vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['send'])

const text = ref('')

function submit() {
  const value = text.value.trim()
  if (!value) return
  emit('send', value)
  text.value = ''
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}
</script>

<template>
  <form class="chat-input" @submit.prevent="submit">
    <textarea
      v-model="text"
      class="field"
      placeholder="Écrivez votre question…"
      rows="1"
      :disabled="disabled"
      @keydown="onKeydown"
    />
    <button type="submit" class="send-btn" :disabled="disabled || !text.trim()">
      Envoyer
    </button>
  </form>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  background: rgba(15, 23, 42, 0.7);
}

.field {
  flex: 1;
  resize: none;
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(2, 6, 23, 0.6);
  color: #f1f5f9;
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.4;
  transition: border-color 0.2s;
}

.field:focus {
  outline: none;
  border-color: #38bdf8;
}

.field::placeholder { color: #64748b; }

.send-btn {
  padding: 0.7rem 1.2rem;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  color: #0f172a;
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition: transform 0.15s, opacity 0.2s;
}

.send-btn:hover:not(:disabled) { transform: translateY(-1px); }
.send-btn:disabled { opacity: 0.45; cursor: not-allowed; }

@media (max-width: 600px) {
  .chat-input { padding: 0.7rem 0.8rem; gap: 0.45rem; }
  .send-btn { padding: 0.7rem 0.9rem; font-size: 0.85rem; }
}
</style>
