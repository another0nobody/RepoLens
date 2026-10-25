<script setup>
import { computed } from "vue";

import BrandLogo from "./BrandLogo.vue";
import Icon from "./Icon.vue";

const props = defineProps({
  health: { type: Object, default: null },
  theme: { type: String, default: "dark" },
});
const emit = defineEmits(["brand", "styles", "history", "concepts", "toggle-theme"]);

const modelLabel = computed(() => {
  if (!props.health) return "检测环境中…";
  return props.health.ai_available ? props.health.model : "未配置模型 · 仅规则扫描";
});

const modelClass = computed(() => (!props.health ? "" : props.health.ai_available ? "ok" : "warn"));
</script>

<template>
  <header class="topbar-wrap">
    <div class="topbar">
      <button class="brand" type="button" aria-label="回到首页" @click="emit('brand')">
        <BrandLogo :size="40" />
        <span class="brand-text">
          <strong>RepoLens</strong>
          <small>技术栈侦探</small>
        </span>
      </button>

      <div class="topbar-right">
        <span class="model-pill" :class="modelClass" :title="health ? '当前使用的大模型' : '正在连接后端'">
          <span class="dot"></span>
          <span class="model-text">{{ modelLabel }}</span>
        </span>
        <button class="btn btn-ghost nav-btn" type="button" title="切换页面风格" @click="emit('styles')">
          <Icon name="palette" :size="16" />
          <span>风格</span>
        </button>
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
  .glass();
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  transition: background 0.3s ease, border-color 0.3s ease;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: @space-5;
  max-width: 1280px;
  margin: 0 auto;
  padding: 14px 26px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  border: 0;
  background: none;
  padding: 0;
  text-align: left;
  .focus-ring();

  &:hover :deep(.brand-mark) {
    transform: rotate(-4deg) scale(1.03);
  }
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;

  strong {
    font-size: 17px;
    letter-spacing: 0.4px;
  }

  small {
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 1.6px;
  }
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 300px;
  padding: 7px 12px;
  border-radius: @radius-pill;
  border: 1px solid var(--line);
  background: var(--panel-soft);
  color: var(--muted);
  font-size: 12px;
  .truncate();

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--faint);
    flex: none;
  }

  &.ok .dot {
    background: var(--good);
    box-shadow: 0 0 12px var(--good);
    animation: pulse 2.4s infinite;
  }

  &.warn .dot {
    background: var(--warn);
    box-shadow: 0 0 12px var(--warn);
  }
}

.model-text {
  .truncate();
}

.nav-btn {
  padding: 8px 11px;
  font-size: 12.5px;
}

@media (max-width: @bp-md) {
  .topbar {
    padding: 11px 15px;
  }

  .brand-text small {
    display: none;
  }

  .model-pill {
    max-width: 160px;
  }

  .model-text {
    font-size: 11px;
  }

  .nav-btn span {
    display: none;
  }
}

@media (max-width: @bp-sm) {
  .model-pill {
    display: none;
  }
}
</style>
