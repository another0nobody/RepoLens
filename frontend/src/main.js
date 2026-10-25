import { createApp } from "vue";

import App from "./App.vue";
import { normalizeStyle } from "./theme";
import "./styles/global.less";

// 在挂载前先应用一次主题，减少刷新时的闪烁。
// （不使用内联 script，是为了兼容生产环境的 CSP。）
try {
  const saved = localStorage.getItem("repolens-theme");
  document.documentElement.dataset.theme = saved === "light" || saved === "dark" ? saved : "dark";
  document.documentElement.dataset.style = normalizeStyle(localStorage.getItem("repolens-style"));
} catch {
  /* 忽略隐私模式下的 localStorage 异常 */
}

createApp(App).mount("#app");
