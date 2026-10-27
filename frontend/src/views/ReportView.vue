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
      tech.function,
      tech.role,
      ...(tech.modules || []).map((module) => `${module.path} ${module.snippet} ${module.role}`),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
});

const groups = computed(() => {
  const map = new Map();
  filteredTechs.value.forEach((tech) => {
    const name = tech.function || tech.category || "其他能力";
    if (!map.has(name)) {
      map.set(name, {
        name,
        order: Number(tech.function_order ?? 999),
        items: [],
      });
    }
    map.get(name).items.push(tech);
  });
  return Array.from(map.values()).sort(
    (a, b) => a.order - b.order || a.name.localeCompare(b.name, "zh-CN")
  );
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
          <span class="tag" :class="aiState.cls"><Icon name="spark" :size="12" /> {{ aiState.text }}</span>
        </div>
        <h2>{{ report.repo_name }}</h2>
        <a v-if="sourceHref" class="source mono" :href="sourceHref" target="_blank" rel="noreferrer noopener">
          {{ report.source }} <Icon name="external" :size="12" />
        </a>
        <p v-else class="source mono">{{ report.source }}</p>
      </div>

      <div class="actions">
        <button class="btn icon-action" type="button" title="复制报告链接" @click="copyLink">
          <Icon name="copy" :size="14" /> 链接
        </button>
        <button class="btn" type="button" @click="reanalyze">
          <Icon name="refresh" :size="14" /> 重新分析
        </button>
        <button class="btn" type="button" @click="exportMarkdown">
          <Icon name="download" :size="14" /> Markdown
        </button>
        <button class="btn" type="button" @click="exportJSON">
          <Icon name="download" :size="14" /> JSON
        </button>
      </div>
    </header>

    <div class="stat-row">
      <div class="stat-card">
        <span class="v">{{ fmtNumber(stats.file_count) }}</span>
        <span class="l">文件总数</span>
      </div>
      <div class="stat-card">
        <span class="v">{{ fmtNumber(stats.code_file_count) }}</span>
        <span class="l">代码文件</span>
      </div>
      <div class="stat-card">
        <span class="v">{{ fmtNumber(stats.total_loc) }}</span>
        <span class="l">代码行数</span>
      </div>
      <div class="stat-card">
        <span class="v">{{ fmtNumber(techs.length) }}</span>
        <span class="l">技术项</span>
      </div>
      <div class="stat-card">
        <span class="v">{{ fmtNumber(codeLanguages) }}</span>
        <span class="l">编程语言</span>
      </div>
      <div class="stat-card">
        <span class="v">{{ scanSeconds < 0.1 ? "<0.1" : scanSeconds.toFixed(1) }}s</span>
        <span class="l">扫描耗时</span>
      </div>
    </div>

    <div class="summary-card">
      <div class="summary-top">
        <h3><Icon name="spark" :size="14" /> 一句话看懂</h3>
        <span class="muted">{{ summaryNote }}</span>
      </div>
      <p>{{ report.summary }}</p>
      <div v-if="(report.highlights || []).length" class="highlights">
        <span v-for="(item, index) in report.highlights" :key="index" class="chip">{{ item }}</span>
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
              <span class="count mono">{{ group.items.length }}</span>
              <span class="line"></span>
            </div>
            <div class="tech-grid">
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
    background: linear-gradient(90deg, var(--accent), var(--accent-2), var(--accent-3));
    transition: width 0.1s linear;
  }
}

.report-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  padding: 8px 0 22px;
}

