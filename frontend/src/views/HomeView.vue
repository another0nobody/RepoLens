<script setup>
import { computed, ref } from "vue";

import { detectSource, truncate } from "../utils";
import { openConcepts, openHistory, startAnalysis, state } from "../store";
import Icon from "../components/Icon.vue";

const input = ref(state.source || "");
const focused = ref(false);
const kind = computed(() => detectSource(input.value));
const canStart = computed(() => input.value.trim().length > 0);
const recent = computed(() => (state.history || []).slice(0, 3));

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
    <div class="contact-hero">
      <div class="hero-copy">
        <h1>冲洗一个<br /><span>陌生仓库</span></h1>
        <p class="lede">
          输入本地目录或 GitHub 地址。Agent 先扫描事实，再逐项核实技术被哪些模块使用，
          最后给你一张可以继续追问的证据表。
        </p>

        <div class="source-card" :class="{ focused }">
          <div class="source-label">
            <span>ROLL / SOURCE</span>
            <span class="kind-pill" :class="kind.kind">
              <Icon :name="kind.kind === 'github' ? 'github' : kind.kind === 'ambiguous' ? 'code' : 'folder'" :size="11" />
              {{ kind.label }}
            </span>
          </div>

          <div class="input-row">
            <span class="input-mark" aria-hidden="true">↳</span>
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
              <template v-else>
                开始分析 <Icon name="arrowRight" :size="15" />
              </template>
            </button>
          </div>

          <div class="source-meta">
            <span><kbd>Enter</kbd> 开始</span>
            <span>密钥自动脱敏</span>
            <span>不修改仓库</span>
          </div>

          <div v-if="state.examples.length" class="examples">
            <button
              v-for="example in state.examples"
              :key="example.value"
              class="example-chip"
              type="button"
              :title="example.description"
              @click="useExample(example)"
            >
              <Icon :name="example.kind === 'github' ? 'github' : 'folder'" :size="11" />
              <b>{{ example.label }}</b>
              <span v-if="example.description">{{ truncate(example.description, 28) }}</span>
            </button>
          </div>
        </div>

        <div v-if="recent.length" class="recent-strip">
          <span class="strip-label">RECENT ROLLS</span>
          <button v-for="item in recent" :key="item.run_id" class="recent-item" type="button" @click="openHistory">
            <b>{{ item.repo_name || item.source }}</b>
            <span class="mono">{{ item.source }}</span>
          </button>
          <button class="strip-more" type="button" @click="openHistory">打开历史 →</button>
        </div>
      </div>

      <aside class="contact-strip" aria-label="分析流程">
        <div class="strip-head">
          <span>PROOF STRIP / 001</span>
          <span>3 FRAMES</span>
        </div>

        <article class="frame">
          <div class="frame-top"><span>01</span><span>SCAN</span></div>
          <div class="frame-art frame-art-scan" aria-hidden="true">
            <span></span><span></span><span></span><span></span>
            <span></span><span></span><span></span><span></span>
          </div>
          <h3>扫描事实</h3>
          <p>遍历目录、统计语言、解析依赖清单与 import。</p>
        </article>

        <article class="frame">
          <div class="frame-top"><span>02</span><span>AGENT</span></div>
          <div class="frame-art frame-art-agent" aria-hidden="true">
            <i></i><i></i><i></i><i></i><i></i>
          </div>
          <h3>核实证据</h3>
          <p>模型拿着事实清单逐项核实，定位每个技术被哪些模块使用。</p>
        </article>

        <article class="frame">
          <div class="frame-top"><span>03</span><span>PROOF</span></div>
          <div class="frame-art frame-art-proof" aria-hidden="true">
            <span></span><span></span><span></span>
            <b></b><b></b><b></b>
          </div>
          <h3>生成证据表</h3>
          <p>技术栈、模块地图、架构、风险与学习路径，全部可继续追问。</p>
        </article>

        <div class="strip-foot">
          <span>NO FRAME WITHOUT A SOURCE</span>
          <span>↗</span>
        </div>
      </aside>
    </div>

    <section class="proof-index" aria-label="报告能力">
      <div class="index-head">
        <span>INDEX / WHAT YOU GET</span>
        <span>03 PROOFS</span>
      </div>
      <table>
        <tbody>
          <tr>
            <th scope="row">技术栈全景</th>
            <td>按类别展示技术、版本、职责、证据和置信度。</td>
            <td class="mono">STACK</td>
          </tr>
          <tr>
            <th scope="row">模块级定位</th>
            <td>精确到文件与行号，并说明每个文件大概在做什么。</td>
            <td class="mono">MODULES</td>
          </tr>
          <tr>
            <th scope="row">技术深挖与追问</th>
            <td>优势、难点、相似方案、为什么选它；回答区分事实与推断。</td>
            <td class="mono">AGENT</td>
          </tr>
        </tbody>
      </table>
    </section>

    <p class="home-foot">
      这是一个用来学习 LangChain Agent 的小项目，不是另一个只会聊天的 AI。
      <button class="link-btn" type="button" @click="openConcepts">查看每个能力对应的教程知识点 →</button>
    </p>
  </section>
