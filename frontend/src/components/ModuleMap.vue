<script setup>
import { computed, ref, watch } from "vue";

import Icon from "./Icon.vue";
import { openCode, setSearch, state } from "../store";
import { fmtNumber, truncate } from "../utils";

const openKeys = ref(new Set());
const topOpen = ref(true);

const techs = computed(() => {
  const query = state.search.trim().toLowerCase();
  return (state.report?.techs || [])
    .filter((tech) => (tech.modules || []).length)
    .filter((tech) => state.category === "全部" || tech.category === state.category)
    .filter((tech) => {
      if (!query) return true;
      const haystack = [
        tech.name,
        tech.category,
        tech.role,
        ...(tech.modules || []).map((module) => `${module.path} ${module.snippet} ${module.role}`),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    })
    .sort((a, b) => b.module_count - a.module_count);
});

const withoutModules = computed(() => {
  const query = state.search.trim().toLowerCase();
  return (state.report?.techs || [])
    .filter((tech) => !(tech.modules || []).length)
    .filter((tech) => state.category === "全部" || tech.category === state.category)
    .filter((tech) => !query || `${tech.name} ${tech.category} ${tech.role}`.toLowerCase().includes(query));
});

const allExpanded = computed(() => techs.value.length > 0 && techs.value.every((tech) => openKeys.value.has(tech.key)));

watch(
  () => state.report?.run_id,
  () => {
    const next = new Set();
    techs.value.slice(0, 3).forEach((tech) => next.add(tech.key));
    openKeys.value = next;
  },
  { immediate: true }
);

function toggle(key) {
  const next = new Set(openKeys.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  openKeys.value = next;
}

function toggleAll() {
  openKeys.value = allExpanded.value ? new Set() : new Set(techs.value.map((tech) => tech.key));
}
</script>

<template>
  <div class="module-map">
    <div class="module-toolbar">
      <div class="module-title">
        <h3>模块地图</h3>
        <span class="muted">{{ fmtNumber(techs.length) }} 项技术有直接 import</span>
      </div>
      <div class="module-actions">
        <input
          :value="state.search"
          class="search-input"
          type="search"
          placeholder="搜索技术 / 文件 / 代码…"
          @input="setSearch($event.target.value)"
        />
        <button class="btn" type="button" :disabled="!techs.length" @click="toggleAll">
          {{ allExpanded ? "全部收起" : "全部展开" }}
        </button>
      </div>
    </div>

    <div v-if="techs.length" class="groups">
      <article v-for="tech in techs" :key="tech.key" class="module-group">
        <button class="group-head" type="button" :aria-expanded="openKeys.has(tech.key)" @click="toggle(tech.key)">
          <span class="chevron" :class="{ open: openKeys.has(tech.key) }">
            <Icon name="chevron" :size="14" />
          </span>
          <span class="group-name">{{ tech.name }}</span>
          <span class="tag">{{ tech.category }}</span>
          <span class="group-meta">{{ fmtNumber(tech.module_count) }} 个模块 · {{ fmtNumber((tech.evidence || []).length) }} 条证据</span>
        </button>

        <Transition name="fold">
          <div v-if="openKeys.has(tech.key)" class="group-body">
            <table class="module-table">
              <thead>
                <tr>
                  <th>文件</th>
                  <th>行</th>
                  <th>角色</th>
                  <th>大概功能</th>
                  <th>代码片段 / 导入语句</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="module in tech.modules" :key="`${module.path}:${module.line}`">
                  <td class="path">
                    <button
                      class="copy-path"
                      type="button"
                      title="查看代码片段"
                      @click.stop="openCode(module.path, module.line)"
                    >
                      {{ module.path }}
                    </button>
                  </td>
                  <td class="line mono">:{{ module.line }}</td>
                  <td class="role">{{ module.role || "源码" }}</td>
                  <td class="summary">{{ module.summary || module.role || "暂无说明" }}</td>
                  <td class="snippet mono">{{ truncate(module.snippet, 160) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Transition>
      </article>
    </div>

    <div v-else class="empty-state">没有找到直接 import 的技术。项目可能只提供了依赖清单，或者代码主要在配置中体现。</div>

    <div v-if="withoutModules.length" class="without">
      <h4>仅出现在依赖清单 / 配置中</h4>
      <p>
        这些技术没有找到直接 import，可能由框架间接使用，也可能已经废弃：
        <span v-for="tech in withoutModules" :key="tech.key" class="tag">{{ tech.name }}</span>
      </p>
    </div>
  </div>
</template>

<style scoped lang="less">
.module-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.module-title {
  display: flex;
  flex-direction: column;
  gap: 2px;

  h3 {
    margin: 0;
    font-size: 15px;
  }

  .muted {
    font-size: 11.5px;
  }
}

.module-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;

  .search-input {
    width: 240px;
  }
}

.search-input {
  padding: 9px 13px;
  border-radius: @radius-sm;
  border: 1px solid var(--line);
  outline: none;
  background: var(--input-bg);
  font-size: 12px;
  transition: border-color 0.18s, box-shadow 0.18s;

  &:focus {
    border-color: var(--accent-line);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.module-group {
  border-radius: @radius-md;
  border: 1px solid var(--line);
  background: var(--panel);
  overflow: hidden;
}

.group-head {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 14px 16px;
  border: 0;
  background: none;
  text-align: left;
  font-size: 12.5px;
  .focus-ring();

  &:hover {
    background: var(--panel-soft);
  }
}

.chevron {
  display: inline-flex;
  color: var(--faint);
  transition: transform 0.18s @ease-out;

  &.open {
    transform: rotate(90deg);
  }
}

.group-name {
  font-weight: 600;
  color: var(--text);
}

.group-meta {
  margin-left: auto;
  color: var(--faint);
  font-size: 10.5px;
  .mono();
}

.group-body {
  border-top: 1px solid var(--line);
  background: color-mix(in srgb, var(--panel-soft) 55%, transparent);
}

.module-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.5px;

  th {
    text-align: left;
    padding: 8px 16px;
    color: var(--faint);
    font-weight: 500;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }

  td {
    padding: 9px 16px;
    border-bottom: 1px solid color-mix(in srgb, var(--line) 55%, transparent);
    vertical-align: top;
  }

  tr:last-child td {
    border-bottom: 0;
  }

  .path {
    width: 27%;
    .mono();
    color: var(--accent);
    word-break: break-all;
  }

  .line {
    color: var(--faint);
    white-space: nowrap;
    width: 50px;
  }

  .role {
    color: var(--muted);
    white-space: nowrap;
    width: 74px;
  }

  .summary {
    width: 28%;
    color: var(--text);
    font-size: 11px;
    line-height: 1.65;
    word-break: break-word;
  }

  .snippet {
    width: 26%;
    color: var(--muted);
    font-size: 10.5px;
    word-break: break-all;
  }
}

.copy-path {
  border: 0;
  background: none;
  color: inherit;
  padding: 0;
  text-align: left;
  font: inherit;
  .mono();
  word-break: break-all;

  &:hover {
    color: var(--text);
    text-decoration: underline;
    text-underline-offset: 2px;
  }
}

.fold-enter-active,
.fold-leave-active {
  transition: opacity 0.18s @ease-out, transform 0.18s @ease-out;
}

.fold-enter-from,
.fold-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.without {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: @radius-md;
  border: 1px dashed var(--line-strong);

  h4 {
    margin: 0 0 6px;
    color: var(--faint);
    font-size: 10.5px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  p {
    margin: 0;
    color: var(--muted);
    font-size: 11.5px;
    line-height: 2;
  }

  .tag {
    margin-right: 4px;
  }
}

@media (max-width: @bp-md) {
  .module-actions {
    width: 100%;

    .search-input {
      width: 100%;
    }
  }

  .group-meta {
    display: none;
  }

  .module-table {
    thead {
      display: none;
    }

    &,
    tbody {
      display: block;
    }

    tbody tr {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 2px 10px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
    }

    tbody tr:last-child {
      border-bottom: 0;
    }

    td {
      display: block;
      padding: 0;
      border: 0;
    }

    .path {
      width: auto;
      grid-column: 1;
    }

    .line {
      grid-column: 2;
      width: auto;
      text-align: right;
    }

    .summary {
      grid-column: 1 / -1;
      width: auto;
      margin-top: 3px;
    }

    .role,
    .snippet {
      display: none;
    }
  }
}
</style>