.head-main {
  min-width: 0;

  h2 {
    margin: 10px 0 0;
    font-size: clamp(28px, 4vw, 42px);
    line-height: 1.1;
    letter-spacing: -1px;
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
  padding: 7px 10px;
  font-size: 11.5px;
}

.source {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 11.5px;
  word-break: break-all;

  &:hover {
    color: var(--accent);
  }
}

.actions {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;

  .btn {
    font-size: 11.5px;
    padding: 8px 11px;
  }
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 9px;
  margin-bottom: 14px;
}

.stat-card {
  padding: 13px 15px;
  border-radius: @radius-md;
  border: 1px solid var(--line);
  background: var(--panel);
  transition: border-color 0.2s, transform 0.2s;

  &:hover {
    border-color: var(--line-strong);
    transform: translateY(-2px);
  }

  .v {
    display: block;
    .mono();
    font-size: 21px;
    font-weight: 600;
    letter-spacing: -0.5px;
  }

  .l {
    color: var(--faint);
    font-size: 10.5px;
  }
}

.summary-card {
  position: relative;
  padding: 20px 22px;
  border-radius: @radius-xl;
  border: 1px solid var(--accent-line);
  background:
    radial-gradient(900px 160px at 0% 0%, var(--accent-soft), transparent 70%),
    var(--panel);
  margin-bottom: 14px;
}

.summary-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;

  h3 {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    color: var(--accent);
    font-size: 12px;
  }

  .muted {
    font-size: 10.5px;
  }
}

.summary-card > p {
  margin: 10px 0 0;
  font-size: 15.5px;
  line-height: 1.8;
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 14px;

  .chip {
    cursor: default;
    color: var(--text);
  }
}

.warnings {
  padding: 12px 15px;
  border-radius: @radius-md;
  border: 1px solid color-mix(in srgb, var(--warn) 26%, transparent);
  background: var(--warn-soft);
  color: var(--warn);
  margin-bottom: 14px;
  font-size: 11.5px;
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
  top: @topbar-h;
  z-index: 30;
  display: flex;
  gap: 3px;
  margin: 18px 0 18px;
  padding: 0;
  border-bottom: 1px solid var(--line);
  overflow-x: auto;
  .glass();
  background: var(--topbar-bg);
}

.tab {
  position: relative;
  border: 0;
  background: none;
  padding: 11px 15px;
  color: var(--muted);
  font-size: 12.5px;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: color 0.16s;

  &:hover {
    color: var(--text);
  }

  &.active {
    color: var(--text);
    border-bottom-color: var(--accent);

    &::after {
      content: "";
      position: absolute;
      left: 13px;
      right: 13px;
      bottom: -2px;
      height: 2px;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 14px var(--accent);
    }
  }
}

.stack-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 250px;
  max-width: 100%;
  padding: 0 10px;
  border-radius: @radius-sm;
  border: 1px solid var(--line);
  background: var(--input-bg);
  color: var(--faint);
  transition: border-color 0.18s, box-shadow 0.18s;

  &:focus-within {
    border-color: var(--accent-line);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }

  input {
    flex: 1;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    padding: 9px 0;
    font-size: 12px;
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
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 14px;
  }

  .count {
    color: var(--faint);
    font-size: 10.5px;
  }

  .line {
    flex: 1;
    height: 1px;
    background: var(--line);
  }
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(272px, 1fr));
  gap: 11px;
}

.tab-panel {
  animation: fade-up 0.3s @ease-out;
}

.report-loading {
  padding-top: 24px;
}

.skeleton {
  border-radius: @radius-lg;
  background: linear-gradient(90deg, var(--panel-soft) 25%, var(--panel-hover) 37%, var(--panel-soft) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.hero-skeleton {
  height: 220px;
  margin-bottom: 14px;
}

.skeleton-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 9px;
  margin-bottom: 14px;
}

.stat-skeleton {
  height: 64px;
}

.body-skeleton {
  height: 520px;
}

@media (max-width: @bp-xl) {
  .stat-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .skeleton-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: @bp-lg) {
  .tech-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: @bp-md) {
  .report-head {
    align-items: flex-start;
  }

  .actions {
    width: 100%;
  }

  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-wrap {
    width: 100%;
  }

  .tabs {
    top: 64px;
  }

  .tech-grid {
    grid-template-columns: 1fr;
  }

  .summary-card {
    padding: 17px;
  }
}
</style>
