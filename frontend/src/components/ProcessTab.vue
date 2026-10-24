<script setup>
import { computed, ref } from "vue";

import { fmtTime, toolLabel, truncate } from "../utils";

const props = defineProps({
  events: { type: Array, default: () => [] },
});

const filter = ref("all");
const filters = [
  { key: "all", label: "全部" },
  { key: "tool", label: "工具" },
  { key: "phase", label: "阶段" },
  { key: "warn", label: "异常" },
];

function describe(event) {
  const data = event.data || {};
  switch (event.type) {
    case "phase":
      return { type: "阶段", text: data.label || data.stage || "" };
    case "tool":
      return {
        type: "工具",
        text: `${toolLabel(data.name)} · ${data.status === "start" ? "开始" : data.status === "end" ? "完成" : "失败"}${
          data.duration ? ` · ${data.duration}s` : ""
        }`,
      };
    case "progress":
      return { type: "进度", text: data.message || "" };
    case "plan":
      return { type: "计划", text: (data.tools || []).map((tool) => toolLabel(tool.name)).join("、") };
    case "todos":
      return { type: "待办", text: `更新为 ${(data.todos || []).length} 项` };
    case "meta":
      return { type: "扫描", text: `完成 ${data.stats?.file_count || 0} 个文件，识别 ${data.tech_count || 0} 项技术` };
    case "warning":
      return { type: "警告", text: data.message || "" };
    case "error":
      return { type: "错误", text: data.message || "" };
    case "interrupt":
      return { type: "审批", text: "等待用户批准克隆仓库" };
    case "interrupt_resolved":
      return { type: "审批", text: `用户选择：${data.decision}` };
    case "done":
      return { type: "完成", text: `生成 ${data.tech_count || 0} 项技术的报告` };
    default:
      return null;
  }
}

const rows = computed(() =>
  props.events
    .map((event) => ({ event, info: describe(event) }))
    .filter((row) => row.info)
    .filter((row) => {
      if (filter.value === "all") return true;
      if (filter.value === "tool") return ["tool", "plan"].includes(row.event.type);
      if (filter.value === "phase") return ["phase", "meta", "done"].includes(row.event.type);
      return ["warning", "error", "interrupt"].includes(row.event.type);
    })
);
</script>

<template>
  <div class="process card">
    <div class="process-head">
      <div>
        <h3>分析过程回放</h3>
        <p class="muted">Agent 本次运行产生的事件流，用来理解它「为什么这么判断」。</p>
      </div>
      <div class="chips">
        <button
          v-for="item in filters"
          :key="item.key"
          class="chip"
          :class="{ active: filter === item.key }"
          type="button"
          @click="filter = item.key"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <ol v-if="rows.length" class="process-log">
      <li v-for="(row, index) in rows" :key="index">
        <span class="t mono">{{ fmtTime(row.event.ts) }}</span>
        <span class="n">{{ row.info.type }}</span>
        <span class="c">{{ truncate(row.info.text, 260) }}</span>
      </li>
    </ol>
    <div v-else class="empty-state">
      历史报告只保存最终结果，没有保存事件流。重新分析一次即可在这里回放 Agent 的每一步。
    </div>
  </div>
</template>

<style scoped lang="less">
.process {
  padding: 20px;
}

.process-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;

  h3 {
    margin: 0 0 4px;
    font-size: 14.5px;
  }

  p {
    margin: 0;
    font-size: 11.5px;
  }
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.process-log {
  list-style: none;
  margin: 0;
  padding: 0;

  li {
    display: grid;
    grid-template-columns: 55px 48px 1fr;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px dashed color-mix(in srgb, var(--line) 65%, transparent);
    font-size: 11.5px;
    color: var(--muted);

    &:last-child {
      border-bottom: 0;
    }
  }

  .t {
    color: var(--faint);
    font-size: 10px;
    padding-top: 2px;
  }

  .n {
    color: var(--accent);
    font-size: 10px;
    letter-spacing: 0.4px;
  }

  .c {
    word-break: break-word;
  }
}
</style>
