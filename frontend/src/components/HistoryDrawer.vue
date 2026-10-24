<script setup>
import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { fmtDate, fmtNumber } from "../utils";
import { closeHistory, loadHistory, loadHistoryReport, state } from "../store";
</script>

<template>
  <BaseDrawer
    :open="state.drawers.history"
    title="历史分析"
    subtitle="报告保存在 data/reports；刷新页面或重启服务后仍可查看。"
    @close="closeHistory"
  >
    <div class="history-toolbar">
      <span class="muted">{{ state.history.length }} 份报告</span>
      <button class="btn" type="button" :disabled="state.historyLoading" @click="loadHistory">
        <Icon name="refresh" :size="14" /> 刷新
      </button>
    </div>

    <div v-if="state.historyLoading" class="history-empty">
      <span class="spinner"></span> 正在读取报告…
    </div>

    <div v-else-if="!state.history.length" class="empty-state">
      还没有历史报告。先分析一个仓库吧。
    </div>

    <div v-else class="history-list">
      <button
        v-for="item in state.history"
        :key="item.run_id"
        class="history-item"
        type="button"
        @click="loadHistoryReport(item.run_id)"
      >
        <div class="item-top">
          <span class="name">{{ item.repo_name }}</span>
          <span class="tag" :class="item.ai_used ? 'good' : 'warn'">{{ item.ai_used ? "AI" : "规则" }}</span>
        </div>
        <div class="meta">
          {{ fmtDate(item.generated_at) }} · {{ fmtNumber(item.tech_count) }} 项技术 ·
          {{ fmtNumber(item.code_files) }} 个代码文件 · {{ fmtNumber(item.total_loc) }} 行
        </div>
        <div class="source mono">{{ item.source }}</div>
      </button>
    </div>
  </BaseDrawer>
</template>

<style scoped lang="less">
.history-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  font-size: 11.5px;
}

.history-empty {
  display: flex;
  align-items: center;
  gap: 9px;
  justify-content: center;
  padding: 46px 0;
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.history-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 13px 15px;
  border-radius: @radius-sm;
  border: 1px solid var(--line);
  background: var(--panel-soft);
  transition: 0.18s @ease-out;
  .focus-ring();

  &:hover {
    border-color: var(--accent-line);
    background: var(--accent-soft);
    transform: translateY(-1px);
  }

  .item-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .name {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text);
  }

  .meta {
    margin-top: 4px;
    color: var(--faint);
    font-size: 10.5px;
    line-height: 1.6;
  }

  .source {
    margin-top: 3px;
    color: var(--faint);
    font-size: 10px;
    word-break: break-all;
  }
}
</style>
