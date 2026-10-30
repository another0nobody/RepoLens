<script setup>
import { computed } from "vue";

import BaseDrawer from "./BaseDrawer.vue";
import Icon from "./Icon.vue";
import { closeCompare, loadDiff, state } from "../store";
import { fmtDate, fmtNumber } from "../utils";

const candidates = computed(() =>
  (state.history || []).filter((item) => item.run_id !== state.report?.run_id)
);
const diff = computed(() => state.diff.data);
const summary = computed(() => diff.value?.summary || {});
const changedCount = computed(() => {
  const value = summary.value;
  return [
    value.tech_added,
    value.tech_removed,
    value.tech_changed,
    value.module_nodes_added,
    value.module_nodes_removed,
    value.module_edges_added,
    value.module_edges_removed,
    value.risk_added,
    value.risk_removed,
    value.warning_added,
    value.warning_removed,
    diff.value?.text?.architecture?.added_count,
    diff.value?.text?.architecture?.removed_count,
    diff.value?.text?.highlights?.added_count,
    diff.value?.text?.highlights?.removed_count,
    diff.value?.text?.learning_path?.added_count,
    diff.value?.text?.learning_path?.removed_count,
  ].reduce((total, item) => total + Number(item || 0), 0);
});

function delta(value) {
  const number = Number(value || 0);
  if (!number) return "0";
  return `${number > 0 ? "+" : ""}${fmtNumber(number)}`;
}

function choose(event) {
  const value = event.target.value;
  if (value) loadDiff(value);
}

function labelOf(item) {
  return `${item.repo_name || item.run_id} · ${fmtDate(item.generated_at)}`;
}
</script>