</template>

<style scoped lang="less">
.home {
  padding-top: 22px;
}

.contact-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.65fr);
  gap: 28px;
  align-items: start;
}

.hero-copy {
  min-width: 0;
}

.strip-head,
.index-head,
.strip-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--faint);
  .mono();
  font-size: 9px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1 {
  margin: 2px 0 0;
  font-size: clamp(48px, 7.3vw, 96px);
  line-height: 0.93;
  letter-spacing: -0.045em;
  font-weight: 500;
  text-transform: uppercase;

  span {
    display: inline-block;
    color: var(--text);
    padding-bottom: 2px;
    border-bottom: 4px solid var(--accent);
  }
}

.lede {
  max-width: 620px;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 15.5px;
  line-height: 1.8;
}

.source-card {
  margin-top: 28px;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  transition: border-color 0.16s, background 0.16s;

  &.focused {
    border-color: var(--accent);
  }
}

.source-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 12px;
  border-bottom: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 9px;
  letter-spacing: 0.1em;
}

.kind-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 9px;
  letter-spacing: 0;
  text-transform: none;

  &.github {
    color: #a9c7e8;
    border-color: #56728d;
  }

  &.ambiguous {
    color: var(--warn);
    border-color: var(--warn);
  }

  &.local {
    color: var(--good);
    border-color: color-mix(in srgb, var(--good) 55%, var(--line));
  }
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
}

.input-mark {
  color: var(--accent);
  .mono();
  font-size: 18px;
  flex: none;
}

#repo-source {
  flex: 1;
  min-width: 0;
  padding: 8px 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text);
  font-size: 16px;
  .mono();

  &::placeholder {
    color: var(--faint);
    font-family: var(--font-ui);
  }
}

.analyze-btn {
  min-width: 122px;
  padding: 11px 14px;
  font-size: 12px;
}

.btn-spinner {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(255, 248, 236, 0.25);
  border-top-color: #fff8ec;
  animation: spin 0.8s linear infinite;
}

.source-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  padding: 9px 12px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 10.5px;

  kbd {
    .mono();
    padding: 1px 4px;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 9px;
  }
}

.examples {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-top: 1px solid var(--line);
}

.example-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 8px 10px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-size: 10.5px;
  text-align: left;

  b {
    color: var(--text);
    font-weight: 500;
  }

  span {
    color: var(--faint);
    .truncate();
    max-width: 150px;
  }

  &:hover {
    background: var(--panel-soft);
    color: var(--text);
  }
}

.recent-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px 14px;
  margin-top: 14px;
  padding: 8px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.strip-label {
  min-width: 100%;
  justify-content: flex-start;
  font-size: 8.5px;
}

.recent-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-size: 10.5px;
  text-align: left;

  b {
    max-width: 110px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text);
    font-weight: 500;
  }

  span {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--faint);
    font-size: 9px;
  }

  &:hover b {
    color: var(--accent);
  }
}

.strip-more {
  margin-left: auto;
  border: 0;
  background: none;
  color: var(--faint);
  font-size: 9.5px;
  .mono();

  &:hover {
    color: var(--accent);
  }
}

.contact-strip {
  border: 1px solid var(--line-strong);
  background: var(--panel);
  padding: 9px;
}

