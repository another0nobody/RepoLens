<script setup>
import { computed } from "vue";

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 1.7 },
});

const ICONS = {
  arrowRight: ["M5 12h14", "m13 6 6 6-6 6"],
  arrowLeft: ["M19 12H5", "m11 18-6-6 6-6"],
  chevron: ["m9 18 6-6-6-6"],
  down: ["m6 9 6 6 6-6"],
  search: ["M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z", "m21 21-4.3-4.3"],
  close: ["M6 6l12 12", "M18 6 6 18"],
  copy: ["M9 9h10v10H9z", "M5 15H4V4h11v1"],
  check: ["m5 12 4 4L19 6"],
  warning: ["M12 4 2.8 20h18.4L12 4Z", "M12 9v5", "M12 17h.01"],
  history: ["M3 12a9 9 0 1 0 3-6.7", "M3 4v5h5", "M12 7v5l3 2"],
  book: ["M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22V5.5Z", "M4 17.5A2.5 2.5 0 0 1 6.5 15H20"],
  sun: ["M12 4V2", "M12 22v-2", "M4 12H2", "M22 12h-2", "M5.6 5.6 4.2 4.2", "M19.8 19.8l-1.4-1.4", "M18.4 5.6l1.4-1.4", "M4.2 19.8l1.4-1.4", "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z"],
  moon: ["M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"],
  refresh: ["M20 11a8 8 0 1 0-2.3 5.7", "M20 4v7h-7"],
  download: ["M12 3v12", "m7 10 5 5 5-5", "M4 21h16"],
  play: ["m8 5 11 7-11 7V5Z"],
  github: ["M9 19c-4 1.4-4-2.2-6-2.7", "M15 21v-3.4c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.7 4.7 0 0 0-1.3-3.2 4.3 4.3 0 0 0-.1-3.2s-1-.3-3.3 1.3a11 11 0 0 0-5.6 0C6.4 2.9 5.4 3.2 5.4 3.2a4.3 4.3 0 0 0-.1 3.2A4.7 4.7 0 0 0 4 9.6c0 4.6 2.7 5.7 5.5 6-.4.4-.5.9-.5 1.4V21"],
  folder: ["M3 6.5A2.5 2.5 0 0 1 5.5 4H10l2 2h6.5A2.5 2.5 0 0 1 21 8.5v9A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5v-11Z"],
  spark: ["m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z", "M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"],
  terminal: ["m4 6 5 6-5 6", "M12 18h8"],
  layers: ["m12 3 9 5-9 5-9-5 9-5Z", "m3 12 9 5 9-5", "m3 16 9 5 9-5"],
  code: ["m8 8-4 4 4 4", "m16 8 4 4-4 4", "m13 5-2 14"],
  external: ["M14 4h6v6", "M20 4l-9 9", "M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"],
};

const paths = computed(() => ICONS[props.name] || ICONS.spark);
const pixelSize = computed(() => (typeof props.size === "number" ? `${props.size}px` : props.size));
</script>

<template>
  <svg
    :width="pixelSize"
    :height="pixelSize"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="icon"
  >
    <path v-for="(d, index) in paths" :key="index" :d="d" />
  </svg>
</template>

<style scoped>
.icon {
  display: block;
  flex: none;
}
</style>
