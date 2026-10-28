<script setup>
import { computed } from "vue";

import BrandLogo from "./BrandLogo.vue";
import Icon from "./Icon.vue";

const props = defineProps({
  health: { type: Object, default: null },
  theme: { type: String, default: "dark" },
});
const emit = defineEmits(["brand", "history", "concepts", "toggle-theme"]);

const modelLabel = computed(() => {
  if (!props.health) return "检测环境中…";
  return props.health.ai_available ? props.health.model : "未配置模型 · 仅规则扫描";
});

const modelClass = computed(() => (!props.health ? "" : props.health.ai_available ? "ok" : "warn"));
</script>

<template>
  <header class="topbar-wrap">
    <div class="edge-rail" aria-hidden="true">
      <span>REPOLENS / CONTACT PROOF</span>
      <span>ROLL 001 · 35MM · SAFETY FILM</span>
      <span>LOCAL / READ-ONLY</span>
    </div>

    <div class="topbar">
      <button class="brand" type="button" aria-label="回到首页" @click="emit('brand')">
        <span class="brand-mark"><BrandLogo :size="28" /></span>
        <span class="brand-text">
          <strong>RepoLens</strong>
          <small>技术栈证据表</small>
        </span>
      </button>

      <div class="topbar-right">
        <span class="model-pill" :class="modelClass" :title="health ? '当前使用的大模型' : '正在连接后端'">
          <span class="dot"></span>
          <span class="model-text">{{ modelLabel }}</span>
        </span>
        <button class="btn btn-ghost nav-btn" type="button" title="查看历史分析" @click="emit('history')">
          <Icon name="history" :size="16" />
          <span>历史</span>
        </button>
        <button class="btn btn-ghost nav-btn" type="button" title="查看知识点讲解" @click="emit('concepts')">
          <Icon name="book" :size="16" />
          <span>知识点</span>
        </button>
        <button
          class="icon-btn"
          type="button"
          :aria-label="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          :title="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          @click="emit('toggle-theme')"
        >
          <Icon :name="theme === 'dark' ? 'sun' : 'moon'" :size="17" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped lang="less">
.topbar-wrap {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line-strong);
}

.edge-rail {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 5px 26px;
  border-bottom: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: @space-5;
  max-width: 1280px;
  margin: 0 auto;
  padding: 12px 26px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 0;
  background: none;
  padding: 0;
  text-align: left;
  .focus-ring();

  &:hover .brand-mark {
    border-color: var(--accent);
  }
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--line-strong);
  padding: 2px;
  transition: border-color 0.16s;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;

  strong {
    font-size: 18px;
    font-weight: 500;
    letter-spacing: -0.03em;
  }

  small {
    color: var(--faint);
    font-size: 8.5px;
    letter-spacing: 0.13em;
    text-transform: uppercase;
  }
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 7px;
}

.model-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 300px;
  padding: 5px 8px;
  border: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;
  .mono();
  letter-spacing: 0.02em;
  .truncate();

  .dot {
    width: 5px;
    height: 5px;
    background: var(--faint);
    flex: none;
  }

  &.ok .dot {
    background: var(--good);
  }

  &.warn .dot {
    background: var(--warn);
  }
}

.model-text {
  .truncate();
}

.nav-btn {
  padding: 7px 9px;
  font-size: 11px;
}

@media (max-width: @bp-md) {
  .edge-rail {
    padding: 5px 15px;

    span:nth-child(2) {
      display: none;
    }
  }

  .topbar {
    padding: 9px 15px;
  }

  .brand-text small,
  .nav-btn span {
    display: none;
  }

  .model-pill {
    max-width: 160px;
  }

  .model-text {
    font-size: 8.5px;
  }
}

@media (max-width: @bp-sm) {
  .model-pill {
    display: none;
  }
}
</style>
