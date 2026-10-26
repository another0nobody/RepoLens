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
  <aside class="index-rail">
    <button class="brand" type="button" aria-label="回到首页" @click="emit('brand')">
      <span class="rail-mark" aria-hidden="true">RL</span>
      <span class="brand-text">
        <strong>RepoLens</strong>
        <small>TYPE INDEX / 001</small>
      </span>
    </button>

    <nav class="rail-nav" aria-label="主导航">
      <button class="rail-link" type="button" @click="emit('brand')">
        <span class="no">00</span><span>分析</span>
      </button>
      <button class="rail-link" type="button" @click="emit('history')">
        <span class="no">01</span><span>历史</span>
      </button>
      <button class="rail-link" type="button" @click="emit('concepts')">
        <span class="no">02</span><span>知识点</span>
      </button>
    </nav>

    <div class="rail-foot">
      <span class="model" :class="modelClass" :title="health ? '当前使用的大模型' : '正在连接后端'">
        <i></i>{{ modelLabel }}
      </span>
      <button
        class="theme-btn"
        type="button"
        :aria-label="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
        :title="theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
        @click="emit('toggle-theme')"
      >
        <Icon :name="theme === 'dark' ? 'sun' : 'moon'" :size="15" />
        <span>{{ theme === "dark" ? "LIGHT" : "DARK" }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped lang="less">
.index-rail {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  width: 212px;
  display: flex;
  flex-direction: column;
  padding: 24px 18px 18px;
  border-right: 1px solid var(--line-strong);
  background: var(--bg);
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  border: 0;
  background: none;
  padding: 0;
  color: var(--text);
  text-align: left;
  .focus-ring();

  &:hover .rail-mark {
    color: var(--accent);
    border-color: var(--accent);
  }
}

.rail-mark {
  display: grid;
  place-items: center;
  width: 31px;
  height: 31px;
  flex: none;
  border: 1px solid var(--line-strong);
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 14px;
  line-height: 1;
  transition: 0.16s;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;

  strong {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 400;
    line-height: 1;
    letter-spacing: -0.04em;
  }

  small {
    margin-top: 4px;
    color: var(--faint);
    font-family: var(--font-ui);
    font-size: 8px;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }
}

.rail-nav {
  display: flex;
  flex-direction: column;
  margin-top: 54px;
  border-top: 1px solid var(--line);
}

.rail-link {
  display: grid;
  grid-template-columns: 28px 1fr;
  align-items: baseline;
  gap: 8px;
  padding: 12px 0;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: none;
  color: var(--muted);
  font-size: 13px;
  text-align: left;
  transition: color 0.16s, padding 0.16s;
  .focus-ring();

  .no {
    color: var(--faint);
    font-family: var(--font-ui);
    font-size: 9px;
  }

  &:hover {
    color: var(--accent);
    padding-left: 3px;
  }
}

.rail-foot {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.model {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--faint);
  font-size: 8.5px;
  line-height: 1.4;
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

.theme-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: max-content;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 8.5px;
  letter-spacing: 0.1em;
  .focus-ring();

  &:hover {
    color: var(--accent);
  }
}

@media (max-width: @bp-md) {
  .index-rail {
    position: sticky;
    inset: auto;
    width: auto;
    flex-direction: row;
    align-items: center;
    padding: 9px 15px;
    border-right: 0;
    border-bottom: 1px solid var(--line-strong);
  }

  .brand-text strong {
    font-size: 18px;
  }

  .brand-text small {
    display: none;
  }

  .rail-nav {
    flex-direction: row;
    margin: 0 0 0 auto;
    border-top: 0;
    border-bottom: 0;
  }

  .rail-link {
    display: flex;
    gap: 4px;
    padding: 5px 8px;
    border-bottom: 0;
    font-size: 11px;

    .no {
      display: none;
    }

    &:hover {
      padding-left: 8px;
    }
  }

  .rail-foot {
    flex-direction: row;
    align-items: center;
    margin: 0 0 0 12px;
    padding: 0 0 0 12px;
    border-top: 0;
    border-left: 1px solid var(--line);
  }

  .model {
    display: none;
  }

  .theme-btn span {
    display: none;
  }
}
</style>