<template>
  <BaseDrawer
    :open="state.drawers.compare"
    title="报告对比"
    subtitle="用当前报告对比另一份历史报告，看技术、依赖和风险发生了什么变化。"
    wide
    @close="closeCompare"
  >
    <div class="compare-head">
      <div>
        <p class="eyebrow mono">REPORT DIFF / 变化追踪</p>
        <h3>当前报告 vs 历史报告</h3>
      </div>
      <button class="btn" type="button" :disabled="state.diff.loading" @click="loadDiff(state.diff.baseId)">
        <Icon name="refresh" :size="14" /> 刷新
      </button>
    </div>

    <div v-if="!candidates.length" class="empty-state">
      还没有其他历史报告可以对比。先分析另一个版本，再回来看看变化。
    </div>

    <template v-else>
      <label class="base-picker">
        <span class="mono">对比基准 / BASE</span>
        <select :value="state.diff.baseId" :disabled="state.diff.loading" @change="choose">
          <option v-for="item in candidates" :key="item.run_id" :value="item.run_id">
            {{ labelOf(item) }}
          </option>
        </select>
      </label>

      <div v-if="state.diff.loading" class="compare-loading">
        <span class="spinner"></span> 正在计算差异…
      </div>
      <div v-else-if="state.diff.error" class="empty-state">{{ state.diff.error }}</div>

      <template v-else-if="diff">
        <div class="compare-summary">
          <div class="compare-side">
            <span class="mono">BASE / 旧</span>
            <b>{{ diff.base.repo_name }}</b>
            <span>{{ fmtDate(diff.base.generated_at) }}</span>
          </div>
          <div class="compare-arrow">→</div>
          <div class="compare-side">
            <span class="mono">TARGET / 当前</span>
            <b>{{ diff.target.repo_name }}</b>
            <span>{{ fmtDate(diff.target.generated_at) }}</span>
          </div>
          <span class="change-total mono">{{ changedCount }} 项变化</span>
        </div>

        <p v-if="!diff.same_repo" class="different-source">
          注意：两份报告的来源不同，下面的差异可能包含不同项目之间的变化。
        </p>

        <div class="stat-diff">
          <div v-for="item in diff.stats" :key="item.key" class="stat-cell">
            <span class="l">{{ item.label }}</span>
            <strong>{{ fmtNumber(item.target) }}</strong>
            <span class="d" :class="{ up: item.delta > 0, down: item.delta < 0 }">{{ delta(item.delta) }}</span>
          </div>
        </div>

        <div v-if="!diff.has_changes" class="empty-state">
          两份报告没有发现技术、依赖、风险或统计变化。
        </div>

        <template v-else>
          <section
            v-if="summary.tech_added || summary.tech_removed || summary.tech_changed"
            class="diff-section"
          >
            <div class="section-head">
              <h4>技术栈</h4>
              <span class="mono">{{ summary.tech_added }} 新增 · {{ summary.tech_removed }} 移除 · {{ summary.tech_changed }} 变化</span>
            </div>
            <div v-if="diff.techs.added.length" class="chip-row">
              <span v-for="tech in diff.techs.added" :key="`add-${tech.name}`" class="chip added">
                + {{ tech.name }} <em v-if="tech.version">v{{ tech.version }}</em>
              </span>
            </div>
            <div v-if="diff.techs.removed.length" class="chip-row">
              <span v-for="tech in diff.techs.removed" :key="`remove-${tech.name}`" class="chip removed">
                − {{ tech.name }} <em v-if="tech.version">v{{ tech.version }}</em>
              </span>
            </div>
            <div v-if="diff.techs.changed.length" class="change-list">
              <div v-for="tech in diff.techs.changed" :key="`changed-${tech.name}`" class="change-row">
                <b>{{ tech.name }}</b>
                <span v-for="change in tech.changes" :key="`${tech.name}-${change.field}`" class="change-field">
                  {{ change.label }}：{{ change.base || "—" }} → {{ change.target || "—" }}
                </span>
              </div>
            </div>
          </section>

          <section
            v-if="
              summary.module_nodes_added ||
              summary.module_nodes_removed ||
              summary.module_edges_added ||
              summary.module_edges_removed ||
              diff.modules.cycle_delta
            "
            class="diff-section"
          >
            <div class="section-head">
              <h4>模块依赖</h4>
              <span class="mono">
                +{{ summary.module_nodes_added }} 节点 · −{{ summary.module_nodes_removed }} 节点 ·
                +{{ summary.module_edges_added }} 边 · −{{ summary.module_edges_removed }} 边
              </span>
            </div>
            <div class="change-list">
              <div v-for="edge in diff.modules.edges_added" :key="`ea-${edge.source}-${edge.target}`" class="change-row">
                <span class="mono">+ {{ edge.source }} → {{ edge.target }}</span>
              </div>
              <div v-for="edge in diff.modules.edges_removed" :key="`er-${edge.source}-${edge.target}`" class="change-row">
                <span class="mono">− {{ edge.source }} → {{ edge.target }}</span>
              </div>
            </div>
          </section>

          <section class="diff-section">
            <div class="section-head">
              <h4>风险与解读</h4>
              <span class="mono">+{{ summary.risk_added }} 风险 · −{{ summary.risk_removed }} 风险</span>
            </div>
            <div v-if="diff.text.risks.added.length" class="text-diff add">
              <p v-for="(item, index) in diff.text.risks.added" :key="`ra-${index}`">+ {{ item }}</p>
            </div>
            <div v-if="diff.text.risks.removed.length" class="text-diff remove">
              <p v-for="(item, index) in diff.text.risks.removed" :key="`rr-${index}`">− {{ item }}</p>
            </div>
            <div v-if="!diff.text.risks.added.length && !diff.text.risks.removed.length" class="muted-line">
              风险列表没有变化。
            </div>
          </section>

          <section
            v-if="
              diff.text.architecture.added.length ||
              diff.text.architecture.removed.length ||
              diff.text.highlights.added.length ||
              diff.text.highlights.removed.length ||
              diff.text.learning_path.added.length ||
              diff.text.learning_path.removed.length
            "
            class="diff-section"
          >
            <div class="section-head">
              <h4>架构与阅读</h4>
              <span class="mono">旧报告 → 当前报告</span>
            </div>
            <div
              v-for="section in [diff.text.architecture, diff.text.highlights, diff.text.learning_path]"
              :key="section.label"
              class="reading-section"
            >
              <p class="reading-label mono">{{ section.label }}</p>
              <div v-if="section.added.length" class="text-diff add">
                <p v-for="(item, index) in section.added" :key="`${section.label}-a-${index}`">+ {{ item }}</p>
              </div>
              <div v-if="section.removed.length" class="text-diff remove">
                <p v-for="(item, index) in section.removed" :key="`${section.label}-r-${index}`">− {{ item }}</p>
              </div>
            </div>
          </section>

          <section v-if="diff.text.warnings.added.length || diff.text.warnings.removed.length" class="diff-section">
            <div class="section-head">
              <h4>警告</h4>
              <span class="mono">+{{ summary.warning_added }} · −{{ summary.warning_removed }}</span>
            </div>
            <div class="text-diff add">
              <p v-for="(item, index) in diff.text.warnings.added" :key="`wa-${index}`">+ {{ item }}</p>
            </div>
            <div class="text-diff remove">
              <p v-for="(item, index) in diff.text.warnings.removed" :key="`wr-${index}`">− {{ item }}</p>
            </div>
          </section>
        </template>
      </template>
    </template>
  </BaseDrawer>
