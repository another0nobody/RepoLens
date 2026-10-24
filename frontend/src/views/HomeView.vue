<script setup>
import { computed, ref } from "vue";

import { detectSource, truncate } from "../utils";
import { openConcepts, startAnalysis, state } from "../store";
import Icon from "../components/Icon.vue";

const input = ref(state.source || "");
const focused = ref(false);
const mouse = ref({ x: 50, y: 28 });
const kind = computed(() => detectSource(input.value));
const canStart = computed(() => input.value.trim().length > 0);

const heroStyle = computed(() => ({
  "--mx": `${mouse.value.x}%`,
  "--my": `${mouse.value.y}%`,
}));

function trackMouse(event) {
  const rect = event.currentTarget.getBoundingClientRect();
  mouse.value = {
    x: Math.round(((event.clientX - rect.left) / rect.width) * 100),
    y: Math.round(((event.clientY - rect.top) / rect.height) * 100),
  };
}

function submit() {
  if (!canStart.value) return;
  startAnalysis(input.value);
}

function useExample(example) {
  input.value = example.value;
  document.querySelector("#repo-source")?.focus();
}

function onKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    submit();
  }
}
</script>

<template>
  <section class="home">
    <div class="hero" :style="heroStyle" @mousemove="trackMouse">
      <div class="hero-glow" aria-hidden="true"></div>

      <p class="eyebrow">
        <span class="eyebrow-dot"></span>
        YOUR FIRST LANGCHAIN AGENT PROJECT
      </p>
      <h1>
        输入一个仓库，<br />
        <span class="grad">看清它的技术栈</span>
      </h1>
      <p class="lede">
        本地目录或 GitHub 地址都可以。Agent 会扫描依赖与 import，核实每一项技术被哪些模块使用，
        再生成一份可以继续追问的中文报告。
      </p>

      <div class="hero-badges">
        <span class="tag good"><Icon name="terminal" :size="13" /> 本地只读扫描</span>
        <span class="tag"><Icon name="layers" :size="13" /> 模块级定位</span>
        <span class="tag"><Icon name="spark" :size="13" /> LangChain Agent</span>
      </div>
    </div>

    <div class="input-card" :class="{ focused }">
      <div class="input-row">
        <span class="input-icon" aria-hidden="true">
          <Icon name="terminal" :size="18" />
        </span>
        <input
          id="repo-source"
          v-model="input"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder="C:\code\my-project   或   https://github.com/owner/repo"
          aria-label="代码仓库路径或 GitHub 地址"
          @focus="focused = true"
          @blur="focused = false"
          @keydown="onKeydown"
        />
        <button class="btn btn-primary analyze-btn" type="button" :disabled="state.analyzing || !canStart" @click="submit">
          <span v-if="state.analyzing" class="btn-spinner"></span>
          <template v-else>
            开始分析
            <Icon name="arrowRight" :size="16" />
          </template>
        </button>
      </div>

      <div class="input-info">
        <span class="kind-pill" :class="kind.kind">
          <Icon :name="kind.kind === 'github' ? 'github' : kind.kind === 'ambiguous' ? 'code' : 'folder'" :size="12" />
          {{ kind.label }}
        </span>
        <span class="shortcut"><kbd>Enter</kbd> 快速开始</span>
        <span class="input-note">只读扫描 · 密钥自动脱敏</span>
      </div>

      <div v-if="state.examples.length" class="examples">
        <button
          v-for="example in state.examples"
          :key="example.value"
          class="chip example-chip"
          type="button"
          :title="example.description"
          @click="useExample(example)"
        >
          <Icon :name="example.kind === 'github' ? 'github' : 'folder'" :size="12" />
          <b>{{ example.label }}</b>
          <span v-if="example.description" class="example-desc">{{ truncate(example.description, 34) }}</span>
        </button>
      </div>
    </div>

    <div class="step-strip">
      <article v-for="(step, index) in [
        { no: '01', title: '扫描事实', text: '遍历目录、统计语言、解析 requirements.txt / package.json / pom.xml，提取 import 语句。' },
        { no: '02', title: 'Agent 核实', text: '大模型拿着事实清单，逐项核实技术，定位每个技术被哪些模块使用。' },
        { no: '03', title: '生成报告', text: '合并成技术栈全景、模块地图、架构解读、风险与学习路径，并支持继续追问。' },
      ]" :key="step.no" class="step-card">
        <span class="step-no">{{ step.no }}</span>
        <h3>{{ step.title }}</h3>
        <p>{{ step.text }}</p>
        <span v-if="index < 2" class="step-arrow" aria-hidden="true">→</span>
      </article>
    </div>

    <div class="feature-grid">
      <article class="feature-card">
        <span class="feature-icon"><Icon name="layers" :size="18" /></span>
        <h3>技术栈全景</h3>
        <p>按前后端、数据库、AI、基础设施等分类展示，标注版本、证据和置信度。</p>
      </article>
      <article class="feature-card">
        <span class="feature-icon"><Icon name="code" :size="18" /></span>
        <h3>模块级定位</h3>
        <p>精确到文件与行号：哪个模块 import 了它、在项目里承担什么角色。</p>
      </article>
      <article class="feature-card">
        <span class="feature-icon"><Icon name="spark" :size="18" /></span>
        <h3>报告追问</h3>
        <p>基于这份报告继续问「Redis 用在哪里」「先读哪个文件」，带多轮记忆。</p>
      </article>
      <article class="feature-card">
        <span class="feature-icon"><Icon name="book" :size="18" /></span>
        <h3>知识点透明</h3>
        <p>Tool、结构化输出、中间件、人机协同、记忆，每个能力都标注对应教程章节。</p>
      </article>
    </div>

    <p class="home-foot">
      这个项目把教程第 5~9 章的 Agent 知识点串了起来。
      <button class="link-btn" type="button" @click="openConcepts">看看每个功能用了什么 →</button>
    </p>
  </section>
