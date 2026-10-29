<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import ArchitectureTab from "../components/ArchitectureTab.vue";
import ChatTab from "../components/ChatTab.vue";
import DependencyGraph from "../components/DependencyGraph.vue";
import Icon from "../components/Icon.vue";
import ModuleMap from "../components/ModuleMap.vue";
import ProcessTab from "../components/ProcessTab.vue";
import TechCard from "../components/TechCard.vue";
import TechGraph from "../components/TechGraph.vue";
import { TABS, categoryIcon, fmtNumber } from "../utils";
import {
  copy,
  exportJSON,
  exportMarkdown,
  goHome,
  openTech,
  setCategory,
  setScrollProgress,
  setSearch,
  startAnalysis,
  state,
  switchTab,
} from "../store";

const report = computed(() => state.report);
const stats = computed(() => report.value?.stats || {});
const techs = computed(() => report.value?.techs || []);
const warnings = computed(() => report.value?.warnings || []);

const codeLanguages = computed(() => (report.value?.languages || []).filter((item) => item.is_code).length);
const scanSeconds = computed(() => Number(stats.value.scan_seconds || 0));

const categories = computed(() => {
  if (report.value?.categories?.length) return report.value.categories;
  const counts = new Map();
  techs.value.forEach((tech) => counts.set(tech.category, (counts.get(tech.category) || 0) + 1));
  return Array.from(counts.entries()).map(([name, count]) => ({ name, count, icon: categoryIcon(name) }));
});

const categoryChips = computed(() => [
  { name: "全部", count: techs.value.length, icon: "◈" },
  ...categories.value,
]);

