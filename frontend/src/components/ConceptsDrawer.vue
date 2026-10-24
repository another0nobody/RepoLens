<script setup>
import BaseDrawer from "./BaseDrawer.vue";
import { closeConcepts, state } from "../store";
</script>

<template>
  <BaseDrawer
    :open="state.drawers.concepts"
    title="知识点讲解"
    subtitle="每个卡片对应教程里的一个章节，说明本项目的哪个功能用了它。"
    wide
    @close="closeConcepts"
  >
    <div v-if="state.conceptsLoading" class="empty-state">正在加载知识点…</div>
    <div v-else class="concepts">
      <details v-for="concept in state.concepts" :key="concept.id" class="concept">
        <summary>
          <span class="chapter">{{ concept.chapter }}</span>
          <span class="title">{{ concept.title }}</span>
          <span class="plus" aria-hidden="true">+</span>
        </summary>
        <div class="summary">{{ concept.summary }}</div>
        <div class="detail">{{ concept.detail }}</div>
      </details>
      <div v-if="!state.concepts.length" class="empty-state">暂无内容。</div>
    </div>
  </BaseDrawer>
</template>

<style scoped lang="less">
.concepts {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.concept {
  border-radius: @radius-md;
  border: 1px solid var(--line);
  background: var(--panel-soft);
  overflow: hidden;

  summary {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    cursor: pointer;
    list-style: none;

    &::-webkit-details-marker {
      display: none;
    }
  }

  .chapter {
    flex: none;
    padding: 2px 8px;
    border-radius: @radius-pill;
    border: 1px solid var(--accent-line);
    color: var(--accent);
    font-size: 9.5px;
    white-space: nowrap;
  }

  .title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text);
  }

  .plus {
    margin-left: auto;
    color: var(--faint);
    font-size: 16px;
    transition: transform 0.2s @ease-out;
  }

  &[open] .plus {
    transform: rotate(45deg);
  }

  .summary {
    padding: 0 16px 4px;
    color: var(--muted);
    font-size: 12px;
  }

  .detail {
    margin: 9px 16px 16px;
    padding-top: 10px;
    border-top: 1px dashed var(--line);
    color: var(--muted);
    font-size: 12px;
    line-height: 1.85;
  }
}
</style>