</template>

<style scoped lang="less">
.home {
  padding-top: 28px;
}

.hero {
  position: relative;
  max-width: 900px;
  padding: 26px 0 30px;
  overflow: hidden;

  .hero-glow {
    position: absolute;
    inset: -80px -60px;
    background: radial-gradient(circle at var(--mx) var(--my), var(--hero-glow), transparent 46%);
    pointer-events: none;
    z-index: -1;
    transition: background 0.15s ease-out;
  }
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 20px;
  color: var(--accent);
  font-size: 11px;
  letter-spacing: 2.2px;
  text-transform: uppercase;
}

.eyebrow-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 14px var(--accent);
}

h1 {
  margin: 0;
  font-size: clamp(40px, 6.2vw, 72px);
  line-height: 1.04;
  letter-spacing: -2.4px;
  font-weight: 720;
}

.grad {
  .gradient-text();
}

.lede {
  max-width: 760px;
  margin: 22px 0 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.75;
}

.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
}

.input-card {
  position: relative;
  margin-top: 30px;
  padding: 16px;
  border-radius: @radius-xl;
  background: linear-gradient(160deg, color-mix(in srgb, var(--panel-solid) 88%, transparent), var(--panel));
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;

  &.focused {
    border-color: var(--accent-line);
    box-shadow: 0 0 0 4px var(--accent-soft), var(--shadow);
  }
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  color: var(--accent);
  flex: none;
}

#repo-source {
  flex: 1;
  min-width: 0;
  padding: 12px 2px;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 16px;
  .mono();

  &::placeholder {
    color: var(--faint);
    font-family: @font-sans;
  }
}

.analyze-btn {
  min-width: 132px;
  padding: 12px 18px;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(4, 18, 26, 0.25);
  border-top-color: #04121a;
  animation: spin 0.8s linear infinite;
}

.input-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding: 10px 6px 2px;
  color: var(--faint);
  font-size: 11.5px;
}

.kind-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: @radius-pill;
  border: 1px solid var(--line);
  background: var(--panel-soft);
  color: var(--muted);

  &.github {
    color: var(--accent-2);
    border-color: color-mix(in srgb, var(--accent-2) 30%, transparent);
  }

  &.ambiguous {
    color: var(--warn);
    border-color: color-mix(in srgb, var(--warn) 30%, transparent);
  }

  &.local {
    color: var(--accent);
    border-color: var(--accent-line);
  }
}

.shortcut {
  display: inline-flex;
  align-items: center;
  gap: 4px;

  kbd {
    .mono();
    padding: 1px 5px;
    border-radius: 5px;
    border: 1px solid var(--line);
    background: var(--panel-soft);
    color: var(--faint);
    font-size: 10px;
  }
}

.input-note {
  margin-left: auto;
}

.examples {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 12px;
}

.example-chip {
  gap: 6px;
  font-size: 11.5px;
  max-width: 100%;

  b {
    color: var(--text);
    font-weight: 600;
  }
}

.example-desc {
  color: var(--faint);
  max-width: 190px;
  .truncate();
}

.step-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin: 34px 0 20px;
}

.step-card {
  position: relative;
  padding: 20px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(140deg, var(--accent-soft), transparent 55%);
    pointer-events: none;
  }

  h3 {
    margin: 8px 0 6px;
    font-size: 15px;
  }

  p {
    margin: 0;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.7;
  }
}

.step-no {
  .mono();
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 2px;
}

.step-arrow {
  position: absolute;
  right: 14px;
  top: 18px;
  color: var(--faint);
  font-size: 14px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.feature-card {
  padding: 19px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);
  .card-lift();

  h3 {
    margin: 10px 0 5px;
    font-size: 14.5px;
  }

  p {
    margin: 0;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.7;
  }
}

.feature-icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-line);
}

.home-foot {
  margin: 30px 0 0;
  text-align: center;
  color: var(--faint);
  font-size: 12.5px;
}

@media (max-width: @bp-lg) {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: @bp-md) {
  .home {
    padding-top: 6px;
  }

  .lede {
    font-size: 15px;
  }

  .input-row {
    flex-wrap: wrap;
  }

  #repo-source {
    flex-basis: 100%;
  }

  .analyze-btn {
    width: 100%;
  }

  .input-note {
    margin-left: 0;
  }

  .step-strip,
  .feature-grid {
    grid-template-columns: 1fr;
  }

  .step-arrow {
    display: none;
  }
}
</style>
