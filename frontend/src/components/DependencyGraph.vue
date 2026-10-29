<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  graph: { type: Object, default: () => ({ nodes: [], edges: [], stats: {} }) },
});

const view = ref("dir");
const search = ref("");
const selectedId = ref("");
const hoveredId = ref("");

const DIR_COLORS = [
  "#67e8f9",
  "#fbbf24",
  "#a78bfa",
  "#34d399",
  "#f472b6",
  "#fb923c",
  "#94a3b8",
  "#e879f9",
];

const nodes = computed(() => Array.isArray(props.graph?.nodes) ? props.graph.nodes : []);
const edges = computed(() => Array.isArray(props.graph?.edges) ? props.graph.edges : []);
const stats = computed(() => props.graph?.stats || {});

const dirGraph = computed(() => {
  const map = new Map();
  const edgeMap = new Map();
  const ensure = (name) => {
    if (!map.has(name)) {
      map.set(name, {
        id: name,
        label: name || "(root)",
        dir: name,
        count: 0,
        loc: 0,
        in: 0,
        out: 0,
        cycle: false,
        entry: false,
      });
    }
    return map.get(name);
  };
  nodes.value.forEach((node) => {
    const item = ensure(node.dir || "(root)");
    item.count += 1;
    item.loc += Number(node.loc || 0);
    item.cycle = item.cycle || Boolean(node.cycle);
    item.entry = item.entry || Boolean(node.entry);
  });
  edges.value.forEach((edge) => {
    const source = edge.source;
    const target = edge.target;
    const sourceNode = nodes.value.find((node) => node.id === source);
    const targetNode = nodes.value.find((node) => node.id === target);
    if (!sourceNode || !targetNode) return;
    const from = sourceNode.dir || "(root)";
    const to = targetNode.dir || "(root)";
    if (from === to) return;
    const key = `${from}→${to}`;
    if (!edgeMap.has(key)) edgeMap.set(key, { source: from, target: to, weight: 0 });
    edgeMap.get(key).weight += 1;
    ensure(from).out += 1;
    ensure(to).in += 1;
  });
  return {
    nodes: Array.from(map.values()).sort((a, b) => a.label.localeCompare(b.label)),
    edges: Array.from(edgeMap.values()),
  };
});

const fileGraph = computed(() => ({
  nodes: nodes.value.map((node) => ({
    ...node,
    label: node.label || node.path,
    in: node.in_degree || 0,
    out: node.out_degree || 0,
    count: 1,
  })),
  edges: edges.value,
}));

const active = computed(() => (view.value === "dir" ? dirGraph.value : fileGraph.value));
const colorFor = (node) => {
  if (view.value === "file") {
    const index = Math.max(0, dirGraph.value.nodes.findIndex((item) => item.label === node.dir));
    return DIR_COLORS[index % DIR_COLORS.length];
  }
  const index = Math.max(0, dirGraph.value.nodes.findIndex((item) => item.id === node.id));
  return DIR_COLORS[index % DIR_COLORS.length];
};

const selected = computed(() =>
  active.value.nodes.find((node) => node.id === selectedId.value) || null
);

const highlighted = computed(() => {
  const wanted = search.value.trim().toLowerCase();
  if (!wanted) return new Set();
  return new Set(
    active.value.nodes
      .filter((node) => `${node.label} ${node.path || ""}`.toLowerCase().includes(wanted))
      .map((node) => node.id)
  );
});

const layoutNodes = computed(() => {
  const items = active.value.nodes;
  const count = items.length;
  const center = { x: 500, y: 306 };
  const radius = count <= 1 ? 0 : Math.min(248, 150 + count * 4);
  return items.map((node, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / Math.max(1, count);
    return {
      ...node,
      x: count === 1 ? center.x : center.x + Math.cos(angle) * radius,
      y: count === 1 ? center.y : center.y + Math.sin(angle) * radius,
      color: colorFor(node),
    };
  });
});

const positionMap = computed(() => {
  const map = new Map();
  layoutNodes.value.forEach((node) => map.set(node.id, node));
  return map;
});

