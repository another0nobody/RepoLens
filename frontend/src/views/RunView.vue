<script setup>
import { computed } from "vue";

import LiveFeed from "../components/LiveFeed.vue";
import StageTimeline from "../components/StageTimeline.vue";
import TodoList from "../components/TodoList.vue";
import Icon from "../components/Icon.vue";
import { fmtDuration, fmtNumber } from "../utils";
import {
  leaveRun,
  loadReport,
  retryAnalysis,
  setFeedFilter,
  stageProgress,
  state,
} from "../store";

const run = computed(() => state.run || {});
const statusClass = computed(() => {
  if (run.value.status === "error") return "error";
  if (run.value.status === "done") return "done";
  return "running";
});
const statusLabel = computed(() => state.runStatusText || (run.value.status === "error" ? "分析失败" : "运行中"));
const stats = computed(() => run.value.stats || {});
const techCount = computed(() => run.value.techCount || 0);
</script>

<template>
  <section v-if="state.run" class="run-view">
    <div class="run-head">
      <button class="btn back-btn" type="button" @click="leaveRun">
        <Icon name="arrowLeft" :size="15" /> 返回
      </button>

      <div class="run-title">
        <div class="title-line">
          <h2>{{ run.repoName || "正在分析…" }}</h2>
          <span v-if="techCount" class="tag">{{ fmtNumber(techCount) }} 项技术</span>
        </div>
        <p class="source mono" :title="run.source">{{ run.source }}</p>
      </div>

      <div class="run-status" :class="statusClass">
        <span class="status-dot" aria-hidden="true"></span>
        <span class="status-text">{{ statusLabel }}</span>
        <span class="run-timer mono">{{ fmtDuration(state.elapsed) }}</span>
      </div>
    </div>

    <div class="progress-bar" aria-hidden="true">
      <span :style="{ width: `${stageProgress}%` }"></span>
    </div>

    <div class="run-layout">
      <aside class="rail">
        <div class="rail-card">
          <div class="rail-head">
            <h3>分析进度</h3>
            <span class="rail-percent mono">{{ stageProgress }}%</span>
          </div>
          <StageTimeline :stage="state.stage" :status="run.status" />
        </div>

        <div class="rail-card">
          <h3>Agent 的待办清单</h3>
          <TodoList :todos="state.todos" />
        </div>

        <div class="rail-card token-card">
          <h3>Token 用量</h3>
          <div class="token-row">
            <span>输入</span>
            <b>{{ fmtNumber(state.tokens.input) }}</b>
          </div>
          <div class="token-row">
            <span>输出</span>
            <b>{{ fmtNumber(state.tokens.output) }}</b>
          </div>
          <div class="token-meta">
            <span v-if="stats.file_count">{{ fmtNumber(stats.file_count) }} 文件</span>
            <span v-if="stats.total_loc">{{ fmtNumber(stats.total_loc) }} 行</span>
            <span v-if="run.model">{{ run.model }}</span>
          </div>
        </div>
      </aside>

      <div class="live-panel">
        <div class="live-head">
          <span class="live-dot" :class="statusClass" aria-hidden="true"></span>
          <span class="live-stage">{{ state.liveStage }}</span>
          <span class="live-hint">Agent 的每一步都会实时显示</span>
        </div>

        <LiveFeed
          :feed="state.feed"
          :filter="state.feedFilter"
          :running="run.status === 'running'"
          @update:filter="setFeedFilter"
        />

        <div v-if="run.status === 'error'" class="error-box">
          <Icon name="warning" :size="18" />
          <div>
            <b>分析失败</b>
            <p>{{ run.error || "请检查路径或网络后重试。" }}</p>
          </div>
          <button class="btn" type="button" @click="retryAnalysis">用相同来源重试</button>
        </div>

        <div v-else-if="run.status === 'done'" class="done-box">
          <span><Icon name="check" :size="16" /> 报告已生成</span>
          <button class="btn btn-primary" type="button" @click="loadReport(run.runId)">打开报告</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped lang="less">
.run-view {
  padding-top: 8px;
}

.run-head {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-bottom: 16px;
}

.back-btn {
  flex: none;
}

