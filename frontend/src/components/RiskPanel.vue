<script setup>
import { computed, ref, watch } from "vue";

import Icon from "./Icon.vue";
import { fetchRisks } from "../api";
import { openCode, openTech } from "../store";
import { fmtNumber } from "../utils";

const props = defineProps({
  report: { type: Object, default: null },
});

const data = ref(null);
const loading = ref(false);
const error = ref("");
const filter = ref("all");

const counts = computed(() => data.value?.counts || { high: 0, medium: 0, low: 0 });
const level = computed(() => data.value?.level || "none");
const levelLabel = computed(
  () => ({ high: "高风险", medium: "中风险", low: "低风险", none: "未发现" })[level.value] || "未知"
);
const visible = computed(() => {
  const findings = data.value?.findings || [];
  return filter.value === "all" ? findings : findings.filter((item) => item.severity === filter.value);
});

function fallbackFindings(report) {
  return (report?.risks || []).map((text, index) => ({
    id: `fallback-${index}`,
    severity: /密码|密钥|安全|敏感/.test(text) ? "high" : /缺少|没有|未/.test(text) ? "medium" : "low",
    severity_label: /密码|密钥|安全|敏感/.test(text) ? "高" : /缺少|没有|未/.test(text) ? "中" : "低",
    category: "报告风险",
    title: String(text).slice(0, 90),
    detail: String(text),
    action: "确认风险范围；需要时打开相关技术或代码补充证据。",
    tech: "",
    evidence: [],
  }));
}

function makeFallback(report, message) {
  const findings = fallbackFindings(report);
  const high = findings.filter((item) => item.severity === "high").length;
  const medium = findings.filter((item) => item.severity === "medium").length;
  const low = findings.filter((item) => item.severity === "low").length;
  return {
    level: high ? "high" : medium ? "medium" : low ? "low" : "none",
    score: Math.min(100, high * 28 + medium * 10 + low * 3),
    counts: { high, medium, low },
    total: findings.length,
    findings,
    warning: message,
  };
}

