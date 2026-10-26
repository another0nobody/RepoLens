<script setup>
import { computed, ref } from "vue";

import { detectSource, truncate } from "../utils";
import { openConcepts, startAnalysis, state } from "../store";
import Icon from "../components/Icon.vue";

const input = ref(state.source || "");
const focused = ref(false);
const kind = computed(() => detectSource(input.value));
const canStart = computed(() => input.value.trim().length > 0);

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
    <div class="home-grid">
      <div class="hero">
        <h1><span>REPO</span><span class="accent">LENS</span></h1>
        <p class="sub">把仓库读成一份可核对的技术档案。</p>
        <p class="lede">
          输入本地目录或 GitHub 地址。Agent 扫描事实、逐项核实技术被哪些模块使用，
          最后生成一份可以继续追问的中文报告。
        </p>
        <div class="specimen-meta">
          <span>SPECIMEN / 001</span>
          <span>LATIN DISPLAY 96 / TEXT 15</span>
        </div>
      </div>

      <aside class="home-index" aria-label="报告能力">
        <div class="index-head">
          <span>INDEX</span><span>03 ENTRIES</span>
        </div>
        <div class="index-row">
          <span class="no">01</span>
          <div><b>技术栈全景</b><p>版本、职责、证据、置信度，一项一项核对。</p></div>
        </div>
        <div class="index-row">
          <span class="no">02</span>
          <div><b>模块定位</b><p>精确到文件与行号，并说明这个文件大概在做什么。</p></div>
        </div>
        <div class="index-row">
          <span class="no">03</span>
          <div><b>技术深挖</b><p>优势、难点、相似方案、为什么选它；事实与推断分开。</p></div>
        </div>
        <button class="index-link" type="button" @click="openConcepts">
          查看能力对应的教程知识点 <Icon name="arrowRight" :size="13" />
        </button>
      </aside>
    </div>

    <div class="source-block">
      <div class="source-kicker">
        <span>SOURCE / 输入仓库</span>
        <span class="kind-pill" :class="kind.kind">
          <Icon :name="kind.kind === 'github' ? 'github' : kind.kind === 'ambiguous' ? 'code' : 'folder'" :size="11" />
          {{ kind.label }}
        </span>
      </div>
      <div class="source-line" :class="{ focused }">
        <span class="source-mark" aria-hidden="true">→</span>
        <input
          id="repo-source"
          v-model="input"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder="本地路径或 GitHub 地址"
          aria-label="代码仓库路径或 GitHub 地址"
          @focus="focused = true"
          @blur="focused = false"
          @keydown="onKeydown"
        />
        <button class="btn btn-primary analyze-btn" type="button" :disabled="state.analyzing || !canStart" @click="submit">
          <span v-if="state.analyzing" class="btn-spinner"></span>
          <template v-else>开始分析</template>
        </button>
      </div>
      <div class="source-meta">
        <span>只读扫描</span>
        <span>密钥自动脱敏</span>
        <span>不修改仓库</span>
        <span class="enter-hint"><kbd>Enter</kbd> 快速开始</span>
      </div>

      <div v-if="state.examples.length" class="examples">
        <span class="examples-label">EXAMPLES</span>
        <button
          v-for="example in state.examples"
          :key="example.value"
          class="example-link"
          type="button"
          :title="example.description"
          @click="useExample(example)"
        >
          <b>{{ example.label }}</b>
          <span v-if="example.description">{{ truncate(example.description, 26) }}</span>
        </button>
      </div>
    </div>

    <p class="home-foot">
      <span>RepoLens / 一个用 LangChain Agent 做的仓库技术档案工具</span>
      <span>扫描在本地完成；只有必要事实会发送给模型。</span>
    </p>
  </section>
</template>

<style scoped lang="less">
.home {
  max-width: 1140px;
  padding-top: 10px;
}

.home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  gap: 52px;
  align-items: start;
}

.hero {
  min-width: 0;
}

h1 {
  display: flex;
  flex-direction: column;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(72px, 10.5vw, 96px);
  font-weight: 400;
  line-height: 0.82;
  letter-spacing: -0.04em;

  .accent {
    color: var(--accent);
    font-style: italic;
    padding-left: 0.34em;
  }
}