.run-title {
  flex: 1;
  min-width: 220px;

  .title-line {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  h2 {
    margin: 0;
    font-size: clamp(22px, 3vw, 30px);
    letter-spacing: -0.6px;
  }

  .source {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 11.5px;
    word-break: break-all;
  }
}

.run-status {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 8px 13px;
  border-radius: @radius-pill;
  border: 1px solid var(--accent-line);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12.5px;
  white-space: nowrap;

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 12px currentColor;
    animation: pulse 1.8s infinite;
  }

  &.done {
    border-color: color-mix(in srgb, var(--good) 34%, transparent);
    background: var(--good-soft);
    color: var(--good);

    .status-dot {
      animation: none;
    }
  }

  &.error {
    border-color: color-mix(in srgb, var(--bad) 34%, transparent);
    background: var(--bad-soft);
    color: var(--bad);

    .status-dot {
      animation: none;
    }
  }
}

.run-timer {
  color: var(--muted);
  font-size: 11px;
}

.progress-bar {
  height: 3px;
  margin-bottom: 18px;
  border-radius: @radius-pill;
  background: var(--panel-soft);
  overflow: hidden;

  span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    box-shadow: 0 0 16px var(--accent);
    transition: width 0.6s @ease-out;
  }
}

.run-layout {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.rail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 86px;
}

.rail-card {
  padding: 18px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);

  h3 {
    margin: 0 0 14px;
    font-size: 12.5px;
    letter-spacing: 0.2px;
  }
}

.rail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;

  h3 {
    margin: 0;
  }
}

.rail-percent {
  font-size: 10.5px;
  color: var(--accent);
}

.token-card {
  h3 {
    margin-bottom: 12px;
  }
}

.token-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--muted);
  padding: 4px 0;

  b {
    .mono();
    color: var(--text);
    font-weight: 500;
  }
}

.token-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
  color: var(--faint);
  font-size: 10.5px;

  span {
    padding: 2px 7px;
    border-radius: @radius-pill;
    background: var(--panel-soft);
  }
}

.live-panel {
  display: flex;
  flex-direction: column;
  min-height: 560px;
  max-height: 76vh;
  border-radius: @radius-xl;
  border: 1px solid var(--line);
  background: linear-gradient(170deg, color-mix(in srgb, var(--panel-solid) 55%, transparent), var(--panel));
  overflow: hidden;
}

.live-head {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 15px 18px;
  border-bottom: 1px solid var(--line);
  font-size: 12.5px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 16px var(--accent);
  animation: pulse 1.6s infinite;

  &.done {
    background: var(--good);
    box-shadow: 0 0 12px var(--good);
    animation: none;
  }

  &.error {
    background: var(--bad);
    box-shadow: 0 0 12px var(--bad);
    animation: none;
  }
}

.live-stage {
  color: var(--text);
}

.live-hint {
  margin-left: auto;
  color: var(--faint);
  font-size: 10.5px;
}

.error-box {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 18px 18px;
  padding: 12px 14px;
  border-radius: @radius-md;
  border: 1px solid color-mix(in srgb, var(--bad) 30%, transparent);
  background: var(--bad-soft);
  color: var(--bad);
  font-size: 12px;

  div {
    flex: 1;
  }

  b {
    display: block;
  }

  p {
    margin: 2px 0 0;
    color: var(--muted);
    font-size: 11.5px;
    word-break: break-word;
  }

  .btn {
    color: var(--text);
    border-color: color-mix(in srgb, var(--bad) 30%, transparent);
    flex: none;
  }
}

.done-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 18px 18px;
  padding: 12px 14px;
  border-radius: @radius-md;
  border: 1px solid color-mix(in srgb, var(--good) 30%, transparent);
  background: var(--good-soft);
  color: var(--good);
  font-size: 12px;

  span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
}

@media (max-width: @bp-lg) {
  .run-layout {
    grid-template-columns: 1fr;
  }

  .rail {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .token-card {
    display: none;
  }

  .live-panel {
    min-height: 520px;
    max-height: none;
  }
}

@media (max-width: @bp-md) {
  .rail {
    grid-template-columns: 1fr;
  }

  .live-panel {
    min-height: 480px;
  }

  .live-hint {
    display: none;
  }
}
</style>
