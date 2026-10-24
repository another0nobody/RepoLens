<script setup>
defineProps({
  size: { type: Number, default: 40 },
});
</script>

<template>
  <span class="brand-mark" :style="{ width: `${size}px`, height: `${size}px` }" aria-hidden="true">
    <svg viewBox="0 0 32 32" fill="none" class="mark">
      <path d="M5 8.5 16 3l11 5.5v15L16 29 5 23.5v-15Z" stroke="currentColor" stroke-width="1.6" />
      <path d="M5 8.5 16 14l11-5.5M16 14v15" stroke="currentColor" stroke-width="1.2" opacity=".65" />
      <circle cx="16" cy="14" r="2.6" fill="currentColor" />
    </svg>
  </span>
</template>

<style scoped lang="less">
.brand-mark {
  display: grid;
  place-items: center;
  border-radius: 13px;
  color: var(--accent);
  background: linear-gradient(145deg, var(--accent-soft), color-mix(in srgb, var(--accent-2) 14%, transparent));
  border: 1px solid var(--accent-line);
  box-shadow: 0 0 32px -8px var(--accent);
  flex: none;
}

.mark {
  width: 64%;
  height: 64%;
}
</style>
