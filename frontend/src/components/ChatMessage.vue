<script setup>
defineProps({
  role: { type: String, required: true },
  text: { type: String, required: true },
})
</script>

<template>
  <div class="message" :class="role">
    <div class="bubble">
      <p class="text">{{ text }}</p>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  width: 100%;
  animation: fade-in 0.25s ease;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 78%;
  padding: 0.7rem 1rem;
  border-radius: 16px;
  line-height: 1.5;
  font-size: 0.95rem;
}

.message.user .bubble {
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  color: #0f172a;
  border-bottom-right-radius: 4px;
  font-weight: 500;
}

.message.assistant .bubble {
  background: rgba(30, 41, 59, 0.9);
  color: #e2e8f0;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-bottom-left-radius: 4px;
}

.text { margin: 0; }

@keyframes fade-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 600px) {
  .bubble { max-width: 88%; font-size: 0.9rem; }
}
</style>
