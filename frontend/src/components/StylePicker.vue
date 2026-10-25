<script setup>
import { computed } from "vue";

import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { STYLE_OPTIONS, styleLabel } from "../theme";
import { closeStyles, setStyle, state, toggleTheme } from "../store";

const currentLabel = computed(() => styleLabel(state.style));

const previewFonts = {
  aurora: '"Segoe UI", "PingFang SC", sans-serif',
  paper: '"Songti SC", "Noto Serif SC", Georgia, serif',
  terminal: '"Cascadia Code", "JetBrains Mono", Consolas, monospace',
  neon: '"Arial Black", "Segoe UI", "PingFang SC", sans-serif',
  sakura: '"Avenir Next", "PingFang SC", sans-serif',
};

function previewVars(option) {
  const palette = option.colors[state.theme] || option.colors.dark;
  return {
    "--pv-bg": palette.bg,
    "--pv-panel": palette.panel,
    "--pv-text": palette.text,
    "--pv-accent": palette.accent,
    "--pv-accent2": palette.accent2,
    "--pv-font": previewFonts[option.key],
  };
}
</script>

<template>
  <BaseDrawer
    :open="state.drawers.styles"
    title="换一种页面风格"
    subtitle="配色、字体、背景和组件细节会整套切换；深色 / 浅色仍然可以单独选择。"
    wide
    @close="closeStyles"
  >
    <div class="style-grid">
      <button
        v-for="option in STYLE_OPTIONS"
        :key="option.key"
        class="style-card"
        :class="{ active: state.style === option.key }"
        type="button"
        :aria-pressed="state.style === option.key"
        @click="setStyle(option.key)"
      >
        <div class="preview" :style="previewVars(option)">
          <div class="pv-nav">
            <span class="pv-mark"></span>
            <span class="pv-brand">RepoLens</span>
            <span class="pv-nav-line"></span>
            <span class="pv-nav-dot"></span>
          </div>
          <div class="pv-title">看清技术栈</div>
          <div class="pv-panel">
            <div class="pv-chip-row">
              <span class="pv-chip">FastAPI</span>
              <span class="pv-chip alt">React</span>
            </div>
            <span class="pv-bar w1"></span>
            <span class="pv-bar w2"></span>
          </div>
          <div class="pv-tags">
            <span>Agent</span>
            <span>Vue</span>
            <span>SSE</span>
          </div>
        </div>

        <div class="card-copy">
          <div class="card-title">
            <b>{{ option.label }}</b>
            <em>{{ option.en }}</em>
            <span class="mode-mini">{{ state.theme === "dark" ? "深色" : "浅色" }}</span>
          </div>
          <span class="card-tagline">{{ option.tagline }}</span>
        </div>
        <p class="card-desc">{{ option.description }}</p>

        <span v-if="state.style === option.key" class="active-check">
          <Icon name="check" :size="12" /> 当前使用
        </span>
      </button>
    </div>

    <div class="style-foot">
      <div>
        <b>当前：{{ currentLabel }}</b>
        <span> · {{ state.theme === "dark" ? "深色模式" : "浅色模式" }}</span>
        <small>所有风格都保留完整功能与信息密度。</small>
      </div>
      <button class="btn" type="button" @click="toggleTheme">
        <Icon :name="state.theme === 'dark' ? 'sun' : 'moon'" :size="14" />
        切换{{ state.theme === "dark" ? "浅色" : "深色" }}
      </button>
    </div>
  </BaseDrawer>
</template>

<style scoped lang="less">
.style-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.style-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);
  text-align: left;
  transition: border-color 0.18s, transform 0.18s @ease-out, box-shadow 0.18s;
  .focus-ring();

  &:hover {
    transform: translateY(-2px);
    border-color: var(--accent-line);
    box-shadow: var(--shadow-soft);
  }

  &.active {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }
}

.preview {
  position: relative;
  min-height: 154px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--pv-text) 14%, transparent);
  background: var(--pv-bg);
  color: var(--pv-text);
  font-family: var(--pv-font);
  overflow: hidden;
  transition: background 0.25s, color 0.25s;

  &::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(circle at 8% 0%, color-mix(in srgb, var(--pv-accent) 24%, transparent), transparent 48%),
      radial-gradient(circle at 100% 100%, color-mix(in srgb, var(--pv-accent2) 20%, transparent), transparent 48%);
    opacity: 0.65;
  }
}

.pv-nav,
.pv-title,
.pv-panel,
.pv-tags {
  position: relative;
  z-index: 1;
}

.pv-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  font-size: 9px;
  letter-spacing: 0.4px;
}

.pv-mark {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: linear-gradient(135deg, var(--pv-accent), var(--pv-accent2));
  box-shadow: 0 0 8px color-mix(in srgb, var(--pv-accent) 50%, transparent);
}

.pv-brand {
  font-weight: 700;
}

.pv-nav-line {
  flex: 1;
  height: 1px;
  background: color-mix(in srgb, var(--pv-text) 18%, transparent);
}

.pv-nav-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--pv-text) 32%, transparent);
}

.pv-title {
  width: fit-content;
  font-size: 25px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(110deg, var(--pv-accent), var(--pv-accent2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.pv-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--pv-text) 12%, transparent);
  background: color-mix(in srgb, var(--pv-panel) 80%, transparent);
}

.pv-chip-row {
  display: flex;
  gap: 4px;
}

.pv-chip {
  padding: 1px 5px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--pv-accent) 35%, transparent);
  color: var(--pv-accent);
  font-size: 7px;
  line-height: 1.5;

  &.alt {
    border-color: color-mix(in srgb, var(--pv-accent2) 35%, transparent);
    color: var(--pv-accent2);
  }
}

.pv-bar {
  display: block;
  height: 4px;
  border-radius: 2px;
  background: color-mix(in srgb, var(--pv-text) 12%, transparent);

  &.w1 {
    width: 88%;
  }

  &.w2 {
    width: 62%;
  }
}

.pv-tags {
  display: flex;
  gap: 6px;
  margin-top: 9px;
  color: color-mix(in srgb, var(--pv-text) 48%, transparent);
  font-size: 7px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.card-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  display: flex;
  align-items: baseline;
  gap: 7px;

  b {
    font-size: 14px;
    color: var(--text);
  }

  em {
    color: var(--faint);
    font-size: 10px;
    font-style: normal;
    letter-spacing: 0.8px;
    text-transform: uppercase;
  }
}

.mode-mini {
  margin-left: auto;
  padding: 1px 5px;
  border-radius: @radius-pill;
  background: var(--panel-soft);
  color: var(--faint);
  font-size: 9px;
}

.card-tagline {
  color: var(--accent);
  font-size: 10.5px;
}

.card-desc {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.active-check {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 7px;
  border-radius: @radius-pill;
  background: var(--accent);
  color: #04121a;
  font-size: 9px;
  font-weight: 700;
  box-shadow: 0 4px 14px -4px var(--accent);
}

.style-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed var(--line);
  color: var(--muted);
  font-size: 11.5px;

  b {
    color: var(--text);
  }

  small {
    display: block;
    margin-top: 2px;
    color: var(--faint);
    font-size: 10.5px;
  }
}

@media (max-width: @bp-sm) {
  .style-grid {
    grid-template-columns: 1fr;
  }

  .preview {
    min-height: 138px;
  }

  .style-foot {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
