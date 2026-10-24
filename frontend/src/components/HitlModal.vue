<script setup>
import { computed } from "vue";

import { fmtDuration } from "../utils";
import { state, submitHitl } from "../store";
import Icon from "./Icon.vue";

const action = computed(() => state.hitl?.first || null);
const target = computed(() => {
  const args = action.value?.args || {};
  return args.url || args.path || (Object.keys(args).length ? JSON.stringify(args) : "");
});
const percent = computed(() => {
  const total = Number(state.hitl?.timeout || 300) || 1;
  return Math.min(100, Math.max(0, (state.hitlRemaining / total) * 100));
});
const pending = computed(() => Boolean(state.hitlPending));
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="state.hitl" class="modal-wrap" @mousedown.self.prevent>
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="hitl-title">
          <div class="modal-top">
            <div class="alert-icon">
              <Icon name="warning" :size="20" />
            </div>
            <div class="countdown-ring" :style="{ '--p': `${percent * 3.6}deg` }">
              <span>{{ fmtDuration(state.hitlRemaining) }}</span>
            </div>
          </div>

          <h2 id="hitl-title">Agent 需要你的批准</h2>
          <p class="desc">
            {{ action?.description || "Agent 想要执行一个会联网或写磁盘的操作，是否允许？" }}
          </p>
          <div v-if="target" class="target">
            <span class="target-label">目标</span>
            <code>{{ target }}</code>
          </div>
          <p class="hint">等待超时会自动拒绝。批准后 Agent 会从断点继续执行。</p>

          <div class="modal-actions">
            <button class="btn" type="button" :disabled="pending" @click="submitHitl('reject')">
              {{ state.hitlPending === "reject" ? "正在拒绝…" : "拒绝" }}
            </button>
            <button
              class="btn btn-primary"
              type="button"
              :disabled="pending"
              @click="submitHitl('approve')"
            >
              {{ state.hitlPending === "approve" ? "正在继续…" : "允许克隆并继续" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="less">
.modal-wrap {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: var(--overlay);
  .glass();
}

.modal {
  width: 560px;
  max-width: 100%;
  padding: 26px;
  border-radius: @radius-xl;
  border: 1px solid color-mix(in srgb, var(--warn) 32%, transparent);
  background: var(--panel-solid);
  box-shadow: var(--shadow);
}

.modal-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.alert-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: var(--warn);
  background: var(--warn-soft);
  border: 1px solid color-mix(in srgb, var(--warn) 30%, transparent);
}

.countdown-ring {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, var(--panel-solid) 57%, transparent 58%),
    conic-gradient(var(--warn) var(--p), var(--panel-soft) 0);
  font-family: @font-mono;
  font-size: 10px;
  color: var(--warn);
}

h2 {
  margin: 16px 0 8px;
  font-size: 21px;
  letter-spacing: -0.3px;
}

.desc {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 13.5px;
  line-height: 1.75;
}

.target {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: @radius-sm;
  border: 1px solid var(--line);
  background: var(--code-bg);
  .mono();
  font-size: 11.5px;
  word-break: break-all;

  .target-label {
    flex: none;
    color: var(--faint);
    font-family: @font-sans;
    font-size: 11px;
  }

  code {
    color: var(--accent);
  }
}

.hint {
  margin: 12px 0 0;
  color: var(--faint);
  font-size: 11.5px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  margin-top: 22px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s @ease-out;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.24s @ease-out, opacity 0.24s @ease-out;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}
</style>
