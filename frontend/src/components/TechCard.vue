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
const code = computed(() => `C${String(props.index + 1).padStart(2, "0")}`);
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
    <span class="tech-code mono">{{ code }}</span>

    <div class="tech-main">
      <div class="tech-title">
        <span class="tech-name">{{ tech.name }}</span>
        <span class="tech-version mono">{{ tech.version ? `v${tech.version}` : "版本未知" }}</span>
      </div>
      <p class="tech-role">{{ tech.role || tech.hint || "暂无说明" }}</p>
    </div>

    <span class="tech-cat"><i :style="{ background: color }"></i>{{ tech.category }}</span>
    <span class="tech-count mono">{{ fmtNumber(tech.module_count) }}M / {{ fmtNumber((tech.evidence || []).length) }}E</span>
    <span class="tech-conf" :title="`置信度 ${tech.confidence || '中'}`"><i :class="confidence"></i></span>
    <span class="open-arrow" aria-hidden="true">↗</span>
  </article>
</template>

<style scoped lang="less">
.tech-card {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) 112px 76px 12px 14px;
  gap: 10px;
  align-items: center;
  padding: 13px 2px;
  border-bottom: 1px solid var(--line);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.14s, padding 0.14s;
  .focus-ring();

  &:hover,
  &:focus-visible {
    padding-left: 7px;
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

.tech-code {
  color: var(--accent);
  font-size: 9px;
  align-self: start;
  padding-top: 4px;
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
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.03em;
  transition: color 0.14s;
}

.tech-version {
  color: var(--faint);
  font-size: 8px;
  white-space: nowrap;
}

.tech-role {
  max-width: 68ch;
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.6;
  .text-clamp(2);
}

.tech-cat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--muted);
  font-size: 9px;

  i {
    width: 5px;
    height: 5px;
    flex: none;
  }
}

.tech-count {
  color: var(--faint);
  font-size: 8px;
  text-align: right;
  white-space: nowrap;
}

.tech-conf {
  display: grid;
  place-items: center;

  i {
    width: 5px;
    height: 5px;
    background: var(--faint);

    &.high {
      background: var(--good);
    }

    &.mid {
      background: var(--warn);
    }
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
    grid-template-columns: 34px minmax(0, 1fr) 14px;
    gap: 8px;
    padding: 12px 0;
  }

  .tech-name {
    font-size: 21px;
  }

  .tech-cat,
  .tech-count,
  .tech-conf {
    display: none;
  }

  .open-arrow {
    grid-column: 3;
    grid-row: 1;
  }
}
</style>
