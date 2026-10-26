<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";

import ArchitectureTab from "../components/ArchitectureTab.vue";
import ChatTab from "../components/ChatTab.vue";
import Icon from "../components/Icon.vue";
import ModuleMap from "../components/ModuleMap.vue";
import ProcessTab from "../components/ProcessTab.vue";
import TechCard from "../components/TechCard.vue";
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
  { name: "全部", count: techs.value.length },
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
      tech.role,
      ...(tech.modules || []).map((module) => `${module.path} ${module.snippet} ${module.role} ${module.summary || ""}`),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
});

const groups = computed(() => {
  const order = categories.value.map((item) => item.name);
  const map = new Map();
  filteredTechs.value.forEach((tech) => {
    if (!map.has(tech.category)) map.set(tech.category, []);
    map.get(tech.category).push(tech);
  });
  return Array.from(map.entries())
    .sort((a, b) => {
      const ia = order.indexOf(a[0]);
      const ib = order.indexOf(b[0]);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    })
    .map(([name, items]) => ({ name, items }));
});

const aiState = computed(() => {
  const ai = report.value?.ai || {};
  if (ai.used) return { cls: "good", text: `AI 解读 · ${ai.model || "模型"}` };
  if (ai.error) return { cls: "warn", text: "AI 解读失败 · 规则报告" };
  return { cls: "warn", text: "仅规则扫描" };
});

const summaryNote = computed(() => {
  const ai = report.value?.ai || {};
  if (ai.used) return "由大模型基于扫描事实生成";
  if (ai.error) return "AI 不可用，由本地规则生成";
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
          <button class="back-btn" type="button" @click="goHome">
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

    <div class="report-layout">
      <aside class="route-rail">
        <div class="rail-head">
          <span>COURSE / REPORT</span>
          <span>{{ techs.length }} CONTROLS</span>
        </div>

        <nav class="tabs" aria-label="报告分区">
          <button
            v-for="(tab, index) in TABS"
            :key="tab.key"
            class="tab"
            :class="{ active: state.tab === tab.key }"
            type="button"
            @click="switchTab(tab.key)"
          >
            <span class="tab-no">{{ String(index + 1).padStart(2, "0") }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </nav>

        <div class="rail-note">
          沿紫色路线切换报告段落；每一段都保留可核对的证据。
        </div>
      </aside>

      <main class="report-main">
        <div class="stat-line">
          <span><b>{{ fmtNumber(stats.file_count) }}</b><small>文件</small></span>
          <span><b>{{ fmtNumber(stats.code_file_count) }}</b><small>代码文件</small></span>
          <span><b>{{ fmtNumber(stats.total_loc) }}</b><small>代码行</small></span>
          <span><b>{{ fmtNumber(techs.length) }}</b><small>技术项</small></span>
          <span><b>{{ fmtNumber(codeLanguages) }}</b><small>语言</small></span>
          <span><b>{{ scanSeconds < 0.1 ? "<0.1" : scanSeconds.toFixed(1) }}s</b><small>扫描</small></span>
        </div>

        <div class="route-note">
          <div class="note-head">
            <span>ROUTE NOTE / 01</span>
            <span>{{ summaryNote }}</span>
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
                  {{ chip.name }} <span>{{ fmtNumber(chip.count) }}</span>
                </button>
              </div>
              <div class="search-wrap">
                <Icon name="search" :size="14" />
                <input
                  :value="state.search"
                  type="search"
                  placeholder="搜索技术 / 分类 / 文件…"
                  aria-label="搜索技术"
                  @input="setSearch($event.target.value)"
                />
                <button v-if="state.search" class="clear-search" type="button" aria-label="清空搜索" @click="setSearch('')">
                  <Icon name="close" :size="12" />
                </button>
              </div>
            </div>

            <div v-if="groups.length" class="tech-groups">
              <section v-for="group in groups" :key="group.name" class="tech-group">
                <div class="group-head">
                  <h3>{{ group.name }}</h3>
                  <span class="count">{{ group.items.length }} CONTROLS</span>
                  <span class="line"></span>
                </div>
                <div class="tech-list">
                  <TechCard
                    v-for="(tech, index) in group.items"
                    :key="tech.key"
                    :tech="tech"
                    :index="index"
                    @open="openTech"
                  />
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
      </main>
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
  padding: 4px 0 18px;
  border-bottom: 1px solid var(--line-strong);
}

.head-main {
  min-width: 0;

  h2 {
    margin: 10px 0 0;
    font-family: var(--font-display);
    font-size: clamp(38px, 5.5vw, 64px);
    line-height: 0.88;
    letter-spacing: -0.04em;
    font-weight: 700;
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
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-size: 10px;
  cursor: pointer;

  &:hover {
    color: var(--accent);
  }
}

.ai-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--faint);
  .mono();
  font-size: 8.5px;

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
  font-size: 9px;
  word-break: break-all;

  &:hover {
    color: var(--accent);
  }
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-bottom: 2px;
}

.text-action {
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 10px;
  cursor: pointer;

  &:hover {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 3px;
  }
}

.report-layout {
  display: grid;
  grid-template-columns: 176px minmax(0, 1fr);
  gap: 34px;
  align-items: start;
  margin-top: 22px;
}

.route-rail {
  position: sticky;
  top: 104px;
  min-width: 0;
}

.rail-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line-strong);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.05em;
}