const selectedLinks = computed(() => {
  if (!selected.value) return { outgoing: [], incoming: [] };
  const outgoing = active.value.edges
    .filter((edge) => edge.source === selected.value.id)
    .map((edge) => positionMap.value.get(edge.target)?.label || edge.target);
  const incoming = active.value.edges
    .filter((edge) => edge.target === selected.value.id)
    .map((edge) => positionMap.value.get(edge.source)?.label || edge.source);
  return {
    outgoing: [...new Set(outgoing)].slice(0, 12),
    incoming: [...new Set(incoming)].slice(0, 12),
  };
});

const selectedFiles = computed(() => {
  if (!selected.value || view.value !== "dir") return [];
  return nodes.value
    .filter((node) => node.dir === selected.value.id)
    .sort((a, b) => b.out_degree - a.out_degree)
    .slice(0, 12);
});

function edgePath(edge) {
  const from = positionMap.value.get(edge.source);
  const to = positionMap.value.get(edge.target);
  if (!from || !to) return "";
  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2;
  const controlX = (midX + 500) / 2;
  const controlY = (midY + 306) / 2;
  return `M ${from.x} ${from.y} Q ${controlX} ${controlY} ${to.x} ${to.y}`;
}

function edgeActive(edge) {
  const focus = hoveredId.value || selectedId.value;
  if (!focus) return true;
  return edge.source === focus || edge.target === focus;
}

function choose(node) {
  selectedId.value = selectedId.value === node.id ? "" : node.id;
}

function chooseFile(file) {
  view.value = "file";
  selectedId.value = file.id;
}

watch(search, () => {
  if (!search.value) selectedId.value = "";
});
</script>