.sub {
  max-width: 34ch;
  margin: 28px 0 0;
  padding-top: 12px;
  border-top: 1px solid var(--line-strong);
  font-family: var(--font-display);
  font-size: clamp(19px, 2vw, 25px);
  line-height: 1.5;
  letter-spacing: -0.02em;
}

.lede {
  max-width: 48ch;
  margin: 16px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.85;
}

.specimen-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 46px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.1em;
}

.home-index {
  border-top: 1px solid var(--line-strong);
}

.index-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.1em;
}

.index-row {
  display: grid;
  grid-template-columns: 30px 1fr;
  gap: 8px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);

  .no {
    color: var(--faint);
    .mono();
    font-size: 9px;
  }

  b {
    display: block;
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 400;
    letter-spacing: -0.02em;
  }

  p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.65;
  }
}

.index-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font-size: 10.5px;
  text-align: left;

  &:hover {
    text-decoration: underline;
    text-underline-offset: 3px;
  }
}

.source-block {
  margin-top: 62px;
}

.source-kicker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--faint);
  .mono();
  font-size: 9px;
  letter-spacing: 0.08em;
}

.kind-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 8.5px;
  letter-spacing: 0;

  &.github {
    color: var(--muted);
  }

  &.local {
    color: var(--good);
    border-color: color-mix(in srgb, var(--good) 50%, var(--line));
  }

  &.ambiguous {
    color: var(--warn);
    border-color: var(--warn);
  }
}

.source-line {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0 8px;
  border-bottom: 2px solid var(--line-strong);
  transition: border-color 0.16s;

  &.focused {
    border-color: var(--accent);
  }
}

.source-mark {
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 22px;
  flex: none;
}

#repo-source {
  flex: 1;
  min-width: 0;
  padding: 8px 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text);
  font-size: 18px;
  .mono();

  &::placeholder {
    color: var(--faint);
    font-family: var(--font-ui);
    font-size: 14px;
  }
}

.analyze-btn {
  flex: none;
  min-width: 116px;
  padding: 11px 18px;
  font-size: 12px;
}

.btn-spinner {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(255, 249, 237, 0.3);
  border-top-color: #fff9ed;
  animation: spin 0.8s linear infinite;
}

.source-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  padding-top: 8px;
  color: var(--faint);
  font-size: 9.5px;

  .enter-hint {
    margin-left: auto;
  }

  kbd {
    .mono();
    padding: 1px 4px;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 8.5px;
  }
}

.examples {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 7px 18px;
  margin-top: 18px;
  padding-top: 9px;
  border-top: 1px solid var(--line);
}

.examples-label {
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.1em;
}

.example-link {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  max-width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-size: 10px;
  text-align: left;

  b {
    color: var(--text);
    font-weight: 500;
  }

  span {
    max-width: 180px;
    .truncate();
    color: var(--faint);
  }

  &:hover b {
    color: var(--accent);
  }
}

.home-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin: 54px 0 0;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;
  letter-spacing: 0.02em;
}

@media (max-width: @bp-lg) {
  .home-grid {
    grid-template-columns: minmax(0, 1.2fr) minmax(250px, 0.8fr);
    gap: 30px;
  }

  h1 {
    font-size: clamp(64px, 9vw, 86px);
  }
}

@media (max-width: @bp-md) {
  .home {
    padding-top: 4px;
  }

  .home-grid {
    grid-template-columns: 1fr;
    gap: 34px;
  }

  h1 {
    font-size: clamp(58px, 17vw, 78px);
  }

  .sub {
    margin-top: 22px;
    font-size: 20px;
  }

  .specimen-meta {
    margin-top: 28px;
  }

  .source-block {
    margin-top: 38px;
  }

  .source-line {
    flex-wrap: wrap;
  }

  #repo-source {
    flex-basis: calc(100% - 36px);
    font-size: 15px;
  }

  .analyze-btn {
    width: 100%;
  }

  .source-meta .enter-hint {
    margin-left: 0;
  }

  .home-foot {
    margin-top: 34px;
    flex-direction: column;
    gap: 5px;
  }
}
</style>
