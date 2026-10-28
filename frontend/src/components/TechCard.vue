<script setup>
import { computed } from "vue";

import Icon from "./Icon.vue";
import { categoryColor, categoryIcon, confidenceClass, fmtNumber } from "../utils";

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
    <div class="frame-top">
      <span class="frame-no mono">{{ frame }}</span>
      <span class="frame-cat"><i :style="{ background: color }"></i>{{ tech.category }}</span>
    </div>

    <div class="tech-top">
      <div class="tech-name">{{ tech.name }}</div>
      <span class="tech-version mono">{{ tech.version ? `v${tech.version}` : "版本未知" }}</span>
    </div>

    <p class="tech-role">{{ tech.role || tech.hint || "暂无说明" }}</p>

    <div class="tech-foot">
      <span class="conf"><i :class="confidence"></i>置信度 {{ tech.confidence || "中" }}</span>
      <span class="sep"></span>
      <span>{{ fmtNumber(tech.module_count) }} 模块</span>
      <span class="sep"></span>
      <span>{{ fmtNumber((tech.evidence || []).length) }} 证据</span>
      <span v-if="tech.ai_inferred" class="ai-flag"><Icon name="spark" :size="11" /> AI 推断</span>
      <span class="open-arrow" aria-hidden="true">↗</span>
    </div>
  </article>
</template>

<style scoped lang="less">
.tech-card {
  position: relative;
  padding: 9px 10px 10px;
  border: 1px solid var(--line);
  background: var(--panel);
  cursor: pointer;
  animation: card-in 0.3s @ease-out both;
  animation-delay: calc(var(--i) * 18ms);
  transition: border-color 0.16s, background 0.16s;
  .focus-ring();

  &:hover,
  &:focus-visible {
    border-color: var(--line-strong);
    background: color-mix(in srgb, var(--panel) 80%, var(--bg));
  }

  &:hover .open-arrow,
  &:focus-visible .open-arrow {
    color: var(--accent);
    transform: translate(1px, -1px);
  }

  &:hover .frame-no {
    color: var(--accent);
  }
}

@keyframes card-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.frame-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 7px;
  border-bottom: 1px solid var(--line);
  color: var(--faint);
  .mono();
  font-size: 8px;
  letter-spacing: 0.08em;
}

.frame-no {
  transition: color 0.16s;
}

.frame-cat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: 0;
  text-transform: none;

  i {
    width: 5px;
    height: 5px;
    flex: none;
  }
}

.tech-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 9px;
  margin-top: 10px;
}

.tech-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.03em;
}

.tech-version {
  color: var(--faint);
  font-size: 8.5px;
  white-space: nowrap;
}

.tech-role {
  margin: 7px 0 12px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.65;
  .text-clamp(3);
}

.tech-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 7px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 9px;
  flex-wrap: wrap;
}

.conf {
  display: inline-flex;
  align-items: center;
  gap: 4px;

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

.sep {
  width: 2px;
  height: 2px;
  background: var(--faint);
  opacity: 0.7;
}

.ai-flag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: auto;
  color: var(--warn);
}

.open-arrow {
  color: var(--faint);
  font-size: 11px;
  transition: 0.16s @ease-out;
}
</style>
