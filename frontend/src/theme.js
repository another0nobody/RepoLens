// 页面视觉风格元数据（纯数据，不访问 DOM）。
//
// 风格选择保存在 localStorage，具体颜色/字体/背景在 styles/global.less 里
// 通过 [data-style="..."] 实现。这里的 colors 只用于选择器里的迷你预览。

export const STYLE_OPTIONS = [
  {
    key: "aurora",
    label: "极光",
    en: "Aurora",
    tagline: "冷色玻璃 · 光晕",
    description: "默认风格：深空蓝黑、青色与紫色光晕，适合长时间阅读报告。",
    colors: {
      dark: { bg: "#05070e", panel: "#0e1525", text: "#e9eefb", accent: "#67e8f9", accent2: "#a78bfa" },
      light: { bg: "#f4f7fc", panel: "#ffffff", text: "#101828", accent: "#0891b2", accent2: "#7c3aed" },
    },
  },
  {
    key: "paper",
    label: "纸境",
    en: "Paper",
    tagline: "暖纸 · 衬线 · 编辑感",
    description: "米白纸张、墨色衬线标题与暖橙点缀，像一本技术刊物。",
    colors: {
      dark: { bg: "#17130e", panel: "#241e16", text: "#f4ead6", accent: "#f59e0b", accent2: "#5eead4" },
      light: { bg: "#f3ecdd", panel: "#fffaf0", text: "#2d251a", accent: "#b45309", accent2: "#0f766e" },
    },
  },
  {
    key: "terminal",
    label: "终端",
    en: "Terminal",
    tagline: "磷光绿 · 等宽 · CRT",
    description: "黑底磷光绿、等宽字体、扫描线与硬边卡片，像打开一台老终端。",
    colors: {
      dark: { bg: "#020604", panel: "#03150b", text: "#c8ffd9", accent: "#4ade80", accent2: "#facc15" },
      light: { bg: "#edf6ea", panel: "#f8fff6", text: "#0d2a16", accent: "#15803d", accent2: "#a16207" },
    },
  },
  {
    key: "neon",
    label: "霓虹",
    en: "Neon",
    tagline: "紫粉 · 发光 · 赛博",
    description: "深紫夜色、霓虹青粉与更强的辉光，适合展示和演示。",
    colors: {
      dark: { bg: "#0a0018", panel: "#1a0730", text: "#faedff", accent: "#22d3ee", accent2: "#e879f9" },
      light: { bg: "#fbf5ff", panel: "#ffffff", text: "#241133", accent: "#7c3aed", accent2: "#db2777" },
    },
  },
  {
    key: "sakura",
    label: "樱",
    en: "Sakura",
    tagline: "樱粉 · 柔光 · 轻盈",
    description: "樱花粉与奶油白、柔和圆角与轻光晕，更轻松友好。",
    colors: {
      dark: { bg: "#1b0e15", panel: "#2a1420", text: "#ffeaf3", accent: "#f9a8d4", accent2: "#c4b5fd" },
      light: { bg: "#fff6f8", panel: "#ffffff", text: "#3b2430", accent: "#db2777", accent2: "#7c3aed" },
    },
  },
  {
    key: "sky",
    label: "晴空",
    en: "Sky",
    tagline: "蓝天 · 白云 · 日光",
    description: "晴空蓝、云朵白与阳光金，柔和圆角和轻盈云层，最不“科技味”；选择时自动切到浅色。",
    colors: {
      dark: { bg: "#071b33", panel: "#0e2a47", text: "#e7f6ff", accent: "#7dd3fc", accent2: "#38bdf8" },
      light: { bg: "#eaf7ff", panel: "#ffffff", text: "#10344d", accent: "#0284c7", accent2: "#38bdf8" },
    },
  },
];

export const STYLE_KEYS = STYLE_OPTIONS.map((item) => item.key);
export const DEFAULT_STYLE = "aurora";

export const STYLE_META = {
  aurora: { dark: "#05070e", light: "#f4f7fc" },
  paper: { dark: "#17130e", light: "#f3ecdd" },
  terminal: { dark: "#020604", light: "#edf6ea" },
  neon: { dark: "#0a0018", light: "#fbf5ff" },
  sakura: { dark: "#1b0e15", light: "#fff6f8" },
  sky: { dark: "#071b33", light: "#eaf7ff" },
};

export function normalizeStyle(style) {
  return STYLE_KEYS.includes(style) ? style : DEFAULT_STYLE;
}

export function styleLabel(style) {
  return STYLE_OPTIONS.find((item) => item.key === style)?.label || "极光";
}
