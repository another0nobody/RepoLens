<script setup>
import { computed } from "vue";

import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { closeTech, copy, currentTech, state } from "../store";
import { categoryColor, fmtNumber, sourceLabel } from "../utils";

const tech = computed(() => currentTech.value);
const modules = computed(() => tech.value?.modules || []);
const evidence = computed(() => tech.value?.evidence || []);
const color = computed(() => categoryColor(tech.value?.category || ""));
</script>

<template>
  <BaseDrawer
    :open="Boolean(tech)"
    :title="tech?.name || '技术详情'"
    :subtitle="tech ? `${tech.function ? `${tech.function} · ` : ''}${tech.category} · ${tech.version ? `版本 ${tech.version}` : '版本未知'} · 置信度 ${tech.confidence}` : ''"
    wide
    @close="closeTech"
  >
    <template #eyebrow>
      <span v-if="tech" class="tag" :style="{ color, borderColor: color }">{{ tech.category }}</span>
    </template>

    <div v-if="tech" class="tech-body">
      <p class="role">{{ tech.role || tech.hint || "暂无职责说明。" }}</p>

      <div class="info-grid">
        <div class="ig">
          <b>{{ fmtNumber(tech.module_count) }}</b>
          <span>使用模块</span>
        </div>
        <div class="ig">
          <b>{{ fmtNumber(evidence.length) }}</b>
          <span>证据条数</span>
        </div>
        <div class="ig">
          <b>{{ (tech.sources || []).map(sourceLabel).join(" / ") || "扫描" }}</b>
          <span>识别来源</span>
        </div>
      </div>

      <p v-if="(tech.usage_tags || []).length" class="usage-line">
        用途：{{ tech.usage_tags.join("、") }}
      </p>

      <div v-if="tech.ai_inferred" class="notice">
        <Icon name="warning" :size="15" />
        这项技术是 AI 根据上下文推断的，代码中没有找到直接证据，请人工确认。
      </div>

      <h4>证据（依赖清单 / import / 代码使用）</h4>
      <ul v-if="evidence.length" class="evidence">
        <li v-for="(item, index) in evidence" :key="index">
          <button class="loc mono" type="button" @click="copy(`${item.path}:${item.line}`, '位置')">
            {{ item.path }}{{ item.line ? `:${item.line}` : "" }}
          </button>
          <span class="kind">{{ item.kind }}</span>
          <code>{{ item.text }}</code>
        </li>
      </ul>
      <p v-else class="muted small">没有可展示的证据。</p>

      <h4>使用它的模块</h4>
      <div v-if="modules.length" class="modules">
        <div v-for="module in modules" :key="`${module.path}:${module.line}`" class="module">
          <div class="module-head">
            <button class="loc mono" type="button" @click="copy(`${module.path}:${module.line}`, '位置')">
              {{ module.path }}:{{ module.line }}
            </button>
            <span class="role-tag">{{ module.role || "源码" }}</span>
          </div>
          <p v-if="module.summary" class="module-summary">{{ module.summary }}</p>
          <code class="snippet">{{ module.snippet || "（无代码片段）" }}</code>
        </div>
      </div>
      <p v-else class="muted small">没有找到直接 import。它可能只出现在依赖清单、Docker 镜像或配置文件中。</p>

      <div v-if="tech.hint" class="hint">
        <h4>技术说明</h4>
        <p>{{ tech.hint }}</p>
      </div>
    </div>
  </BaseDrawer>
</template>

<style scoped lang="less">
.tech-body {
  .role {
    margin: 0 0 16px;
    color: var(--text);
    font-size: 14px;
    line-height: 1.8;
  }

  .usage-line {
    margin: 9px 0 0;
    padding: 6px 9px;
    border-left: 0;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    color: var(--muted);
    font-size: 10.5px;
  }

  h4 {
    margin: 20px 0 9px;
    color: var(--faint);
    font-size: 10.5px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;

  .ig {
    padding: 10px 12px;
    border-radius: @radius-sm;
    border: 1px solid var(--line);
    background: var(--panel-soft);

    b {
      display: block;
      .mono();
      font-size: 14px;
      color: var(--text);
      word-break: break-all;
    }

    span {
      color: var(--faint);
      font-size: 10px;
    }
  }
}

.notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 14px;
  padding: 11px 12px;
  border-radius: @radius-sm;
  border: 1px solid color-mix(in srgb, var(--warn) 24%, transparent);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.65;
}

.evidence {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;

  li {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 4px 10px;
    padding: 9px 11px;
    border-radius: @radius-xs;
    border: 1px solid var(--line);
    background: var(--panel-soft);
    font-size: 11px;

    code {
      grid-column: 1 / -1;
      color: var(--muted);
      .mono();
      font-size: 10.5px;
      word-break: break-all;
    }
  }

  .kind {
    color: var(--faint);
    font-size: 10px;
  }
}

.loc {
  border: 0;
  background: none;
  padding: 0;
  color: var(--accent);
  text-align: left;
  .mono();
  font-size: 11px;
  word-break: break-all;

  &:hover {
    text-decoration: underline;
    text-underline-offset: 2px;
  }
}

.modules {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.module {
  padding: 10px 12px;
  border-radius: @radius-xs;
  border: 1px solid var(--line);
  background: var(--panel-soft);

  .module-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .role-tag {
    flex: none;
    color: var(--faint);
    font-size: 10px;
  }

  .module-summary {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.6;
  }

  .snippet {
    display: block;
    margin-top: 6px;
    color: var(--faint);
    .mono();
    font-size: 10.5px;
    word-break: break-all;
  }
}

.hint p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}

.small {
  font-size: 11.5px;
}
</style>