.tabs {
  position: relative;
  display: flex;
  flex-direction: column;
  margin-top: 10px;
  padding-left: 17px;

  &::before {
    content: "";
    position: absolute;
    top: 9px;
    bottom: 9px;
    left: 4px;
    width: 1px;
    background: var(--accent);
    opacity: 0.45;
  }
}

.tab {
  position: relative;
  display: grid;
  grid-template-columns: 27px 1fr;
  gap: 5px;
  align-items: baseline;
  padding: 8px 0;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: none;
  color: var(--muted);
  font-size: 11.5px;
  text-align: left;
  cursor: pointer;

  .tab-no {
    color: var(--faint);
    .mono();
    font-size: 8px;
  }

  &::before {
    content: "";
    position: absolute;
    left: -17px;
    top: 12px;
    width: 9px;
    height: 9px;
    border: 1px solid var(--accent);
    border-radius: 50%;
    background: var(--bg);
  }

  &:hover {
    color: var(--text);
  }

  &.active {
    color: var(--accent);

    &::before {
      background: var(--accent);
    }
  }
}

.rail-note {
  margin-top: 15px;
  color: var(--faint);
  font-size: 9px;
  line-height: 1.6;
}

.report-main {
  min-width: 0;
}

.stat-line {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);

  span {
    display: flex;
    flex-direction: column;
    gap: 1px;
    padding: 9px 10px;
    border-right: 1px solid var(--line);

    &:last-child {
      border-right: 0;
    }
  }

  b {
    color: var(--text);
    .mono();
    font-size: 17px;
    font-weight: 400;
    line-height: 1.2;
  }

  small {
    color: var(--faint);
    font-size: 8.5px;
  }
}

.route-note {
  max-width: 74ch;
  padding: 20px 0 17px;
  border-bottom: 1px solid var(--line-strong);

  p {
    margin: 13px 0 0;
    color: var(--text);
    font-family: var(--font-display);
    font-size: clamp(20px, 2.2vw, 27px);
    line-height: 1.6;
    letter-spacing: -0.01em;
  }
}

.note-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.07em;
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin-top: 14px;
  color: var(--muted);
  font-size: 10px;

  span::before {
    content: "—";
    margin-right: 5px;
    color: var(--accent);
  }
}

.warnings {
  padding: 9px 0;
  border-bottom: 1px solid var(--line);
  color: var(--warn);
  font-size: 10px;
  line-height: 1.7;

  p {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin: 3px 0;
  }
}

.stack-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin: 18px 0 14px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-bottom: 1px solid var(--line);
}

.chip {
  padding: 5px 7px;
  border: 0;
  border-bottom: 1px solid transparent;
  background: none;
  color: var(--muted);
  font-size: 9.5px;
  cursor: pointer;

  span {
    color: var(--faint);
    font-size: 8px;
  }

  &:hover {
    color: var(--text);
  }

  &.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 220px;
  max-width: 100%;
  padding: 0 8px;
  border-bottom: 1px solid var(--line-strong);
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
    padding: 6px 0;
    color: var(--text);
    font-size: 10.5px;
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
  gap: 24px;
}

.group-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line-strong);

  h3 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .count {
    color: var(--faint);
    .mono();
    font-size: 8px;
  }

  .line {
    flex: 1;
    height: 1px;
    background: var(--line);
  }
}

.tech-list {
  display: flex;
  flex-direction: column;
}

.tab-panel {
  animation: fade-up 0.22s @ease-out;
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

@media (max-width: @bp-lg) {
  .report-layout {
    grid-template-columns: 150px minmax(0, 1fr);
    gap: 24px;
  }

  .stat-line {
    grid-template-columns: repeat(3, 1fr);
  }

  .stat-line span:nth-child(3) {
    border-right: 0;
  }

  .stat-line span:nth-child(n + 4) {
    border-top: 1px solid var(--line);
  }
}

@media (max-width: @bp-md) {
  .report-head {
    align-items: flex-start;
  }

  .actions {
    width: 100%;
    gap: 16px;
  }

  .report-layout {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-top: 16px;
  }

  .route-rail {
    position: static;
  }

  .rail-head {
    display: none;
  }

  .tabs {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    margin-top: 0;
    padding-left: 0;
    border-bottom: 1px solid var(--line);
    overflow-x: auto;

    &::before {
      display: none;
    }
  }

  .tab {
    display: flex;
    justify-content: center;
    gap: 4px;
    padding: 8px 4px;
    border-bottom: 0;
    border-right: 1px solid var(--line);
    font-size: 10px;

    .tab-no {
      display: none;
    }

    &::before {
      display: none;
    }

    &:last-child {
      border-right: 0;
    }

    &.active {
      border-bottom: 2px solid var(--accent);
    }
  }

  .rail-note {
    display: none;
  }

  .stat-line {
    grid-template-columns: repeat(3, 1fr);
  }

  .route-note p {
    font-size: 19px;
  }

  .search-wrap {
    width: 100%;
  }
}

@media (max-width: @bp-sm) {
  .stat-line {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-line span:nth-child(3) {
    border-right: 1px solid var(--line);
  }

  .stat-line span:nth-child(2n) {
    border-right: 0;
  }

  .stat-line span:nth-child(n + 3) {
    border-top: 1px solid var(--line);
  }

  .tabs {
    grid-template-columns: repeat(5, minmax(66px, 1fr));
  }

  .tab {
    font-size: 9px;
  }
}
</style>
