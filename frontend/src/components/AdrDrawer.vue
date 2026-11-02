<script setup>
import { computed } from "vue";

import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { closeAdr, copy, loadAdr, state } from "../store";
import { download } from "../utils";

const adr = computed(() => state.adr);
const data = computed(() => adr.value.data);
const techs = computed(() =>
  [...(state.report?.techs || [])]
    .filter((tech) => tech.name)
    .sort((a, b) => String(a.name).localeCompare(String(b.name), "zh-CN"))
);

function choose(event) {
  loadAdr(event.target.value);
}

function copyMarkdown() {
  if (data.value) copy(data.value.markdown, "ADR Markdown");
}

function downloadMarkdown() {
  if (!data.value) return;
  download(data.value.filename, data.value.markdown, "text/markdown;charset=utf-8");
}
</script>

<template>
  <BaseDrawer
    :open="adr.open"
    title="技术选型 ADR"
    subtitle="基于报告事实生成可选型记录；选型动机未记录时明确标注为待确认。"
    wide
    @close="closeAdr"
  >
    <template #eyebrow>
      <span class="tag mono">ARCHITECTURE DECISION / 决策记录</span>
    </template>

    <div class="adr-toolbar">
      <label class="adr-picker">
        <span class="mono">技术 / TECH</span>
        <select :value="adr.tech" :disabled="adr.loading" @change="choose">
          <option v-for="tech in techs" :key="tech.key || tech.name" :value="tech.name">
            {{ tech.name }} · {{ tech.layer || tech.category }}
          </option>
        </select>
      </label>
      <div class="adr-actions">
        <button class="btn" type="button" :disabled="!data" @click="copyMarkdown">
          <Icon name="copy" :size="14" /> 复制 Markdown
        </button>
        <button class="btn" type="button" :disabled="!data" @click="downloadMarkdown">
          <Icon name="download" :size="14" /> 下载 .md
        </button>
      </div>
    </div>

    <div v-if="adr.loading" class="adr-loading">
      <span class="spinner"></span> 正在生成 ADR…
    </div>
    <div v-else-if="adr.error" class="empty-state">{{ adr.error }}</div>

    <template v-else-if="data">
      <div class="adr-meta">
        <span class="mono">{{ data.filename }}</span>
        <span>状态：提议 · 待团队确认</span>
      </div>

      <div v-if="data.alternatives?.length" class="adr-alternatives">
        <span class="mono">备选方案</span>
        <span v-for="item in data.alternatives" :key="item.name" class="adr-alt">
          {{ item.name }}
          <em v-if="item.in_project">项目内已有</em>
        </span>
      </div>

      <pre class="adr-preview">{{ data.markdown }}</pre>

      <p class="adr-foot">
        ADR 中的“同类方案”来自技术词典，不代表团队真实比较过；涉及动机、成本和合规的内容请在团队内确认。
      </p>
    </template>
  </BaseDrawer>
</template>

<style scoped lang="less">
.adr-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 13px;
  border-bottom: 1px solid var(--line-strong);
}

.adr-picker {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;

  > span {
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.07em;
  }

  select {
    min-width: 220px;
    max-width: 100%;
    padding: 7px 8px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 11px;
  }
}

.adr-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.adr-loading {
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

.adr-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 0 8px;
  color: var(--faint);
  font-size: 9px;
}

.adr-alternatives {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;

  > span:first-child {
    margin-right: 4px;
    color: var(--faint);
    font-size: 8px;
  }
}

.adr-alt {
  padding: 3px 6px;
  border: 1px solid var(--line);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 9px;

  em {
    margin-left: 3px;
    color: var(--accent);
    font-size: 8px;
    font-style: normal;
  }
}

.adr-preview {
  margin: 0;
  padding: 14px;
  max-height: 58vh;
  overflow: auto;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
  font-family: @font-mono;
  font-size: 11px;
  line-height: 1.7;
  white-space: pre-wrap;
  .scrollbar();
}

.adr-foot {
  margin: 10px 0 0;
  color: var(--faint);
  font-size: 9.5px;
  line-height: 1.5;
}

@media (max-width: 720px) {
  .adr-toolbar {
    display: block;
  }

  .adr-picker {
    display: block;

    > span {
      display: block;
      margin-bottom: 4px;
    }

    select {
      width: 100%;
      min-width: 0;
    }
  }

  .adr-actions {
    margin-top: 10px;
  }
}
</style>
