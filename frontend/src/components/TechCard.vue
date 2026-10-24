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
    <div class="tech-top">
      <div class="tech-id">
        <div class="tech-name">{{ tech.name }}</div>
        <div class="tech-version mono">{{ tech.version ? `v${tech.version}` : "版本未知" }}</div>
      </div>
      <span class="tag cat">{{ categoryIcon(tech.category) }} {{ tech.category }}</span>
    </div>

    <p class="tech-role">{{ tech.role || tech.hint || "暂无说明" }}</p>

    <div class="tech-foot">
      <span class="conf"><i :class="confidence"></i>置信度 {{ tech.confidence || "中" }}</span>
      <span class="sep"></span>
      <span>{{ fmtNumber(tech.module_count) }} 个模块</span>
      <span class="sep"></span>
      <span>{{ fmtNumber((tech.evidence || []).length) }} 条证据</span>
      <span v-if="tech.ai_inferred" class="ai-flag"><Icon name="spark" :size="11" /> AI 推断</span>
      <span class="open-arrow" aria-hidden="true"><Icon name="arrowRight" :size="14" /></span>
    </div>
  </article>
</template>

<style scoped lang="less">
.tech-card {
  position: relative;
  padding: 17px 18px 14px;
  border-radius: @radius-lg;
  border: 1px solid var(--line);
  background: var(--panel);
  cursor: pointer;
  overflow: hidden;
  animation: card-in 0.38s @ease-out both;
  animation-delay: calc(var(--i) * 24ms);
  transition: transform 0.2s @ease-out, border-color 0.2s, box-shadow 0.2s;
  .focus-ring();

  &::before {
    content: "";
    position: absolute;
    left: 0;
    top: 16px;
    bottom: 16px;
    width: 2px;
    border-radius: 2px;
    background: var(--c);
    opacity: 0.85;
    transition: top 0.2s, bottom 0.2s;
  }

  &:hover {
    transform: translateY(-3px);
    border-color: color-mix(in srgb, var(--c) 40%, var(--line));
    box-shadow: var(--shadow-soft);

    &::before {
      top: 10px;
      bottom: 10px;
    }

    .open-arrow {
      opacity: 1;
      transform: translateX(0);
    }
  }
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tech-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.tech-name {
  font-size: 16px;
  font-weight: 650;
  letter-spacing: -0.2px;
}

.tech-version {
  margin-top: 2px;
  color: var(--faint);
  font-size: 9.5px;
}

.tag.cat {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 10px;
}

.tech-role {
  margin: 9px 0 12px;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.65;
  .text-clamp(3);
}

.tech-foot {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--faint);
  font-size: 10px;
  flex-wrap: wrap;
}

.conf {
  display: inline-flex;
  align-items: center;
  gap: 5px;

  i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--faint);

    &.high {
      background: var(--good);
      box-shadow: 0 0 7px var(--good);
    }

    &.mid {
      background: var(--warn);
    }
  }
}

.sep {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--faint);
  opacity: 0.6;
}

.ai-flag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: auto;
  color: var(--accent-2);
}

.open-arrow {
  position: absolute;
  right: 16px;
  bottom: 13px;
  color: var(--c);
  opacity: 0;
  transform: translateX(-4px);
  transition: 0.2s @ease-out;
}
</style>