const filteredTechs = computed(() => {
  const query = state.search.trim().toLowerCase();
  return techs.value.filter((tech) => {
    if (state.category !== "全部" && tech.category !== state.category) return false;
    if (!query) return true;
    return [
      tech.name,
      tech.category,
      tech.layer,
      tech.function,
      tech.role,
      ...(tech.modules || []).map((module) => `${module.path} ${module.snippet} ${module.role} ${module.summary || ""}`),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
});

const stackView = ref("group");

const groups = computed(() => {
  const layerMap = new Map();
  filteredTechs.value.forEach((tech) => {
    const layerName = tech.layer || "其他";
    const functionName = tech.function || tech.category || "其他能力";
    if (!layerMap.has(layerName)) {
      layerMap.set(layerName, {
        name: layerName,
        order: Number(tech.layer_order ?? 999),
        techCount: 0,
        functions: new Map(),
      });
    }
    const layer = layerMap.get(layerName);
    layer.techCount += 1;
    if (!layer.functions.has(functionName)) {
      layer.functions.set(functionName, {
        name: functionName,
        order: Number(tech.function_order ?? 999),
        items: [],
      });
    }
    layer.functions.get(functionName).items.push(tech);
  });
  return Array.from(layerMap.values())
    .sort((a, b) => a.order - b.order || a.name.localeCompare(b.name, "zh-CN"))
    .map((layer) => ({
      ...layer,
      functions: Array.from(layer.functions.values()).sort(
        (a, b) => a.order - b.order || a.name.localeCompare(b.name, "zh-CN")
      ),
    }));
});

const aiState = computed(() => {
  const ai = report.value?.ai || {};
  if (ai.used) return { cls: "good", text: `AI 解读 · ${ai.model || "模型"}` };
  if (ai.error) return { cls: "warn", text: "AI 解读失败 · 规则报告" };
  return { cls: "warn", text: "仅规则扫描（未启用 AI 解读）" };
});

const summaryNote = computed(() => {
  const ai = report.value?.ai || {};
  if (ai.used) return "由大模型基于扫描事实生成";
  if (ai.error) return "AI 不可用，本报告由本地规则生成";
  return "由本地规则生成";
});

const sourceHref = computed(() => {
  if (!report.value) return "";
  if (report.value.source_type !== "github") return "";
  return report.value.source.startsWith("http") ? report.value.source : `https://github.com/${report.value.source}`;
});

function onScroll() {
  const doc = document.documentElement;
  const total = doc.scrollHeight - window.innerHeight;
  setScrollProgress(total > 0 ? (window.scrollY / total) * 100 : 0);
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});

onBeforeUnmount(() => window.removeEventListener("scroll", onScroll));

function reanalyze() {
  if (report.value) startAnalysis(report.value.source);
}

function copyLink() {
  copy(window.location.href, "报告链接");
}
</script>

<template>
  <div class="reading-progress" aria-hidden="true">
    <span :style="{ width: `${state.scrollProgress}%` }"></span>
  </div>

  <section v-if="state.reportLoading && !report" class="report-loading">
    <div class="skeleton hero-skeleton"></div>
    <div class="skeleton-row">
      <div v-for="i in 6" :key="i" class="skeleton stat-skeleton"></div>
    </div>
    <div class="skeleton body-skeleton"></div>
  </section>

  <section v-else-if="!report" class="empty-state">
    <p>报告还没生成。</p>
    <button class="btn" type="button" @click="goHome">返回首页</button>
  </section>

  <section v-else class="report-view">
    <header class="report-head">
      <div class="head-main">
        <div class="kicker">
          <button class="btn back-btn" type="button" @click="goHome">
            <Icon name="arrowLeft" :size="14" /> 新分析
          </button>
          <span class="ai-state" :class="aiState.cls"><i></i>{{ aiState.text }}</span>
        </div>
        <h2>{{ report.repo_name }}</h2>
        <a v-if="sourceHref" class="source mono" :href="sourceHref" target="_blank" rel="noreferrer noopener">
          {{ report.source }} <Icon name="external" :size="12" />
        </a>
        <p v-else class="source mono">{{ report.source }}</p>
      </div>

      <div class="actions">
        <button class="text-action" type="button" @click="copyLink">复制链接</button>
        <button class="text-action" type="button" @click="reanalyze">重新分析</button>
        <button class="text-action" type="button" @click="exportMarkdown">Markdown</button>
        <button class="text-action" type="button" @click="exportJSON">JSON</button>
      </div>
    </header>

    <div class="stat-strip">
      <div class="stat">
        <span class="l">文件总数</span>
        <span class="v">{{ fmtNumber(stats.file_count) }}</span>
      </div>
      <div class="stat">
        <span class="l">代码文件</span>
        <span class="v">{{ fmtNumber(stats.code_file_count) }}</span>
      </div>
      <div class="stat">
        <span class="l">代码行数</span>
        <span class="v">{{ fmtNumber(stats.total_loc) }}</span>
      </div>
      <div class="stat">
        <span class="l">技术项</span>
        <span class="v">{{ fmtNumber(techs.length) }}</span>
      </div>
      <div class="stat">
        <span class="l">编程语言</span>
        <span class="v">{{ fmtNumber(codeLanguages) }}</span>
      </div>
      <div class="stat">
        <span class="l">扫描耗时</span>
        <span class="v">{{ scanSeconds < 0.1 ? "<0.1" : scanSeconds.toFixed(1) }}s</span>
      </div>
    </div>

    <div class="proof-note">
      <div class="proof-note-head">
        <span class="mono">PROOF NOTE / 01</span>
        <span class="muted">{{ summaryNote }}</span>
      </div>
      <p>{{ report.summary }}</p>
      <div v-if="(report.highlights || []).length" class="highlights">
        <span v-for="(item, index) in report.highlights" :key="index">{{ item }}</span>
      </div>
    </div>

    <div v-if="warnings.length" class="warnings">
      <p v-for="(warning, index) in warnings" :key="index">
        <Icon name="warning" :size="13" /> {{ warning }}
      </p>
    </div>

    <nav class="tabs" aria-label="报告分区">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        class="tab"
        :class="{ active: state.tab === tab.key }"
        type="button"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <div class="tab-panels">
      <section v-show="state.tab === 'stack'" class="tab-panel">
        <div class="stack-toolbar">
          <div class="chips">
            <button
              v-for="chip in categoryChips"
              :key="chip.name"
              class="chip"
              :class="{ active: state.category === chip.name }"
              type="button"
              @click="setCategory(chip.name)"
            >
              {{ chip.icon }} {{ chip.name }} · {{ fmtNumber(chip.count) }}
            </button>
          </div>
          <div class="view-toggle" role="group" aria-label="技术栈展示方式">
            <button type="button" :class="{ active: stackView === 'group' }" @click="stackView = 'group'">
              分组
            </button>
            <button type="button" :class="{ active: stackView === 'graph' }" @click="stackView = 'graph'">
              层级图
            </button>
          </div>
          <div class="search-wrap">
            <Icon name="search" :size="14" />
            <input
              :value="state.search"
              type="search"
              placeholder="搜索技术 / 层级 / 功能 / 文件…"
              aria-label="搜索技术"
              @input="setSearch($event.target.value)"
            />
            <button v-if="state.search" class="clear-search" type="button" aria-label="清空搜索" @click="setSearch('')">
              <Icon name="close" :size="12" />
            </button>
          </div>
        </div>

        <div v-if="stackView === 'graph'" class="graph-view">
          <TechGraph v-if="filteredTechs.length" :techs="filteredTechs" @open="openTech" />
          <div v-else class="empty-state">没有匹配的技术。试试清空搜索或切换分类。</div>
        </div>

        <div v-else-if="groups.length" class="tech-groups">
          <section v-for="layer in groups" :key="layer.name" class="tech-group layer-group">
            <div class="group-head">
              <h3>{{ layer.name }}</h3>
              <span class="count mono">{{ layer.techCount }} FRAMES</span>
              <span class="line"></span>
            </div>
            <div v-for="fn in layer.functions" :key="fn.name" class="function-group">
              <div class="function-head">
                <h4>{{ fn.name }}</h4>
                <span class="count mono">{{ fn.items.length }}</span>
                <span class="line"></span>
              </div>
              <div class="tech-grid">
                <TechCard
                  v-for="(tech, index) in fn.items"
                  :key="tech.key"
                  :tech="tech"
                  :index="index"
                  @open="openTech"
                />
              </div>
            </div>
          </section>
        </div>
        <div v-else class="empty-state">
          没有匹配的技术。试试清空搜索或切换分类。
        </div>
      </section>

      <section v-show="state.tab === 'modules'" class="tab-panel">
        <ModuleMap />
      </section>

      <section v-show="state.tab === 'deps'" class="tab-panel">
        <DependencyGraph :graph="report.module_graph" />
      </section>

      <section v-show="state.tab === 'architecture'" class="tab-panel">
        <ArchitectureTab :report="report" />
      </section>

      <section v-show="state.tab === 'chat'" class="tab-panel">
        <ChatTab />
      </section>

      <section v-show="state.tab === 'process'" class="tab-panel">
        <ProcessTab :events="state.events" />
      </section>
    </div>
  </section>
</template>

<style scoped lang="less">
.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 60;
  pointer-events: none;

  span {
    display: block;
    height: 100%;
    background: var(--accent);
    transition: width 0.1s linear;
  }
}

.report-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  padding: 10px 0 18px;
  border-bottom: 1px solid var(--line-strong);
}

