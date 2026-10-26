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
    <div class="terrain" aria-hidden="true">
      <svg viewBox="0 0 1400 760" preserveAspectRatio="none">
        <path class="open" d="M-40 210 C130 90, 250 180, 360 120 S570 70, 700 170 S930 260, 1070 130 S1290 40, 1440 120 L1440 330 C1260 300, 1120 420, 940 360 S620 260, 430 410 S120 420, -40 350 Z" />
        <path class="marsh" d="M760 500 C840 430, 980 450, 1050 520 S1090 660, 980 700 S760 640, 760 500 Z" />
        <path class="contour" d="M-30 600 C180 520, 300 640, 460 560 S760 470, 920 560 S1190 660, 1430 560" />
        <path class="contour" d="M-20 545 C160 470, 290 570, 430 505 S720 430, 900 500 S1150 600, 1430 500" />
        <path class="contour" d="M-20 490 C140 420, 270 510, 400 455 S690 390, 860 450 S1110 550, 1430 440" />
        <path class="contour" d="M100 330 C230 280, 330 350, 450 300 S700 250, 820 300 S1020 380, 1130 300" />
        <path class="contour" d="M60 275 C190 230, 300 300, 430 245 S680 195, 800 245 S980 320, 1080 245" />
        <path class="course" d="M170 620 C250 510, 520 560, 610 430 S760 290, 1010 330 S1190 430, 1260 360" />
        <circle class="control" cx="170" cy="620" r="7" />
        <circle class="control" cx="610" cy="430" r="7" />
        <circle class="control active" cx="1010" cy="330" r="8" />
      </svg>
    </div>

    <div class="hero">
      <h1>找到<br /><span>技术路线</span></h1>
      <p class="lede">
        仓库不是一张文件清单，而是一片地形。RepoLens 先测出事实，再由 Agent 标出技术、模块与阅读顺序。
      </p>
      <div class="hero-meta">
        <span>FIELD NOTE / 001</span>
        <span>START → SCAN → AGENT → PROOF</span>
      </div>
    </div>

    <div class="start-box">
      <div class="start-head">
        <span>START / 输入仓库</span>
        <span class="kind-pill" :class="kind.kind">
          <Icon :name="kind.kind === 'github' ? 'github' : kind.kind === 'ambiguous' ? 'code' : 'folder'" :size="11" />
          {{ kind.label }}
        </span>
      </div>
      <div class="start-row" :class="{ focused }">
        <span class="start-mark" aria-hidden="true">◎</span>
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
      <div class="start-meta">
        <span>只读扫描</span>
        <span>密钥自动脱敏</span>
        <span>不修改仓库</span>
        <span class="enter"><kbd>Enter</kbd> 开始</span>
      </div>
      <div v-if="state.examples.length" class="examples">
        <span class="examples-label">TRAILHEADS</span>
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

    <div class="legs-block">
      <div class="legs-head">
        <span>COURSE / 03 LEGS</span>
        <span>FOLLOW THE PURPLE LINE</span>
      </div>
      <div class="course-line" aria-hidden="true"></div>
      <div class="legs">
        <article class="leg">
          <span class="leg-code">01</span>
          <h2>扫描事实</h2>
          <p>目录、语言、清单、import；先让证据落地。</p>
          <span class="leg-state">SCAN</span>
        </article>
        <article class="leg">
          <span class="leg-code">02</span>
          <h2>Agent 核实</h2>
          <p>拿着事实清单逐项核实每项技术被哪些模块使用。</p>
          <span class="leg-state">AGENT</span>
        </article>
        <article class="leg">
          <span class="leg-code">03</span>
          <h2>报告证据</h2>
          <p>技术栈、模块地图、架构、风险与学习路径；可继续追问。</p>
          <span class="leg-state">PROOF</span>
        </article>
      </div>
    </div>

    <p class="home-foot">
      <span>RepoLens / 一个用 LangChain Agent 做的仓库技术地形图</span>
      <button class="link-btn" type="button" @click="openConcepts">查看每个能力对应的教程知识点 →</button>
    </p>
  </section>
</template>

<style scoped lang="less">
.home {
  position: relative;
  max-width: 1160px;
  padding-top: 26px;
  isolation: isolate;
  overflow: hidden;
}

.terrain {
  position: absolute;
  z-index: -1;
  top: -40px;
  left: -8vw;
  right: -8vw;
  height: 620px;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.75;

  svg {
    width: 100%;
    height: 100%;
  }

  .open {
    fill: color-mix(in srgb, var(--accent-3) 12%, transparent);
  }

  .marsh {
    fill: color-mix(in srgb, var(--accent) 7%, transparent);
  }

  .contour {
    fill: none;
    stroke: color-mix(in srgb, var(--accent-3) 45%, transparent);
    stroke-width: 0.8;
  }

  .course {
    fill: none;
    stroke: var(--accent);
    stroke-width: 2;
    stroke-dasharray: 8 5;
    opacity: 0.7;
  }

  .control {
    fill: var(--bg);
    stroke: var(--accent);
    stroke-width: 2;
  }

  .control.active {
    fill: var(--accent);
  }
}

