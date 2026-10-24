<script setup>
import Icon from "./Icon.vue";

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: "" },
  subtitle: { type: String, default: "" },
  wide: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div v-if="open" class="overlay" @mousedown.self="emit('close')">
        <aside class="drawer" :class="{ wide }" role="dialog" aria-modal="true" :aria-label="title">
          <header class="drawer-head">
            <div class="head-copy">
              <slot name="eyebrow" />
              <h2>{{ title }}</h2>
              <p v-if="subtitle">{{ subtitle }}</p>
            </div>
            <button class="icon-btn" type="button" aria-label="关闭" @click="emit('close')">
              <Icon name="close" :size="17" />
            </button>
          </header>
          <div class="drawer-body">
            <slot />
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="less">
.overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  justify-content: flex-end;
  background: var(--overlay);
  .glass();
}

.drawer {
  width: 540px;
  max-width: 94vw;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--drawer-bg);
  border-left: 1px solid var(--line);
  box-shadow: var(--shadow);
  animation: drawer-in 0.28s @ease-out;

  &.wide {
    width: 780px;
  }
}

@keyframes drawer-in {
  from {
    transform: translateX(36px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}

.head-copy {
  min-width: 0;

  h2 {
    margin: 6px 0 4px;
    font-size: 22px;
    letter-spacing: -0.4px;
  }

  p {
    margin: 0;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.7;
  }
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px 2px 28px;
  .scrollbar();
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.24s @ease-out;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

@media (max-width: @bp-sm) {
  .drawer {
    width: 100%;
    max-width: 100vw;
    padding: 18px;
  }
}
</style>
