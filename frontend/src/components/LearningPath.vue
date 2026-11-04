<script setup>
import { computed, ref, watch } from "vue";

import Icon from "./Icon.vue";
import { openCode } from "../store";

const props = defineProps({
  report: { type: Object, default: null },
});

const PATH_RE = /([A-Za-z0-9_@./-]+\.(?:py|pyi|ts|tsx|js|jsx|vue|svelte|go|java|kt|rs|rb|php|cs|c|cc|cpp|h|hpp|md|json|ya?ml|toml|txt))/;
const done = ref(new Set());

const storageKey = computed(() => `repolens-learning:${props.report?.run_id || "unknown"}`);

const steps = computed(() =>
  (props.report?.learning_path || []).map((raw, index) => {
    const text = String(raw || "").replace(/^\s*\d+[.、)]\s*/, "").trim();
    const match = text.match(PATH_RE);
    return {
      index,
      text,
      path: match ? match[1] : "",
    };
  })
);

const progress = computed(() => {
  if (!steps.value.length) return 0;
  return Math.round((steps.value.filter((step) => done.value.has(step.index)).length / steps.value.length) * 100);
});

const completed = computed(() => steps.value.filter((step) => done.value.has(step.index)).length);

function loadDone() {
  done.value = new Set();
  if (!props.report?.run_id) return;
  try {
    const raw = localStorage.getItem(storageKey.value);
    const parsed = raw ? JSON.parse(raw) : [];
    if (Array.isArray(parsed)) done.value = new Set(parsed.filter((item) => Number.isInteger(item)));
  } catch {
    done.value = new Set();
  }
}

function saveDone() {
  try {
    localStorage.setItem(storageKey.value, JSON.stringify([...done.value]));
  } catch {
    // 隐私模式下 localStorage 可能不可用；不阻塞阅读。
  }
}

function toggle(index) {
  const next = new Set(done.value);
  if (next.has(index)) next.delete(index);
  else next.add(index);
  done.value = next;
  saveDone();
}

function reset() {
  done.value = new Set();
  saveDone();
}

watch(
  () => props.report?.run_id,
  () => loadDone(),
  { immediate: true }
);
</script>

<template>
  <div class="learning-path">
    <div class="learn-head">
      <div>
        <p class="eyebrow mono">LEARNING PATH / 学习路线</p>
        <h2>前 30 分钟怎么读</h2>
        <p class="learn-note">
          每一步都可以勾选；进度只保存在当前浏览器，按报告 ID 区分。
        </p>
      </div>
      <div class="learn-progress">
        <span class="progress-number mono">{{ progress }}%</span>
        <span class="progress-text">{{ completed }} / {{ steps.length }} 步</span>
        <span class="progress-track"><i :style="{ width: `${progress}%` }"></i></span>
      </div>
    </div>

    <div v-if="!steps.length" class="empty-state">
      这份报告没有学习路线。先打开模块地图，从入口文件开始读。
    </div>

    <template v-else>
      <div class="learn-toolbar">
        <span class="mono">{{ completed === steps.length ? "路线已完成" : "勾选完成的步骤" }}</span>
        <button class="btn" type="button" :disabled="!completed" @click="reset">
          <Icon name="refresh" :size="14" /> 重置进度
        </button>
      </div>

      <ol class="learn-list">
        <li
          v-for="step in steps"
          :key="step.index"
          class="learn-step"
          :class="{ done: done.has(step.index) }"
        >
          <label class="step-check">
            <input
              type="checkbox"
              :checked="done.has(step.index)"
              :aria-label="`标记第 ${step.index + 1} 步完成`"
              @change="toggle(step.index)"
            />
            <span class="step-index mono">{{ String(step.index + 1).padStart(2, "0") }}</span>
          </label>
          <div class="step-body">
            <p>{{ step.text }}</p>
            <button
              v-if="step.path"
              type="button"
              class="step-path mono"
              @click="openCode(step.path, 1)"
            >
              <Icon name="code" :size="12" /> {{ step.path }}
            </button>
          </div>
          <span v-if="done.has(step.index)" class="step-done mono">DONE</span>
        </li>
      </ol>

      <p class="learn-foot">
        <Icon name="book" :size="12" />
        路线来自报告的 learning_path；代码入口只打开扫描到的文件片段。
      </p>
    </template>
  </div>
</template>

<style scoped lang="less">
.learn-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-strong);

  h2 {
    margin: 4px 0 4px;
    font-family: var(--font-display);
    font-size: 24px;
    font-weight: 500;
  }
}

.learn-note {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.learn-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  min-width: 96px;

  .progress-number {
    color: var(--accent);
    font-size: 26px;
    line-height: 1;
  }

  .progress-text {
    color: var(--faint);
    font-size: 9px;
  }

  .progress-track {
    width: 100%;
    height: 2px;
    margin-top: 5px;
    background: var(--line);
    overflow: hidden;

    i {
      display: block;
      height: 100%;
      background: var(--accent);
      transition: width 0.2s;
    }
  }
}

.learn-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 0 8px;
  color: var(--faint);
  font-size: 8px;
}

.learn-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}

.learn-step {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  padding: 13px 0;
  border-bottom: 1px solid var(--line);

  &.done {
    .step-body p {
      color: var(--faint);
      text-decoration: line-through;
    }
  }
}

.step-check {
  display: flex;
  align-items: center;
  gap: 7px;
  flex: none;
  cursor: pointer;

  input {
    width: 14px;
    height: 14px;
    margin: 0;
    accent-color: var(--accent);
    cursor: pointer;
  }
}

.step-index {
  color: var(--faint);
  font-size: 9px;
}

.step-body {
  min-width: 0;
  flex: 1;

  p {
    margin: 0;
    color: var(--text);
    font-size: 12px;
    line-height: 1.65;
  }
}

.step-path {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  margin-top: 6px;
  padding: 3px 6px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--accent);
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  cursor: pointer;

  &:hover {
    border-color: var(--accent);
    background: var(--accent-soft);
  }
}

.step-done {
  flex: none;
  color: var(--good);
  font-size: 8px;
}

.learn-foot {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 12px 0 0;
  color: var(--faint);
  font-size: 9.5px;
  line-height: 1.5;
}

@media (max-width: 720px) {
  .learn-head {
    display: block;
  }

  .learn-progress {
    align-items: flex-start;
    margin-top: 10px;
  }

  .learn-step {
    gap: 8px;
  }
}
</style>
