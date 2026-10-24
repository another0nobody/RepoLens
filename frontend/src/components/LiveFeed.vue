<script setup>
import { computed, nextTick, ref, watch } from "vue";

import Icon from "./Icon.vue";

const props = defineProps({
  feed: { type: Array, default: () => [] },
  filter: { type: String, default: "all" },
  running: { type: Boolean, default: false },
});
const emit = defineEmits(["update:filter"]);

const listRef = ref(null);
const stick = ref(true);
const filters = [
  { key: "all", label: "全部" },
  { key: "tool", label: "工具" },
  { key: "progress", label: "进度" },
  { key: "warn", label: "异常" },
];

const filtered = computed(() => {
  if (props.filter === "tool") return props.feed.filter((item) => ["tool", "plan"].includes(item.kind));
  if (props.filter === "progress") return props.feed.filter((item) => item.kind === "info");
  if (props.filter === "warn") return props.feed.filter((item) => ["warn", "error"].includes(item.kind));
  return props.feed;
});

function onScroll() {
  const el = listRef.value;
  if (!el) return;
  stick.value = el.scrollHeight - el.scrollTop - el.clientHeight < 36;
}

async function scrollToBottom() {
  await nextTick();
  const el = listRef.value;
  if (el) el.scrollTop = el.scrollHeight;
  stick.value = true;
}

watch(
  () => [props.feed.length, props.filter],
  async () => {
    if (stick.value) await scrollToBottom();
  }
);

const iconFor = (kind) => {
  if (kind === "tool") return "terminal";
  if (kind === "plan") return "layers";
  if (kind === "ok") return "check";
  if (kind === "warn") return "warning";
  if (kind === "error") return "warning";
  return "spark";
};
</script>

<template>
  <div class="live-feed-wrap">
    <div class="feed-toolbar">
      <div class="filters">
        <button
          v-for="item in filters"
          :key="item.key"
          class="chip mini"
          :class="{ active: filter === item.key }"
          type="button"
          @click="emit('update:filter', item.key)"
        >
          {{ item.label }}
        </button>
      </div>
      <span class="feed-count">{{ filtered.length }} 条</span>
    </div>

    <div ref="listRef" class="feed" @scroll.passive="onScroll">
      <TransitionGroup name="feed">
        <div v-for="item in filtered" :key="item.id" class="feed-line" :class="item.kind">
          <span class="time">{{ item.time }}</span>
          <span class="feed-icon"><Icon :name="iconFor(item.kind)" :size="13" /></span>
          <span class="text">{{ item.text }}</span>
        </div>
      </TransitionGroup>

      <div v-if="!filtered.length" class="feed-empty">
        <span v-if="running" class="spinner"></span>
        <span>{{ running ? "等待 Agent 的第一步…" : "本次分析没有相关事件。" }}</span>
      </div>
    </div>

    <Transition name="fade">
      <button v-if="!stick && filtered.length" class="jump-btn btn" type="button" @click="scrollToBottom">
        <Icon name="down" :size="14" /> 回到底部
      </button>
    </Transition>
  </div>
</template>

<style scoped lang="less">
.live-feed-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.feed-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--line);
}

.filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip.mini {
  padding: 4px 10px;
  font-size: 11px;
}

.feed-count {
  color: var(--faint);
  font-size: 10.5px;
  .mono();
}

.feed {
  flex: 1;
  overflow-y: auto;
  max-height: 58vh;
  padding: 14px 18px 24px;
  .scrollbar();
}

.feed-line {
  display: grid;
  grid-template-columns: 55px 18px 1fr;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed color-mix(in srgb, var(--line) 55%, transparent);
  font-size: 12.5px;
  line-height: 1.55;
  animation: fade-up 0.24s @ease-out;

  &:last-child {
    border-bottom: 0;
  }

  .time {
    .mono();
    color: var(--faint);
    font-size: 10px;
    padding-top: 2px;
  }

  .feed-icon {
    color: var(--faint);
    padding-top: 1px;
    display: flex;
    justify-content: center;
  }

  .text {
    color: var(--muted);
    word-break: break-word;
  }

  &.info .text,
  &.ok .text {
    color: var(--text);
  }

  &.tool .feed-icon,
  &.tool .text {
    color: var(--accent);
  }

  &.plan .feed-icon,
  &.plan .text {
    color: var(--accent-2);
  }

  &.warn .feed-icon,
  &.warn .text {
    color: var(--warn);
  }

  &.error .feed-icon,
  &.error .text {
    color: var(--bad);
  }
}

.feed-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 64px 20px;
  color: var(--faint);
  font-size: 12.5px;
}

.spinner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--accent-soft);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

.jump-btn {
  position: absolute;
  right: 20px;
  bottom: 16px;
  padding: 7px 11px;
  font-size: 11.5px;
  box-shadow: var(--shadow-soft);
}

.feed-enter-active {
  transition: opacity 0.22s @ease-out, transform 0.22s @ease-out;
}

.feed-enter-from {
  opacity: 0;
  transform: translateY(5px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: @bp-md) {
  .feed {
    max-height: 50vh;
  }
}
</style>
