<script setup>
import { computed } from "vue";

const props = defineProps({
  techs: { type: Array, default: () => [] },
});
const emit = defineEmits(["open"]);

const LAYER_COLORS = {
  前端: "#e879f9",
  后端: "#67e8f9",
  "数据与存储": "#fbbf24",
  "Agent / AI": "#a78bfa",
  语言与运行时: "#94a3b8",
  基础设施: "#38bdf8",
  工程效率: "#34d399",
  其他: "#64748b",
};

const layers = computed(() => {
  const layerMap = new Map();
  props.techs.forEach((tech) => {
    const layerName = tech.layer || "其他";
    const functionName = tech.function || tech.category || "其他能力";
    if (!layerMap.has(layerName)) {
      layerMap.set(layerName, {
        name: layerName,
        order: Number(tech.layer_order ?? 999),
        functions: new Map(),
      });
    }
    const layer = layerMap.get(layerName);
    if (!layer.functions.has(functionName)) {
      layer.functions.set(functionName, {
        name: functionName,
        order: Number(tech.function_order ?? 999),
        techs: [],
      });
    }
    layer.functions.get(functionName).techs.push(tech);
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

const layout = computed(() => {
  const ROW = 42;
  const COL_LAYER = 18;
  const COL_FUNCTION = 294;
  const COL_TECH = 636;
  const LAYER_RIGHT = COL_LAYER + 132;
  const FUNCTION_RIGHT = COL_FUNCTION + 182;
  const LAYER_JUNCTION = LAYER_RIGHT + (COL_FUNCTION - LAYER_RIGHT) / 2;
  const FUNCTION_JUNCTION = FUNCTION_RIGHT + (COL_TECH - FUNCTION_RIGHT) / 2;
  const WIDTH = 884;
  const layerNodes = [];
  const functionNodes = [];
  const techNodes = [];
  const paths = [];
  let y = 54;

  layers.value.forEach((layer) => {
    const layerStart = y;
    const layerFunctions = [];
    layer.functions.forEach((fn) => {
      const fnStart = y;
      const fnTechTops = [];
      fn.techs.forEach((tech) => {
        const center = y + ROW / 2;
        fnTechTops.push(center);
        techNodes.push({
          tech,
          top: center,
          left: COL_TECH,
          color: LAYER_COLORS[layer.name] || "var(--accent)",
        });
        y += ROW;
      });
      const center = fnTechTops.length ? fnStart + (y - fnStart) / 2 : fnStart + ROW / 2;
      layerFunctions.push({ fn, top: center });
      functionNodes.push({
        fn,
        top: center,
        left: COL_FUNCTION,
        color: LAYER_COLORS[layer.name] || "var(--accent)",
        techTops: fnTechTops,
      });
      y += 14;
    });

    const layerCenter = layerFunctions.length
      ? layerFunctions.reduce((total, item) => total + item.top, 0) / layerFunctions.length
      : layerStart + ROW / 2;
    const color = LAYER_COLORS[layer.name] || "var(--accent)";
    layerNodes.push({
      layer,
      top: layerCenter,
      left: COL_LAYER,
      color,
    });

    // 分叉点放在两列中间：先出一条主干，再在中间垂直分叉到各功能。
    if (layerFunctions.length) {
      let d = `M ${LAYER_RIGHT} ${layerCenter} H ${LAYER_JUNCTION}`;
      layerFunctions.forEach((item) => {
        d += ` M ${LAYER_JUNCTION} ${layerCenter} V ${item.top} H ${COL_FUNCTION}`;
      });
      paths.push({ d, color });
    }
    y += 10;
  });

  functionNodes.forEach((node) => {
    if (!node.techTops.length) return;
    let d = `M ${FUNCTION_RIGHT} ${node.top} H ${FUNCTION_JUNCTION}`;
    node.techTops.forEach((techTop) => {
      d += ` M ${FUNCTION_JUNCTION} ${node.top} V ${techTop} H ${COL_TECH}`;
    });
    paths.push({ d, color: node.color });
  });

  return {
    width: WIDTH,
    height: Math.max(200, y + 24),
    layerNodes,
    functionNodes,
    techNodes,
    paths,
  };
});

function open(tech) {
  emit("open", tech.key);
}
</script>

<template>
  <div class="tech-graph">
    <div class="graph-head">
      <span>层级 / LAYER</span>
      <span>功能 / FUNCTION</span>
      <span>技术 / TECH</span>
    </div>

    <div class="graph-canvas" :style="{ height: `${layout.height}px`, width: `${layout.width}px` }">
      <svg class="graph-lines" :viewBox="`0 0 ${layout.width} ${layout.height}`" aria-hidden="true">
        <path
          v-for="(edge, index) in layout.paths"
          :key="index"
          :d="edge.d"
          :stroke="edge.color"
          fill="none"
          stroke-width="1"
          opacity="0.55"
        />
      </svg>

      <div
        v-for="node in layout.layerNodes"
        :key="`layer-${node.layer.name}`"
        class="graph-node layer-node"
        :style="{ top: `${node.top}px`, left: `${node.left}px`, '--node-color': node.color }"
      >
        <i></i>
        <b>{{ node.layer.name }}</b>
        <span>{{ node.layer.functions.length }} 功能</span>
      </div>

      <div
        v-for="node in layout.functionNodes"
        :key="`function-${node.fn.name}`"
        class="graph-node function-node"
        :style="{ top: `${node.top}px`, left: `${node.left}px`, '--node-color': node.color }"
      >
        <b>{{ node.fn.name }}</b>
        <span>{{ node.fn.techs.length }} 项</span>
      </div>

      <button
        v-for="node in layout.techNodes"
        :key="`tech-${node.tech.key}`"
        class="graph-node tech-node"
        type="button"
        :style="{ top: `${node.top}px`, left: `${node.left}px`, '--node-color': node.color }"
        :title="node.tech.role || node.tech.name"
        @click="open(node.tech)"
      >
        <i></i>
        <b>{{ node.tech.name }}</b>
        <span>{{ node.tech.version ? `v${node.tech.version}` : "版本未知" }}</span>
      </button>
    </div>

    <div class="graph-tree">
      <section v-for="layer in layers" :key="layer.name" class="tree-layer">
        <h4>{{ layer.name }}</h4>
        <div v-for="fn in layer.functions" :key="fn.name" class="tree-function">
          <h5>{{ fn.name }}</h5>
          <div class="tree-techs">
            <button v-for="tech in fn.techs" :key="tech.key" type="button" @click="open(tech)">
              <b>{{ tech.name }}</b>
              <span>{{ tech.version ? `v${tech.version}` : "版本未知" }}</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped lang="less">
.tech-graph {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.graph-head {
  display: grid;
  grid-template-columns: 294px 342px 1fr;
  gap: 0;
  padding: 0 0 8px;
  border-bottom: 1px solid var(--line-strong);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.08em;

  span:nth-child(2) {
    padding-left: 18px;
  }

  span:nth-child(3) {
    padding-left: 34px;
  }
}

.graph-canvas {
  position: relative;
  margin-top: 10px;
}

.graph-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.graph-node {
  position: absolute;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 5px 8px;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
  text-align: left;

  i {
    width: 6px;
    height: 6px;
    flex: none;
    background: var(--node-color);
  }

  b {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }

  span {
    margin-left: auto;
    color: var(--faint);
    .mono();
    font-size: 8px;
    white-space: nowrap;
  }
}

.layer-node {
  width: 132px;
  border-color: color-mix(in srgb, var(--node-color) 48%, var(--line));
  background: color-mix(in srgb, var(--node-color) 8%, var(--panel));

  b {
    font-family: var(--font-display);
    font-size: 13px;
  }
}

.function-node {
  width: 182px;
  border-left: 0;

  b {
    font-size: 11px;
  }
}

.tech-node {
  width: 230px;
  cursor: pointer;
  transition: border-color 0.14s, background 0.14s;
  .focus-ring();

  b {
    font-family: var(--font-display);
    font-size: 13px;
  }

  &:hover,
  &:focus-visible {
    border-color: var(--node-color);
    background: color-mix(in srgb, var(--node-color) 9%, var(--panel));
  }
}

.graph-tree {
  display: none;
}

@media (max-width: 960px) {
  .graph-head,
  .graph-canvas {
    display: none;
  }

  .graph-tree {
    display: block;
    padding-top: 4px;
    border-top: 1px solid var(--line-strong);
  }
}

.tree-layer {
  padding: 12px 0;
  border-bottom: 1px solid var(--line);

  > h4 {
    margin: 0 0 8px;
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 500;
  }
}

.tree-function {
  padding: 6px 0 8px 12px;
  border-left: 1px solid var(--line-strong);

  > h5 {
    margin: 0 0 6px;
    color: var(--muted);
    font-size: 11px;
    font-weight: 400;
  }
}

.tree-techs {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.tree-techs button {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-right: 0;
  background: transparent;
  color: var(--text);
  cursor: pointer;

  &:last-child {
    border-right: 1px solid var(--line);
  }

  b {
    font-family: var(--font-display);
    font-size: 12px;
    font-weight: 500;
  }

  span {
    color: var(--faint);
    .mono();
    font-size: 8px;
  }
}
</style>