.hero {
  max-width: 820px;
  padding-top: 20px;
}

h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(64px, 9.5vw, 96px);
  font-weight: 700;
  line-height: 0.84;
  letter-spacing: -0.04em;
  text-transform: uppercase;

  span {
    display: inline-block;
    color: var(--text);
    padding-bottom: 2px;
    border-bottom: 4px solid var(--accent);
  }
}

.lede {
  max-width: 52ch;
  margin: 26px 0 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.8;
}

.hero-meta {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  max-width: 620px;
  margin-top: 30px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.08em;
}

.start-box {
  max-width: 820px;
  margin-top: 30px;
  border: 1px solid var(--line-strong);
  background: color-mix(in srgb, var(--panel) 92%, transparent);
}

.start-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 11px;
  border-bottom: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8.5px;
  letter-spacing: 0.08em;
}

.kind-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 8px;
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

.start-row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 11px;

  &.focused {
    box-shadow: inset 0 -2px 0 var(--accent);
  }
}

.start-mark {
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 22px;
  flex: none;
}

#repo-source {
  flex: 1;
  min-width: 0;
  padding: 7px 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text);
  font-size: 16px;
  .mono();

  &::placeholder {
    color: var(--faint);
    font-family: var(--font-ui);
    font-size: 13px;
  }
}

.analyze-btn {
  flex: none;
  min-width: 110px;
  padding: 10px 15px;
  font-size: 11px;
}

.btn-spinner {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(253, 250, 239, 0.3);
  border-top-color: #fdfaef;
  animation: spin 0.8s linear infinite;
}

.start-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding: 8px 11px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;

  .enter {
    margin-left: auto;
  }

  kbd {
    .mono();
    padding: 1px 4px;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 8px;
  }
}

.examples {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 8px 11px;
  border-top: 1px solid var(--line);
}

.examples-label {
  color: var(--faint);
  .mono();
  font-size: 7.5px;
  letter-spacing: 0.08em;
}

.example-link {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  max-width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-size: 9.5px;
  text-align: left;

  b {
    color: var(--text);
    font-weight: 500;
  }

  span {
    max-width: 170px;
    .truncate();
    color: var(--faint);
  }

  &:hover b {
    color: var(--accent);
  }
}

.legs-block {
  position: relative;
  max-width: 980px;
  margin-top: 56px;
}

.legs-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line-strong);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.08em;
}

.course-line {
  position: absolute;
  top: 39px;
  left: 28px;
  right: 28px;
  height: 1px;
  background: var(--accent);
  opacity: 0.7;
}

.legs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.leg {
  position: relative;
  padding-top: 24px;

  &::before {
    content: "";
    position: absolute;
    top: -4px;
    left: 22px;
    width: 9px;
    height: 9px;
    border: 2px solid var(--accent);
    border-radius: 50%;
    background: var(--bg);
  }

  &:last-child::before {
    background: var(--accent);
  }

  .leg-code {
    color: var(--accent);
    .mono();
    font-size: 9px;
  }

  h2 {
    margin: 6px 0 0;
    font-family: var(--font-display);
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  p {
    max-width: 30ch;
    margin: 7px 0 0;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.7;
  }

  .leg-state {
    display: inline-block;
    margin-top: 12px;
    color: var(--faint);
    .mono();
    font-size: 8px;
    letter-spacing: 0.1em;
  }
}

.home-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  max-width: 980px;
  margin: 54px 0 0;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;
}

.link-btn {
  border: 0;
  background: none;
  color: var(--accent);
  padding: 0;
  font-size: inherit;
}

@media (max-width: @bp-lg) {
  h1 {
    font-size: clamp(62px, 9vw, 92px);
  }

  .start-box,
  .hero {
    max-width: 740px;
  }
}

@media (max-width: @bp-md) {
  .home {
    padding-top: 4px;
  }

  .terrain {
    top: -20px;
    height: 480px;
  }

  h1 {
    font-size: clamp(54px, 16vw, 82px);
  }

  .lede {
    font-size: 13px;
  }

  .hero-meta {
    margin-top: 22px;
    flex-direction: column;
    gap: 5px;
  }

  .start-box {
    margin-top: 24px;
  }

  .start-row {
    flex-wrap: wrap;
  }

  #repo-source {
    flex-basis: calc(100% - 32px);
    font-size: 14px;
  }

  .analyze-btn {
    width: 100%;
  }

  .start-meta .enter {
    margin-left: 0;
  }

  .legs-block {
    margin-top: 38px;
  }

  .course-line {
    display: none;
  }

  .legs {
    grid-template-columns: 1fr;
    gap: 0;
    border-top: 1px solid var(--line);
  }

  .leg {
    padding: 14px 0;
    border-bottom: 1px solid var(--line);

    &::before {
      top: 19px;
      left: 0;
    }

    .leg-code {
      padding-left: 18px;
    }

    h2,
    p,
    .leg-state {
      padding-left: 18px;
    }

    p {
      max-width: none;
    }
  }

  .home-foot {
    margin-top: 28px;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