async function load() {
  if (!props.report?.run_id) return;
  loading.value = true;
  error.value = "";
  try {
    data.value = await fetchRisks(props.report.run_id);
  } catch (err) {
    data.value = makeFallback(props.report, err.message);
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

watch(() => props.report?.run_id, load, { immediate: true });

function severityClass(severity) {
  return `severity-${severity}`;
}
</script>

<template>
  <div class="risk-panel">
    <div class="risk-head">
      <div>
        <p class="eyebrow mono">RISK PANEL / 风险面板</p>
        <h2>哪些地方值得先确认</h2>
        <p class="risk-note">风险来自报告事实、依赖结构和扫描限制；不是安全审计结论。</p>
      </div>
      <div v-if="data" class="risk-score" :class="severityClass(level)">
        <span class="score mono">{{ fmtNumber(data.score) }}</span>
        <span class="score-label">{{ levelLabel }}</span>
        <span class="score-total mono">{{ data.total }} 项</span>
      </div>
    </div>

    <div v-if="loading" class="risk-loading">
      <span class="spinner"></span> 正在整理风险…
    </div>
    <div v-else-if="!data" class="empty-state">{{ error || "还没有风险数据。" }}</div>

    <template v-else>
      <p v-if="error" class="risk-warning">风险接口不可用，已回退到报告风险列表：{{ error }}</p>

      <div class="risk-toolbar">
        <div class="risk-filter" role="group" aria-label="风险严重度筛选">
          <button type="button" :class="{ active: filter === 'all' }" @click="filter = 'all'">
            全部 · {{ data.total }}
          </button>
          <button type="button" :class="{ active: filter === 'high' }" @click="filter = 'high'">
            高 · {{ counts.high }}
          </button>
          <button type="button" :class="{ active: filter === 'medium' }" @click="filter = 'medium'">
            中 · {{ counts.medium }}
          </button>
          <button type="button" :class="{ active: filter === 'low' }" @click="filter = 'low'">
            低 · {{ counts.low }}
          </button>
        </div>
        <span class="mono risk-hint">点击证据打开代码</span>
      </div>

      <div v-if="visible.length" class="risk-list">
        <article v-for="finding in visible" :key="finding.id" class="risk-item" :class="severityClass(finding.severity)">
          <div class="risk-item-head">
            <span class="risk-severity">{{ finding.severity_label }}</span>
            <span class="risk-category mono">{{ finding.category }}</span>
            <span v-if="finding.tech" class="risk-tech">
              <button type="button" @click="openTech(finding.tech)">{{ finding.tech }}</button>
            </span>
          </div>
          <h3>{{ finding.title }}</h3>
          <p class="risk-detail">{{ finding.detail }}</p>
          <p v-if="finding.action" class="risk-action">建议：{{ finding.action }}</p>
          <div v-if="finding.evidence?.length" class="risk-evidence">
            <button
              v-for="item in finding.evidence"
              :key="`${item.path}:${item.line}`"
              type="button"
              class="risk-evidence-btn mono"
              @click="openCode(item.path, item.line)"
            >
              {{ item.path }}:{{ item.line }}
            </button>
          </div>
        </article>
      </div>
      <div v-else class="empty-state">这个严重度下没有风险项。</div>

      <p class="risk-foot">
        <Icon name="warning" :size="12" />
        风险面板只覆盖扫描与报告能证明的内容；没有发现某项风险不等于它不存在。
      </p>
    </template>
  </div>
</template>

<style scoped lang="less">
.risk-head {
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

.risk-note {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.risk-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 82px;
  padding: 6px 9px;
  border: 1px solid var(--line);
  background: var(--panel);

  .score {
    color: var(--text);
    font-size: 26px;
    line-height: 1;
  }

  .score-label {
    margin-top: 4px;
    color: var(--faint);
    font-size: 9px;
  }

  .score-total {
    margin-top: 2px;
    color: var(--faint);
    font-size: 8px;
  }

  &.severity-high {
    border-color: var(--accent);

    .score,
    .score-label {
      color: var(--accent);
    }
  }

  &.severity-medium .score-label {
    color: var(--warn);
  }
}

.risk-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 52px 0;
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

.risk-warning {
  margin: 10px 0 0;
  padding: 7px 9px;
  border-left: 2px solid var(--warn);
  color: var(--warn);
  font-size: 10px;
}

.risk-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 13px 0;
}

.risk-filter {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid var(--line);

  button {
    padding: 5px 8px;
    border: 0;
    border-right: 1px solid var(--line);
    background: transparent;
    color: var(--muted);
    font-family: var(--font-ui);
    font-size: 9.5px;
    cursor: pointer;

    &:last-child {
      border-right: 0;
    }

    &.active {
      background: var(--accent-soft);
      color: var(--accent);
    }
  }
}

.risk-hint {
  color: var(--faint);
  font-size: 8px;
}

.risk-list {
  display: flex;
  flex-direction: column;
}

.risk-item {
  padding: 14px 14px 13px;
  border: 1px solid var(--line);
  border-left: 3px solid var(--line-strong);
  background: var(--panel);
  margin-bottom: 8px;

  &.severity-high {
    border-left-color: var(--accent);
  }

  &.severity-medium {
    border-left-color: var(--warn);
  }

  &.severity-low {
    border-left-color: var(--good);
  }

  h3 {
    margin: 7px 0 4px;
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 500;
  }
}

.risk-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.risk-severity {
  padding: 2px 5px;
  border: 1px solid var(--line-strong);
  color: var(--faint);
  font-family: var(--font-ui);
  font-size: 8px;

  .severity-high & {
    border-color: var(--accent);
    color: var(--accent);
  }

  .severity-medium & {
    border-color: var(--warn);
    color: var(--warn);
  }
}

.risk-category {
  color: var(--faint);
  font-size: 8px;
  letter-spacing: 0.05em;
}

.risk-tech {
  margin-left: auto;

  button {
    padding: 2px 5px;
    border: 1px solid var(--line);
    background: transparent;
    color: var(--accent);
    font-family: var(--font-ui);
    font-size: 9px;
    cursor: pointer;
  }
}

.risk-detail {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.65;
}

.risk-action {
  margin: 6px 0 0;
  color: var(--faint);
  font-size: 10px;
  line-height: 1.55;
}

.risk-evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.risk-evidence-btn {
  max-width: 100%;
  overflow: hidden;
  padding: 3px 6px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;

  &:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
}

.risk-foot {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 12px 0 0;
  color: var(--faint);
  font-size: 9.5px;
  line-height: 1.5;
}

@media (max-width: 720px) {
  .risk-head {
    display: block;
  }

  .risk-score {
    align-items: flex-start;
    margin-top: 10px;
  }

  .risk-toolbar {
    align-items: flex-start;
  }

  .risk-hint {
    display: none;
  }
}
</style>