.strip-head,
.strip-foot {
  padding: 0 3px 8px;
  border-bottom: 1px solid var(--line);
}

.strip-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  padding: 8px 3px 0;
  border-top: 1px solid var(--line);
  border-bottom: 0;
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.1em;
}

.frame {
  padding: 10px;
  border: 1px solid var(--line);
  border-top: 0;
  background: color-mix(in srgb, var(--panel) 82%, var(--bg));

  h3 {
    margin: 8px 0 2px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0;
  }

  p {
    margin: 0;
    color: var(--muted);
    font-size: 10.5px;
    line-height: 1.55;
  }
}

.frame-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.12em;
}

.frame-art {
  height: 52px;
  margin-top: 7px;
  border: 1px solid var(--line);
  background: var(--bg-2);
  position: relative;
  overflow: hidden;
}

.frame-art-scan {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 3px;
  padding: 7px;

  span {
    border: 1px solid var(--line);
    background: var(--panel-soft);
  }

  span:nth-child(3),
  span:nth-child(6) {
    background: var(--accent-soft);
    border-color: var(--accent-line);
  }
}

.frame-art-agent {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px;

  i {
    width: 7px;
    height: 7px;
    background: var(--line-strong);

    &:nth-child(1) {
      background: var(--accent);
    }

    &:nth-child(2) {
      height: 18px;
    }

    &:nth-child(3) {
      height: 29px;
      background: var(--text);
    }

    &:nth-child(4) {
      height: 13px;
    }
  }
}

.frame-art-proof {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 4px;
  padding: 8px;

  span {
    height: 5px;
    background: var(--line-strong);
    align-self: start;
  }

  b {
    height: 22px;
    border: 1px solid var(--line);
    grid-row: 2;
  }

  b:nth-child(5) {
    border-color: var(--accent-line);
  }
}

.proof-index {
  margin-top: 38px;
  border-top: 1px solid var(--line-strong);
}

.index-head {
  padding: 9px 0;
  border-bottom: 1px solid var(--line);
}

.proof-index table {
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    padding: 13px 12px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }

  th {
    width: 24%;
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0;
  }

  td {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
  }

  td:last-child {
    width: 90px;
    color: var(--faint);
    font-size: 9px;
    text-align: right;
  }
}

.home-foot {
  margin: 26px 0 0;
  color: var(--faint);
  font-size: 11px;
  line-height: 1.7;
}

.link-btn {
  border: 0;
  background: none;
  color: var(--accent);
  padding: 0;
  font-size: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: @bp-lg) {
  .contact-hero {
    grid-template-columns: minmax(0, 1.15fr) minmax(270px, 0.85fr);
    gap: 18px;
  }
}

@media (max-width: @bp-md) {
  .contact-hero {
    grid-template-columns: 1fr;
  }

  .contact-strip {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0;
    padding: 8px;
  }

  .strip-head,
  .strip-foot {
    grid-column: 1 / -1;
  }

  .frame {
    border-top: 1px solid var(--line);
    border-left: 0;

    &:nth-of-type(2) {
      border-left: 1px solid var(--line);
    }

    &:nth-of-type(3) {
      border-left: 1px solid var(--line);
    }

    p {
      display: none;
    }

    h3 {
      font-size: 11px;
    }
  }

  .frame-art {
    height: 38px;
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

  .recent-item span {
    display: none;
  }

  .proof-index {
    th {
      width: 34%;
      font-size: 12px;
    }

    td:last-child {
      display: none;
    }
  }
}

@media (max-width: @bp-sm) {
  h1 {
    font-size: clamp(42px, 14vw, 64px);
  }

  .contact-strip {
    grid-template-columns: 1fr;
  }

  .frame {
    border-left: 0 !important;

    &:nth-of-type(2),
    &:nth-of-type(3) {
      border-left: 0;
      border-top: 1px solid var(--line);
    }

    p {
      display: block;
    }
  }

  .frame-art {
    height: 44px;
  }

  .example-chip span {
    display: none;
  }

  .proof-index table {
    th,
    td {
      padding: 10px 6px;
    }

    th {
      width: 42%;
    }
  }
}
</style>