<template>
  <div class="dependency-graph">
    <div class="dep-head">
      <div>
        <p class="eyebrow mono">DEPENDENCY MAP / 依赖图</p>
        <h2>模块之间怎么连</h2>
        <p class="dep-note">
          只统计仓库内文件之间的 import；目录视图先去噪，文件视图看具体引用。
        </p>
      </div>
      <div class="dep-stats mono">
        <span>{{ active.nodes.length }} 节点</span>
        <span>{{ active.edges.length }} 边</span>
        <span v-if="view === 'dir'" class="mono">文件图 {{ stats.node_count ?? nodes.length }}/{{ stats.edge_count ?? edges.length }}</span>
        <span v-if="stats.cycle_count" class="cycle-count">{{ stats.cycle_count }} 回边</span>
        <span v-if="stats.truncated" class="warn">已截断</span>
      </div>
    </div>

    <div class="dep-toolbar">
      <div class="dep-view-toggle" role="group" aria-label="依赖图视图">
        <button type="button" :class="{ active: view === 'dir' }" @click="view = 'dir'; selectedId = ''">
          目录
        </button>
        <button type="button" :class="{ active: view === 'file' }" @click="view = 'file'; selectedId = ''">
          文件
        </button>
      </div>
      <div class="dep-search">
        <input v-model="search" type="search" placeholder="搜索目录 / 文件…" aria-label="搜索依赖节点" />
      </div>
      <span class="dep-hint mono">点击节点查看依赖</span>
    </div>

    <div v-if="!active.nodes.length" class="dep-empty">
      <p>这份报告还没有模块依赖图。</p>
      <span>旧报告需要重新分析；如果仓库没有本地 import，也会显示为空。</span>
    </div>

    <template v-else>
      <div class="dep-canvas" :class="{ dimmed: highlighted.size > 0 }">
        <svg viewBox="0 0 1000 612" class="dep-svg" role="img" aria-label="模块依赖关系图">
          <defs>
            <marker id="dep-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
            </marker>
          </defs>

          <g class="dep-edges">
            <path
              v-for="(edge, index) in active.edges"
              :key="`${edge.source}-${edge.target}-${index}`"
              :d="edgePath(edge)"
              class="dep-edge"
              :class="{ active: edgeActive(edge), muted: (hoveredId || selectedId) && !edgeActive(edge) }"
              :style="{ color: positionMap.get(edge.source)?.color || 'var(--line-strong)' }"
              marker-end="url(#dep-arrow)"
            />
          </g>

          <g
            v-for="node in layoutNodes"
            :key="node.id"
            class="dep-node"
            :class="{
              selected: selectedId === node.id,
              muted: (highlighted.size > 0 && !highlighted.has(node.id)) || ((hoveredId || selectedId) && hoveredId !== node.id && selectedId !== node.id),
              matched: highlighted.has(node.id),
              cycle: node.cycle,
              entry: node.entry,
            }"
            :transform="`translate(${node.x} ${node.y})`"
            tabindex="0"
            role="button"
            :aria-label="`${node.label}，${node.in || 0} 个入边，${node.out || 0} 个出边`"
            @click="choose(node)"
            @keydown.enter.prevent="choose(node)"
            @mouseenter="hoveredId = node.id"
            @mouseleave="hoveredId = ''"
          >
            <title>{{ node.path || node.label }}</title>
            <rect :x="view === 'dir' ? -72 : -58" :y="-22" :width="view === 'dir' ? 144 : 116" height="44" />
            <rect :x="view === 'dir' ? -62 : -48" y="-16" width="6" height="6" :fill="node.color" class="node-dot" />
            <text text-anchor="middle" y="0">{{ node.label }}</text>
            <text class="node-count" text-anchor="middle" y="14">
              {{ view === "dir" ? `${node.count} files · ${node.loc} loc` : `${node.language || "code"} · ${node.loc} loc` }}
            </text>
          </g>
        </svg>
      </div>

      <div class="dep-mobile">
        <section v-for="node in active.nodes" :key="node.id" class="dep-mobile-row" @click="choose(node)">
          <span class="dot" :style="{ background: colorFor(node) }"></span>
          <b>{{ node.label }}</b>
          <span class="mono">{{ node.in || 0 }} in / {{ node.out || 0 }} out</span>
        </section>
      </div>

      <div v-if="selected" class="dep-detail">
        <div class="dep-detail-head">
          <div>
            <p class="eyebrow mono">{{ view === "dir" ? "DIRECTORY" : "FILE" }} / SELECTED</p>
            <h3>{{ selected.label }}</h3>
            <p class="dep-path mono">{{ selected.path || selected.id }}</p>
          </div>
          <button type="button" class="dep-close" aria-label="关闭详情" @click="selectedId = ''">关闭</button>
        </div>
        <div class="dep-detail-grid">
          <div>
            <span class="label mono">入边</span>
            <strong>{{ selected.in || 0 }}</strong>
            <p v-if="selectedLinks.incoming.length" class="dep-link-list">{{ selectedLinks.incoming.join("、") }}</p>
          </div>
          <div>
            <span class="label mono">出边</span>
            <strong>{{ selected.out || 0 }}</strong>
            <p v-if="selectedLinks.outgoing.length" class="dep-link-list">{{ selectedLinks.outgoing.join("、") }}</p>
          </div>
          <div v-if="view === 'file'">
            <span class="label mono">角色</span>
            <strong>{{ selected.role || "代码文件" }}</strong>
            <p class="dep-link-list">{{ selected.entry ? "入口文件" : "普通模块" }} · {{ selected.cycle ? "参与循环依赖" : "无回边" }}</p>
          </div>
        </div>

        <div v-if="view === 'dir' && selectedFiles.length" class="dep-file-list">
          <p class="label mono">目录内文件（按出边排序）</p>
          <button
            v-for="file in selectedFiles"
            :key="file.id"
            type="button"
            class="dep-file-row"
            @click="chooseFile(file)"
          >
            <span>{{ file.label }}</span>
            <span class="mono">{{ file.out_degree }} out · {{ file.loc }} loc</span>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped lang="less">
.dependency-graph {
  min-width: 0;
}

.dep-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line-strong);

  h2 {
    margin: 4px 0 4px;
    font-family: var(--font-display);
    font-size: 24px;
    font-weight: 500;
  }
}

.dep-note {
  margin: 0;
  max-width: 560px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.dep-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  color: var(--faint);
  font-size: 9px;
  white-space: nowrap;

  .cycle-count {
    color: var(--accent);
  }

  .warn {
    color: #fbbf24;
  }
}

.dep-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 0;
}

.dep-view-toggle {
  display: flex;
  border: 1px solid var(--line);
}

.dep-view-toggle button {
  padding: 5px 10px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 10px;
  cursor: pointer;

  &:last-child {
    border-right: 0;
  }

  &.active {
    background: var(--accent-soft);
    color: var(--accent);
  }
}

