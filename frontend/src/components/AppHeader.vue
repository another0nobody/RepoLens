<script setup>
import { computed } from "vue";

import Icon from "./Icon.vue";

const props = defineProps({
  health: { type: Object, default: null },
  theme: { type: String, default: "light" },
});
const emit = defineEmits(["brand", "history", "concepts", "toggle-theme"]);

const modelLabel = computed(() => {
  if (!props.health) return "检测环境中…";
  return props.health.ai_available ? props.health.model : "未配置模型 · 仅规则扫描";
});

const modelClass = computed(() => (!props.health ? "" : props.health.ai_available ? "ok" : "warn"));
</script>

<template>
  <header class="map-head">
    <div class="topbar">
      <button class="brand" type="button" aria-label="回到首页" @click="emit('brand')">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-text">
          <strong>RepoLens</strong>
          <small>FIELD MAP / 001</small>
        </span>
      </button>

      <div class="topbar-right">
        <span class="model" :class="modelClass" :title="health ? '当前使用的大模型' : '正在连接后端'">
          <i></i>{{ modelLabel }}
        </span>
        <button class="nav-btn" type="button" @click="emit('history')">历史</button>
        <button class="nav-btn" type="button" @click="emit('concepts')">知识点</button>
        <button
          class="theme-btn"
          type="button"
          :aria-label="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          :title="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          @click="emit('toggle-theme')"
        >
          <Icon :name="theme === 'dark' ? 'sun' : 'moon'" :size="15" />
        </button>
      </div>
    </div>

    <div class="legend" aria-label="地图图例">
      <span class="legend-label">LEGEND</span>
      <span><i class="swatch scan"></i>扫描事实</span>
      <span><i class="swatch agent"></i>Agent 核实</span>
      <span><i class="swatch proof"></i>报告证据</span>
      <span><i class="swatch ask"></i>追问 / 深挖</span>
      <span class="legend-note">LOCAL / READ-ONLY</span>
    </div>
  </header>
</template>

<style scoped lang="less">
.map-head {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--bg);
  border-bottom: 1px solid var(--line-strong);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  max-width: 1320px;
  margin: 0 auto;
  padding: 13px 34px 11px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 0;
  background: none;
  padding: 0;
  color: var(--text);
  text-align: left;
  .focus-ring();

  &:hover .brand-mark {
    border-color: var(--accent);
  }

  &:hover .brand-mark::after {
    background: var(--accent);
  }
}

.brand-mark {
  position: relative;
  width: 29px;
  height: 29px;
  flex: none;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  transition: border-color 0.16s;

  &::before,
  &::after {
    content: "";
    position: absolute;
  }

  &::before {
    left: 50%;
    top: -4px;
    bottom: -4px;
    width: 1px;
    background: var(--line-strong);
  }

  &::after {
    left: 50%;
    top: 50%;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent);
    transform: translate(-50%, -50%);
    transition: background 0.16s;
  }
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.05;

  strong {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.03em;
  }

  small {
    margin-top: 2px;
    color: var(--faint);
    .mono();
    font-size: 7.5px;
    letter-spacing: 0.1em;
  }
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.model {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 250px;
  color: var(--faint);
  font-size: 9px;
  .truncate();

  i {
    width: 5px;
    height: 5px;
    flex: none;
    background: var(--faint);
  }

  &.ok i {
    background: var(--good);
  }

  &.warn i {
    background: var(--warn);
  }
}

.nav-btn,
.theme-btn {
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 10.5px;
  cursor: pointer;

  &:hover {
    color: var(--accent);
  }
}

.theme-btn {
  display: inline-flex;
  align-items: center;
  margin-left: 2px;
}

.legend {
  display: flex;
  align-items: center;
  gap: 14px;
  max-width: 1320px;
  margin: 0 auto;
  padding: 6px 34px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;
  overflow-x: auto;

  span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
  }
}

.legend-label {
  .mono();
  font-size: 7.5px;
  letter-spacing: 0.1em;
}

.legend-note {
  margin-left: auto;
  .mono();
  font-size: 7.5px;
  letter-spacing: 0.08em;
}

.swatch {
  width: 9px;
  height: 9px;
  display: inline-block;

  &.scan {
    background: var(--accent-2);
  }

  &.agent {
    background: #d3ad50;
  }

  &.proof {
    background: var(--accent-3);
  }

  &.ask {
    background: var(--accent);
  }
}

@media (max-width: @bp-md) {
  .topbar {
    padding: 10px 16px 8px;
  }

  .brand-text strong {
    font-size: 18px;
  }

  .brand-text small {
    display: none;
  }

  .model {
    display: none;
  }

  .topbar-right {
    gap: 12px;
  }

  .legend {
    padding: 6px 16px;
    gap: 10px;
  }

  .legend-note {
    display: none !important;
  }
}
</style>
