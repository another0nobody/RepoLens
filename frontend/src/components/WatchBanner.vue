<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { fetchWatch } from "../api";
import { startAnalysis } from "../store";

const props = defineProps({
  report: { type: Object, default: null },
});

const enabled = ref(false);
const loading = ref(false);
const data = ref(null);
const error = ref("");
let timer = null;

const changed = computed(() => Boolean(data.value?.changed));
const available = computed(() => data.value?.available !== false);
const lastChecked = computed(() => {
  if (!data.value?.checked_at) return "";
  return new Date(data.value.checked_at * 1000).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
});

async function check() {
  if (!props.report?.run_id || !props.report?.local_path) return;
  loading.value = true;
  try {
    data.value = await fetchWatch(props.report.run_id);
    error.value = "";
    if (!data.value.available) stop();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function start() {
  if (!props.report?.local_path) return;
  enabled.value = true;
  check();
  timer = window.setInterval(check, 15000);
}

function stop() {
  enabled.value = false;
  if (timer) {
    window.clearInterval(timer);
    timer = null;
  }
}

function toggle() {
  if (enabled.value) stop();
  else start();
}

function reanalyze() {
  if (props.report?.source) startAnalysis(props.report.source);
}

watch(
  () => props.report?.run_id,
  () => {
    stop();
    data.value = null;
    error.value = "";
  }
);

onBeforeUnmount(stop);
</script>

<template>
  <section v-if="report?.source_type === 'local'" class="watch-bar" :class="{ changed }">
    <div class="watch-copy">
      <i class="dot" :class="{ on: enabled, changed }"></i>
      <div>
        <b>{{ changed ? "检测到仓库变化" : "监听本地仓库变化" }}</b>
        <span v-if="changed">
          {{ data?.latest_path || "文件已更新" }}；建议重新分析后再对比报告。
        </span>
        <span v-else-if="enabled">
          每 15 秒检查一次<template v-if="lastChecked"> · 上次 {{ lastChecked }}</template>
        </span>
        <span v-else-if="error">监听失败：{{ error }}</span>
        <span v-else>分析完成后，可以持续观察文件是否又有改动。</span>
      </div>
    </div>
    <div class="watch-actions">
      <button v-if="changed" class="watch-primary" type="button" @click="reanalyze">
        重新分析
      </button>
      <button class="watch-toggle" type="button" :disabled="loading || (!available && enabled)" @click="toggle">
        {{ enabled ? "停止监听" : "开始监听" }}
      </button>
    </div>
  </section>
</template>

<style scoped lang="less">
.watch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 12px;
  padding: 9px 11px;
  border: 1px solid var(--line);
  background: var(--panel);

  &.changed {
    border-color: var(--warn);
    background: var(--warn-soft);
  }
}

.watch-copy {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;

  .dot {
    width: 6px;
    height: 6px;
    margin-top: 4px;
    flex: none;
    background: var(--faint);

    &.on {
      background: var(--good);
    }

    &.changed {
      background: var(--warn);
    }
  }

  b {
    display: block;
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 10.5px;
    font-weight: 500;
  }

  span {
    display: block;
    margin-top: 2px;
    color: var(--faint);
    font-size: 9px;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
}

.watch-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: none;
}

.watch-primary,
.watch-toggle {
  padding: 5px 8px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 9px;
  cursor: pointer;

  &:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  &:disabled {
    opacity: 0.45;
    cursor: wait;
  }
}

.watch-primary {
  border-color: var(--warn);
  color: var(--warn);
}

@media (max-width: 720px) {
  .watch-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .watch-actions {
    width: 100%;
  }

  .watch-actions button {
    flex: 1;
  }
}
</style>