.dep-search {
  input {
    width: 190px;
    padding: 6px 8px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 11px;
    outline: none;

    &:focus {
      border-color: var(--accent);
    }
  }
}

.dep-hint {
  margin-left: auto;
  color: var(--faint);
  font-size: 8px;
}

.dep-canvas {
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--line);
  background:
    linear-gradient(var(--line) 1px, transparent 1px),
    linear-gradient(90deg, var(--line) 1px, transparent 1px);
  background-size: 48px 48px;
}

.dep-svg {
  display: block;
  width: 100%;
  height: auto;
  min-height: 380px;
}

.dep-edge {
  fill: none;
  stroke: currentColor;
  stroke-width: 1;
  opacity: 0.5;
  transition: opacity 0.14s, stroke-width 0.14s;

  &.active {
    opacity: 0.9;
    stroke-width: 1.5;
  }

  &.muted {
    opacity: 0.08;
  }
}

.dep-node {
  cursor: pointer;
  outline: none;

  rect {
    fill: var(--panel);
    stroke: var(--line-strong);
    stroke-width: 1;
  }

  i {
    position: relative;
  }

  text {
    fill: var(--text);
    font-family: var(--font-display);
    font-size: 12px;
    pointer-events: none;
  }

  .node-count {
    fill: var(--faint);
    font-family: var(--font-ui);
    font-size: 8px;
  }

  &:hover,
  &:focus-visible,
  &.selected,
  &.matched {
    rect {
      stroke: var(--accent);
      stroke-width: 1.5;
    }
  }

  &.selected rect {
    fill: var(--accent-soft);
  }

  &.cycle rect {
    stroke: var(--accent);
    stroke-dasharray: 3 3;
  }

  &.entry rect {
    stroke-width: 2;
  }

  &.muted {
    opacity: 0.25;
  }
}

.dep-empty {
  padding: 36px 0;
  border: 1px solid var(--line);
  color: var(--muted);
  text-align: center;

  p {
    margin: 0 0 6px;
    color: var(--text);
  }

  span {
    font-size: 11px;
  }
}

.dep-mobile {
  display: none;
}

.dep-detail {
  margin-top: 12px;
  padding: 14px;
  border: 1px solid var(--line);
  background: var(--panel-soft, var(--panel));
}

.dep-detail-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);

  h3 {
    margin: 3px 0;
    font-family: var(--font-display);
    font-size: 19px;
    font-weight: 500;
  }
}

.dep-path {
  margin: 0;
  color: var(--faint);
  font-size: 9px;
}

.dep-close {
  align-self: flex-start;
  padding: 4px 7px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 9px;
  cursor: pointer;

  &:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
}

.dep-detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding-top: 12px;

  .label {
    display: block;
    margin-bottom: 4px;
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.08em;
  }

  strong {
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 500;
  }
}

.dep-link-list {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.dep-file-list {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--line);

  .label {
    margin: 0 0 6px;
    color: var(--faint);
    font-size: 8px;
    letter-spacing: 0.08em;
  }
}

.dep-file-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 6px 4px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--text);
  text-align: left;
  font-size: 11px;
  cursor: pointer;

  &:hover {
    color: var(--accent);
  }

  .mono {
    color: var(--faint);
    font-size: 9px;
    white-space: nowrap;
  }
}

@media (max-width: 720px) {
  .dep-head {
    display: block;
  }

  .dep-stats {
    justify-content: flex-start;
    margin-top: 8px;
  }

  .dep-hint {
    display: none;
  }

  .dep-canvas {
    display: none;
  }

  .dep-mobile {
    display: block;
    border: 1px solid var(--line);
  }

  .dep-mobile-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 10px;
    border-bottom: 1px solid var(--line);
    cursor: pointer;

    &:last-child {
      border-bottom: 0;
    }

    .dot {
      width: 6px;
      height: 6px;
      flex: none;
    }

    b {
      font-family: var(--font-display);
      font-size: 13px;
      font-weight: 500;
    }

    .mono {
      margin-left: auto;
      color: var(--faint);
      font-size: 8px;
    }
  }

  .dep-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