.head-main {
  min-width: 0;

  h2 {
    margin: 10px 0 0;
    font-size: clamp(32px, 4.6vw, 52px);
    line-height: 0.98;
    letter-spacing: -0.04em;
    font-weight: 500;
    word-break: break-word;
  }
}

.kicker {
  display: flex;
  align-items: center;
  gap: 9px;
  flex-wrap: wrap;
}

.back-btn {
  padding: 6px 9px;
  font-size: 10.5px;
}

.ai-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--faint);
  .mono();
  font-size: 9px;
  letter-spacing: 0.04em;

  i {
    width: 5px;
    height: 5px;
    background: var(--faint);
  }

  &.good i {
    background: var(--good);
  }

  &.warn i {
    background: var(--warn);
  }
}

.source {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin: 8px 0 0;
  color: var(--faint);
  font-size: 10px;
  word-break: break-all;

  &:hover {
    color: var(--accent);
  }
}

.actions {
  display: flex;
  gap: 0;
  flex-wrap: wrap;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.text-action {
  padding: 7px 9px;
  border: 0;
  border-right: 1px solid var(--line);
  background: none;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 10.5px;
  cursor: pointer;

  &:last-child {
    border-right: 0;
  }

  &:hover {
    color: var(--accent);
    background: var(--panel-soft);
  }
}

.stat-strip {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  margin: 18px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.stat {
  min-width: 0;
  padding: 10px 12px;
  border-right: 1px solid var(--line);

  &:last-child {
    border-right: 0;
  }

  .l {
    display: block;
    color: var(--faint);
    font-size: 9px;
    letter-spacing: 0.06em;
  }

  .v {
    display: block;
    margin-top: 2px;
    color: var(--text);
    .mono();
    font-size: 19px;
    line-height: 1.2;
    white-space: nowrap;
  }
}

.proof-note {
  padding: 16px 18px;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  margin-bottom: 14px;

  > p {
    max-width: 74ch;
    margin: 12px 0 0;
    color: var(--text);
    font-size: 15px;
    line-height: 1.8;
  }
}

.proof-note-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--faint);
  font-size: 9px;
  letter-spacing: 0.08em;

  .muted {
    color: var(--faint);
    font-size: 9px;
  }
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 5px 14px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--line);

  span {
    color: var(--muted);
    font-size: 11px;

    &::before {
      content: "—";
      color: var(--accent);
      margin-right: 5px;
    }
  }
}

