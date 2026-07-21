<template>
  <div class="loader-wrap">
    <div class="dots">
      <span></span><span></span><span></span>
    </div>
    <span class="label">L'IA réfléchit…</span>
  </div>
</template>

<style scoped>
.loader-wrap {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.2rem;
}

.dots {
  display: inline-flex;
  gap: 0.3rem;
}

.dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  animation: bounce 1.2s infinite ease-in-out;
}

.dots span:nth-child(2) { animation-delay: 0.15s; }
.dots span:nth-child(3) { animation-delay: 0.3s; }

.label {
  font-size: 0.85rem;
  color: #94a3b8;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
