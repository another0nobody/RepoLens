<script setup>
import { computed } from "vue";

import Icon from "./Icon.vue";
import { fmtNumber } from "../utils";

const props = defineProps({
  report: { type: Object, required: true },
});

const architecture = computed(() => props.report.architecture || []);
const risks = computed(() => props.report.risks || []);
const learning = computed(() =>
  (props.report.learning_path || []).map((item) => String(item).replace(/^\s*\d+\s*[.、]\s*/, ""))
);
const entryPoints = computed(() => (props.report.entry_points || []).slice(0, 8));
const manifests = computed(() => (props.report.manifests || []).slice(0, 8));
const topDirs = computed(() => (props.report.top_dirs || []).slice(0, 6));
const languages = computed(() => (props.report.languages || []).filter((item) => item.is_code).slice(0, 5));
const maxDir = computed(() => Math.max(1, ...topDirs.value.map((item) => item.files || 0)));
const maxLoc = computed(() => Math.max(1, ...languages.value.map((item) => item.loc || 0)));
</script>

<template>
  <div class="architecture">
    <div class="two-col">
      <section class="card">
        <header class="card-head">
          <Icon name="layers" :size="16" />
          <h3>架构解读</h3>
        </header>
        <ol v-if="architecture.length" class="numbered">
          <li v-for="(item, index) in architecture" :key="index">{{ item }}</li>
        </ol>
        <p v-else class="muted small">报告没有提供架构说明。</p>
      </section>

      <section class="card">
        <header class="card-head">
          <Icon name="warning" :size="16" />
          <h3>风险与建议</h3>
        </header>
        <ul v-if="risks.length" class="risk-list">
          <li v-for="(item, index) in risks" :key="index">{{ item }}</li>
        </ul>
        <div v-else class="risk-empty">
          <Icon name="check" :size="15" />
          没有发现明显的风险信号。仍建议人工检查依赖版本与密钥配置。
        </div>
      </section>
    </div>

    <div class="two-col">
      <section class="card">
        <header class="card-head">
          <Icon name="book" :size="16" />
          <h3>学习路径</h3>
        </header>
        <ul v-if="learning.length" class="learn-list">
          <li v-for="(item, index) in learning" :key="index">{{ item }}</li>
        </ul>
        <p v-else class="muted small">报告没有提供学习路径。</p>
      </section>

      <section class="card">
        <header class="card-head">
          <Icon name="folder" :size="16" />
          <h3>关键文件与目录</h3>
        </header>

        <div v-if="entryPoints.length" class="kf-block">
          <h4>入口 / 关键文件</h4>
          <div v-for="path in entryPoints" :key="path" class="kf-item">{{ path }}</div>
        </div>

        <div v-if="manifests.length" class="kf-block">
          <h4>依赖清单</h4>
          <div v-for="item in manifests" :key="item.path" class="kf-item">
            <span>{{ item.path }}</span>
            <b>{{ fmtNumber(item.dependency_count) }} 条依赖</b>
          </div>
        </div>

        <div v-if="topDirs.length" class="kf-block">
          <h4>目录规模</h4>
          <div class="bars">
            <div v-for="item in topDirs" :key="item.name" class="bar-row">
              <span class="bar-label">{{ item.name }}/</span>
              <span class="bar-track">
                <span class="bar-fill" :style="{ width: `${Math.max(7, Math.round((item.files / maxDir) * 100))}%` }"></span>
              </span>
              <span class="bar-num mono">{{ fmtNumber(item.files) }}</span>
            </div>
          </div>
        </div>

        <div v-if="languages.length" class="kf-block">
          <h4>语言分布</h4>
          <div class="bars">
            <div v-for="item in languages" :key="item.name" class="bar-row">
              <span class="bar-label">{{ item.name }}</span>
              <span class="bar-track">
                <span class="bar-fill alt" :style="{ width: `${Math.max(7, Math.round((item.loc / maxLoc) * 100))}%` }"></span>
              </span>
              <span class="bar-num mono">{{ item.percent }}%</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped lang="less">
.architecture {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.card {
  padding: 20px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: var(--accent);

  h3 {
    margin: 0;
    color: var(--text);
    font-size: 14.5px;
  }
}

.numbered {
  list-style: none;
  counter-reset: n;
  margin: 0;
  padding: 0;

  li {
    position: relative;
    counter-increment: n;
    padding: 0 0 13px 30px;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.7;

    &::before {
      content: counter(n, decimal-leading-zero);
      position: absolute;
      left: 0;
      top: 0;
      .mono();
      font-size: 10px;
      color: var(--accent);
      border: 1px solid var(--accent-line);
      border-radius: 6px;
      padding: 1px 4px;
    }

    &:last-child {
      padding-bottom: 0;
    }
  }
}

.learn-list {
  list-style: none;
  margin: 0;
  padding: 0;

  li {
    position: relative;
    padding: 0 0 12px 22px;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.7;

    &::before {
      content: "";
      position: absolute;
      left: 3px;
      top: 8px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 8px var(--accent);
    }

    &:last-child {
      padding-bottom: 0;
    }
  }
}

.risk-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;

  li {
    position: relative;
    padding: 10px 12px 10px 32px;
    border-radius: @radius-sm;
    border: 1px solid color-mix(in srgb, var(--warn) 20%, transparent);
    background: var(--warn-soft);
    color: var(--muted);
    font-size: 12px;
    line-height: 1.65;

    &::before {
      content: "!";
      position: absolute;
      left: 12px;
      top: 11px;
      width: 14px;
      height: 14px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: var(--warn);
      color: #101828;
      font-size: 9px;
      font-weight: 800;
    }
  }
}

.risk-empty {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  border-radius: @radius-sm;
  border: 1px solid color-mix(in srgb, var(--good) 20%, transparent);
  background: var(--good-soft);
  color: var(--good);
  font-size: 12px;
  line-height: 1.65;
}

.small {
  font-size: 12px;
}

.kf-block {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }

  h4 {
    margin: 0 0 8px;
    color: var(--faint);
    font-size: 10.5px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
  }
}

.kf-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 5px 0;
  border-bottom: 1px dashed color-mix(in srgb, var(--line) 70%, transparent);
  .mono();
  font-size: 11px;
  color: var(--muted);
  word-break: break-all;

  b {
    flex: none;
    color: var(--text);
    font-weight: 500;
  }
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.bar-row {
  display: grid;
  grid-template-columns: 112px 1fr 46px;
  gap: 9px;
  align-items: center;
  font-size: 11px;
}

.bar-label {
  color: var(--muted);
  .truncate();
}

.bar-track {
  height: 5px;
  border-radius: @radius-pill;
  background: var(--panel-soft);
  overflow: hidden;
}

.bar-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  opacity: 0.8;

  &.alt {
    background: linear-gradient(90deg, var(--accent-2), var(--accent-3));
  }
}

.bar-num {
  text-align: right;
  color: var(--faint);
  font-size: 10px;
}

@media (max-width: @bp-lg) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