.warnings {
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--warn) 40%, var(--line));
  color: var(--warn);
  margin-bottom: 14px;
  font-size: 10.5px;
  line-height: 1.7;

  p {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin: 3px 0;
  }
}

.tabs {
  position: sticky;
  top: 78px;
  z-index: 30;
  display: flex;
  gap: 0;
  margin: 16px 0 18px;
  padding: 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line-strong);
  background: var(--bg);
  overflow-x: auto;
}

.tab {
  border: 0;
  border-right: 1px solid var(--line);
  background: none;
  padding: 10px 14px;
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
  transition: color 0.16s, background 0.16s;

  &:hover {
    color: var(--text);
    background: var(--panel-soft);
  }

  &.active {
    color: var(--accent);
    background: var(--accent-soft);
  }
}

.stack-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.view-toggle {
  display: flex;
  border: 1px solid var(--line);
}

.view-toggle button {
  padding: 5px 8px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 9.5px;
  cursor: pointer;

  &:last-child {
    border-right: 0;
  }

  &.active {
    background: var(--accent-soft);
    color: var(--accent);
  }
}

.graph-view {
  min-width: 0;
  overflow-x: auto;
  padding-bottom: 8px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border: 1px solid var(--line);
}

.chip {
  padding: 5px 8px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-size: 10px;

  &:last-child {
    border-right: 0;
  }

  &:hover {
    color: var(--text);
    background: var(--panel-soft);
  }

  &.active {
    color: var(--accent);
    background: var(--accent-soft);
  }
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 240px;
  max-width: 100%;
  padding: 0 9px;
  border: 1px solid var(--line);
  background: var(--input-bg);
  color: var(--faint);

  &:focus-within {
    border-color: var(--accent);
  }

  input {
    flex: 1;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    padding: 7px 0;
    color: var(--text);
    font-size: 11px;
  }
}

.clear-search {
  border: 0;
  background: none;
  color: var(--faint);
  padding: 2px;
  display: grid;
  place-items: center;

  &:hover {
    color: var(--text);
  }
}

.tech-groups {
  display: flex;
  flex-direction: column;
  gap: 26px;
}

.group-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 9px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line);

  h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: -0.02em;
  }

  .count {
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.08em;
  }

  .line {
    flex: 1;
    height: 1px;
    background: var(--line);
  }
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}

.function-group {
  margin-top: 14px;

  &:first-of-type {
    margin-top: 10px;
  }
}

.function-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
  padding-left: 3px;
  border-left: 1px solid var(--line-strong);

  h4 {
    margin: 0;
    padding-left: 7px;
    color: var(--muted);
    font-family: var(--font-ui);
    font-size: 10px;
    font-weight: 400;
  }

  .count {
    color: var(--faint);
    font-size: 8px;
  }

  .line {
    flex: 1;
    height: 1px;
    background: var(--line);
  }
}

.tab-panel {
  animation: fade-up 0.25s @ease-out;
}

.report-loading {
  padding-top: 24px;
}

.skeleton {
  background: linear-gradient(90deg, var(--panel-soft) 25%, var(--panel-hover) 37%, var(--panel-soft) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.hero-skeleton {
  height: 160px;
  margin-bottom: 14px;
}

.skeleton-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 9px;
  margin-bottom: 14px;
}

.stat-skeleton {
  height: 52px;
}

.body-skeleton {
  height: 520px;
}

@media (max-width: @bp-xl) {
  .stat-strip {
    grid-template-columns: repeat(3, 1fr);
    row-gap: 0;
  }

  .stat:nth-child(3) {
    border-right: 0;
  }

  .stat:nth-child(n + 4) {
    border-top: 1px solid var(--line);
  }
}

@media (max-width: @bp-lg) {
  .tech-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: @bp-md) {
  .report-head {
    align-items: flex-start;
  }

  .actions {
    width: 100%;
  }

  .text-action {
    flex: 1;
    text-align: center;
  }

  .stat-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat:nth-child(2n) {
    border-right: 0;
  }

  .stat:nth-child(3) {
    border-right: 1px solid var(--line);
  }

  .stat:nth-child(n + 3) {
    border-top: 1px solid var(--line);
  }

  .search-wrap {
    width: 100%;
  }

  .tabs {
    top: 70px;
  }

  .tech-grid {
    grid-template-columns: 1fr;
  }

  .proof-note {
    padding: 14px;
  }
}
</style>
