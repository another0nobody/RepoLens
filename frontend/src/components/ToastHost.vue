<script setup>
import { dismissToast, state } from "../store";
import Icon from "./Icon.vue";

const iconFor = (kind) => (kind === "error" ? "warning" : kind === "warn" ? "warning" : kind === "ok" ? "check" : "spark");
</script>

<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toasts" aria-live="polite">
      <div v-for="item in state.toasts" :key="item.id" class="toast" :class="item.kind" role="status">
        <Icon :name="iconFor(item.kind)" :size="16" class="toast-icon" />
        <span class="toast-text">{{ item.message }}</span>
        <button class="toast-close" type="button" aria-label="关闭提示" @click="dismissToast(item.id)">
          <Icon name="close" :size="13" />
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<style scoped lang="less">
.toasts {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 120;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: min(420px, calc(100vw - 40px));
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding: 12px 13px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--toast-bg);
  box-shadow: var(--shadow);
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
  pointer-events: auto;

  &.ok {
    border-color: color-mix(in srgb, var(--good) 34%, transparent);
    color: var(--good);
  }

  &.warn {
    border-color: color-mix(in srgb, var(--warn) 34%, transparent);
    color: var(--warn);
  }

  &.error {
    border-color: color-mix(in srgb, var(--bad) 36%, transparent);
    color: var(--bad);
  }
}

.toast-icon {
  margin-top: 2px;
}

.toast-text {
  flex: 1;
  color: var(--text);
}

.toast-close {
  border: 0;
  background: none;
  color: var(--faint);
  padding: 2px;
  border-radius: 5px;

  &:hover {
    color: var(--text);
    background: var(--panel-soft);
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.22s @ease-out, transform 0.22s @ease-out;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.toast-move {
  transition: transform 0.22s @ease-out;
}
</style>