</template>

<style scoped lang="less">
.compare-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-strong);

  h3 {
    margin: 4px 0 0;
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 500;
  }
}

.base-picker {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0;

  > span {
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }

  select {
    flex: 1;
    min-width: 0;
    padding: 7px 8px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 11px;
  }
}

.compare-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--faint);
  font-size: 12px;
}

.spinner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--accent-soft);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

.compare-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.compare-side {
  display: flex;
  flex-direction: column;
  gap: 3px;

  span {
    color: var(--faint);
    font-size: 9px;
  }

  b {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 500;
  }
}

.compare-arrow {
  color: var(--accent);
  .mono();
}

.change-total {
  margin-left: auto;
  padding: 4px 7px;
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 8px;
  white-space: nowrap;
}

.different-source {
  margin: 0 0 12px;
  padding: 7px 9px;
  border-left: 2px solid var(--warn);
  color: var(--warn);
  font-size: 10.5px;
  line-height: 1.55;
}

.stat-diff {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin: 14px 0 20px;
  background: var(--line);
  border: 1px solid var(--line);
}

.stat-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 9px;
  background: var(--panel);

  .l {
    color: var(--faint);
    font-size: 9px;
  }

  strong {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 500;
  }

  .d {
    color: var(--faint);
    .mono();
    font-size: 9px;

    &.up {
      color: var(--accent);
    }

    &.down {
      color: var(--faint);
    }
  }
}

.diff-section {
  padding: 14px 0;
  border-top: 1px solid var(--line);
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;

  h4 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 500;
  }

  span {
    color: var(--faint);
    font-size: 8px;
  }
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 7px;
}

.chip {
  padding: 3px 6px;
  border: 1px solid var(--line);
  font-family: var(--font-ui);
  font-size: 10px;

  em {
    color: var(--faint);
    font-family: var(--mono);
    font-size: 8px;
    font-style: normal;
  }

  &.added {
    border-color: var(--good);
    color: var(--good);
  }

  &.removed {
    border-color: var(--line-strong);
    color: var(--faint);
    text-decoration: line-through;
  }
}

.change-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.change-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--line);
  font-size: 10.5px;

  b {
    font-family: var(--font-display);
    font-size: 12px;
    font-weight: 500;
  }
}

.change-field {
  color: var(--muted);
  font-size: 10px;
}

.reading-section {
  margin-bottom: 8px;

  .reading-label {
    margin: 0 0 4px;
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.06em;
  }
}

.text-diff {
  padding: 7px 9px;
  border-left: 2px solid var(--line-strong);

  p {
    margin: 3px 0;
    color: var(--muted);
    font-size: 10.5px;
    line-height: 1.55;
  }

  &.add {
    border-left-color: var(--good);
  }

  &.remove {
    border-left-color: var(--line-strong);

    p {
      color: var(--faint);
      text-decoration: line-through;
    }
  }
}

.muted-line {
  color: var(--faint);
  font-size: 10.5px;
}

@media (max-width: 720px) {
  .compare-summary {
    flex-wrap: wrap;
  }

  .change-total {
    margin-left: 0;
  }

  .stat-diff {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
