<script setup>
import { computed, nextTick, ref, watch } from "vue";

import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { closeCode, copy, state } from "../store";

const codeBody = ref(null);
const viewer = computed(() => state.codeViewer);
const data = computed(() => viewer.value.data);
const codeText = computed(() => (data.value?.lines || []).map((line) => line.text).join("\n"));

watch(
  () => data.value,
  async () => {
    await nextTick();
    codeBody.value?.querySelector(".code-line.highlight")?.scrollIntoView({ block: "center" });
  }
);

function copyLocation() {
  copy(`${viewer.value.path}:${viewer.value.line}`, "位置");
}

function copyCode() {
  copy(codeText.value, "代码片段");
}
</script>

<template>
  <BaseDrawer
    :open="viewer.open"
    :title="viewer.path || '代码片段'"
    :subtitle="data ? `${data.language || '文本'} · 第 ${data.start}–${data.end} 行 · 共 ${data.total_lines} 行` : '只读 · 自动脱敏'"
    wide
    @close="closeCode"
  >
    <template #eyebrow>
      <span class="tag mono">EVIDENCE VIEWER / 证据</span>
    </template>

    <div class="code-head">
      <div class="code-meta">
        <span class="mono">LINE {{ viewer.line }}</span>
        <span v-if="data?.masked" class="mask-note">已隐藏疑似密钥</span>
        <span v-if="data?.truncated" class="mask-note">片段已截断</span>
      </div>
      <div class="code-actions">
        <button class="btn" type="button" @click="copyLocation">复制位置</button>
        <button class="btn" type="button" :disabled="!data" @click="copyCode">复制片段</button>
      </div>
    </div>

    <div v-if="viewer.loading" class="code-loading">
      <span class="spinner"></span> 正在读取文件…
    </div>
    <div v-else-if="viewer.error" class="empty-state">{{ viewer.error }}</div>

    <div v-else-if="data" ref="codeBody" class="code-window">
      <div
        v-for="line in data.lines"
        :key="line.number"
        class="code-line"
        :class="{ highlight: line.highlight }"
      >
        <span class="code-number mono">{{ line.number }}</span>
        <code>{{ line.text || " " }}</code>
      </div>
    </div>

    <p v-if="data?.truncated" class="code-foot">
      只展示证据行附近的片段；完整文件请在本地编辑器中打开。
    </p>
  </BaseDrawer>
</template>

<style scoped lang="less">
.code-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line-strong);
}

.code-meta {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--faint);
  font-size: 8px;
  letter-spacing: 0.06em;
}

.mask-note {
  padding: 2px 5px;
  border: 1px solid var(--line);
  color: var(--warn);
  font-family: var(--font-ui);
  font-size: 9px;
}

.code-actions {
  display: flex;
  gap: 6px;
}

.code-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 56px 0;
  color: var(--faint);
  font-size: 12px;
}

.spinner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--accent-soft);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

.code-window {
  margin-top: 12px;
  overflow: auto;
  border: 1px solid var(--line);
  background: var(--panel);
  padding: 8px 0;
  .scrollbar();
}

.code-line {
  display: grid;
  grid-template-columns: 46px 1fr;
  min-width: 0;
  padding: 2px 10px 2px 0;
  border-left: 2px solid transparent;
  font-family: @font-mono;
  font-size: 11.5px;
  line-height: 1.65;

  &.highlight {
    border-left-color: var(--accent);
    background: var(--accent-soft);
  }

  .code-number {
    padding-right: 10px;
    color: var(--faint);
    text-align: right;
    user-select: none;
  }

  code {
    color: var(--text);
    white-space: pre;
    overflow-wrap: normal;
    min-width: 0;
  }
}

.code-foot {
  margin: 10px 0 0;
  color: var(--faint);
  font-size: 10px;
}
</style>
