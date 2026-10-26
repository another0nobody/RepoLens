<script setup>
import { computed } from "vue";

import { categoryColor, confidenceClass, fmtNumber } from "../utils";

const props = defineProps({
  tech: { type: Object, required: true },
  index: { type: Number, default: 0 },
});
const emit = defineEmits(["open"]);

const color = computed(() => categoryColor(props.tech.category));
const confidence = computed(() => confidenceClass(props.tech.confidence));
const modules = computed(() => props.tech.modules || []);
const frame = computed(() => String(props.index + 1).padStart(2, "0"));
const keyModules = computed(() =>
  (props.tech.key_modules || modules.value.map((module) => module.path) || []).slice(0, 6)
);
</script>

<template>
  <article
    class="tech-card"
    :style="{ '--c': color, '--i': index }"
    role="button"
    tabindex="0"
    :aria-label="`查看 ${tech.name} 详情`"
    :title="keyModules.join('\n') || tech.name"
    @click="emit('open', tech.key)"
    @keydown.enter.prevent="emit('open', tech.key)"
    @keydown.space.prevent="emit('open', tech.key)"
  >
    <span class="tech-index mono">{{ frame }}</span>

    <div class="tech-main">
      <div class="tech-title">
        <span class="tech-name">{{ tech.name }}</span>
        <span class="tech-version mono">{{ tech.version ? `v${tech.version}` : "版本未知" }}</span>
      </div>
      <p class="tech-role">{{ tech.role || tech.hint || "暂无说明" }}</p>
    </div>

    <div class="tech-side tech-foot">
      <span class="cat"><i :style="{ background: color }"></i>{{ tech.category }}</span>
      <span class="conf"><i :class="confidence"></i>置信度 {{ tech.confidence || "中" }}</span>
      <span>{{ fmtNumber(tech.module_count) }} 模块</span>
      <span>{{ fmtNumber((tech.evidence || []).length) }} 证据</span>
      <span v-if="tech.ai_inferred" class="ai-flag">AI 推断</span>
    </div>

    <span class="open-arrow" aria-hidden="true">↗</span>
  </article>
</template>

<style scoped lang="less">
.tech-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto 18px;
  gap: 12px;
  align-items: center;
  padding: 13px 4px;
  border-bottom: 1px solid var(--line);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.14s, padding 0.14s;
  .focus-ring();

  &:hover,
  &:focus-visible {
    padding-left: 8px;
    background: var(--panel-soft);
  }

  &:hover .tech-name,
  &:focus-visible .tech-name {
    color: var(--accent);
  }

  &:hover .open-arrow,
  &:focus-visible .open-arrow {
    color: var(--accent);
    transform: translate(1px, -1px);
  }
}

.tech-index {
  color: var(--faint);
  font-size: 9px;
  align-self: start;
  padding-top: 3px;
}

.tech-main {
  min-width: 0;
}

.tech-title {
  display: flex;
  align-items: baseline;
  gap: 9px;
  min-width: 0;
}

.tech-name {
  color: var(--text);
  font-family: var(--font-display);
  font-size: 23px;
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: -0.04em;
  transition: color 0.14s;
}

.tech-version {
  color: var(--faint);
  font-size: 8px;
  white-space: nowrap;
}

.tech-role {
  max-width: 72ch;
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
  .text-clamp(2);
}

.tech-side {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px 10px;
  max-width: 240px;
  color: var(--faint);
  font-size: 8.5px;
  line-height: 1.4;
  text-align: right;

  .cat,
  .conf {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  i {
    width: 5px;
    height: 5px;
    flex: none;
    background: var(--faint);
  }

  .conf i.high {
    background: var(--good);
  }

  .conf i.mid {
    background: var(--warn);
  }

  .ai-flag {
    color: var(--warn);
  }
}

.open-arrow {
  color: var(--faint);
  font-size: 12px;
  align-self: start;
  padding-top: 3px;
  transition: color 0.14s, transform 0.14s;
}

@media (max-width: @bp-md) {
  .tech-card {
    grid-template-columns: 27px minmax(0, 1fr) 16px;
    gap: 8px;
    padding: 12px 0;
  }

  .tech-name {
    font-size: 21px;
  }

  .tech-side {
    grid-column: 2 / 3;
    justify-content: flex-start;
    max-width: none;
    padding-top: 4px;
    text-align: left;
  }

  .tech-foot {
    grid-column: 2 / 3;
  }

  .open-arrow {
    grid-column: 3;
    grid-row: 1;
  }
}
</style>
