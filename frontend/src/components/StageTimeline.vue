<script setup>
import { computed } from "vue";

import { STAGES } from "../utils";

const props = defineProps({
  stage: { type: Number, default: 0 },
  status: { type: String, default: "running" },
});

const percent = computed(() => Math.min(100, Math.round((Math.min(props.stage, 4) / 4) * 100)));

function itemState(index) {
  if (props.status === "error" && index === Math.min(props.stage, 3)) return "error";
  if (index < props.stage || props.stage >= 4) return "done";
  if (index === props.stage) return props.status === "running" ? "active" : "done";
  return "pending";
}
</script>

<template>
  <ol class="timeline" :style="{ '--p': `${percent}%` }">
    <div class="track" aria-hidden="true"><span class="fill"></span></div>
    <li v-for="(stage, index) in STAGES" :key="stage.key" :class="itemState(index)">
      <span class="dot" aria-hidden="true">
        <span v-if="itemState(index) === 'done'" class="check">✓</span>
        <span v-else-if="itemState(index) === 'error'" class="cross">!</span>
      </span>
      <span class="copy">
        <b>{{ stage.label }}</b>
        <small>{{ stage.hint }}</small>
      </span>
      <span class="index">{{ String(index + 1).padStart(2, "0") }}</span>
    </li>
  </ol>
</template>

<style scoped lang="less">
.timeline {
  position: relative;
  list-style: none;
  margin: 0;
  padding: 0;

  .track {
    position: absolute;
    left: 8px;
    top: 8px;
    bottom: 20px;
    width: 2px;
    border-radius: 2px;
    background: var(--line);
    overflow: hidden;
  }

  .fill {
    display: block;
    width: var(--p);
    height: 100%;
    background: linear-gradient(var(--accent), var(--accent-2));
    transition: height 0.5s @ease-out;
  }
}

li {
  position: relative;
  display: grid;
  grid-template-columns: 18px 1fr auto;
  gap: 12px;
  align-items: start;
  padding: 0 0 20px;
  color: var(--faint);

  &:last-child {
    padding-bottom: 0;
  }

  .dot {
    position: relative;
    z-index: 1;
    display: grid;
    place-items: center;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    border-radius: 50%;
    border: 2px solid var(--line-strong);
    background: var(--bg);
    font-size: 9px;
    font-weight: 700;
    color: #04121a;
    transition: 0.3s @ease-out;
  }

  .copy {
    display: flex;
    flex-direction: column;
    line-height: 1.45;

    b {
      font-size: 12.5px;
      font-weight: 600;
    }

    small {
      font-size: 10.5px;
      color: var(--faint);
    }
  }

  .index {
    .mono();
    font-size: 9.5px;
    color: var(--faint);
    letter-spacing: 1px;
  }

  &.done {
    color: var(--muted);

    .dot {
      border-color: var(--good);
      background: var(--good);
    }
  }

  &.active {
    color: var(--text);

    .dot {
      border-color: var(--accent);
      background: var(--bg);
      box-shadow: 0 0 0 4px var(--accent-soft), 0 0 18px -4px var(--accent);
      animation: dot-breathe 1.8s ease-in-out infinite;
    }

    b {
      color: var(--text);
    }
  }

  &.error {
    color: var(--bad);

    .dot {
      border-color: var(--bad);
      background: var(--bad);
      color: #fff;
    }
  }
}

@keyframes dot-breathe {
  0%,
  100% {
    box-shadow: 0 0 0 4px var(--accent-soft), 0 0 18px -4px var(--accent);
  }
  50% {
    box-shadow: 0 0 0 7px transparent, 0 0 18px -2px var(--accent);
  }
}
</style>
