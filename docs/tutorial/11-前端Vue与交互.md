# 第 11 章：前端 Vue 与交互

> 阅读时间：75–120 分钟
> 前置：第 09/10 章
> 目标：理解报告页是如何把 JSON 变成可浏览、可核对的界面

---

## 11.1 技术栈

```text
Vue 3 Composition API
Vite 6
Less
无 UI 组件库
```

设计：

```text
Contact Sheet / 暗房接触印样
黑色工作台 + 银白印样 + 单一 grease red
```

没有 Element Plus / Ant Design，所有组件都是项目自己写的。

---

## 11.2 三个视图

`App.vue` 根据 `state.view` 切换：

```text
home    首页：输入来源
run     运行页：时间线/工具流/审批
report  报告页：技术栈/模块/架构/学习/追问
```

不是 Vue Router 的多页面，而是单页状态切换。
URL 通过 query 参数保存：

```text
?report=<run_id>&tab=risks
```

所以可以分享报告链接。

---

## 11.3 Vue 基础

### 组件

每个 `.vue` 文件是一个组件：

```text
<script setup>   逻辑
<template>       HTML
<style scoped>   样式
```

### `ref`

```js
const loading = ref(false);
loading.value = true;
```

模板里自动解包：

```html
<div v-if="loading">加载中</div>
```

### `computed`

```js
const visibleTabs = computed(() => ...);
```

它依赖响应式数据，自动更新。

### `props` / `emit`

```js
defineProps({ report: Object });
const emit = defineEmits(["open"]);
emit("open", tech.key);
```

父组件：

```html
<TechCard :tech="tech" @open="openTech" />
```

### `v-if` / `v-for`

```html
<section v-if="report">
  <article v-for="tech in techs" :key="tech.key">...</article>
</section>
```

---

## 11.4 store.js：单一状态源

项目没有 Vuex/Pinia，使用一个 `reactive`：

```js
export const state = reactive({
  view: "home",
  run: null,
  report: null,
  events: [],
  chat: {...},
  drawers: {...},
  codeViewer: {...},
});
```

业务动作：

```js
export async function startAnalysis(source) { ... }
export async function loadReport(runId) { ... }
export function switchTab(tab) { ... }
export async function openCode(path, line) { ... }
```

组件不直接写 `state.report = ...`，而是调用 action。

好处：

- 状态变化集中；
- 刷新/恢复逻辑集中；
- SSE 重连集中；
- 深链接集中。

---

## 11.5 API 层

`api.js` 封装：

```js
fetchJSON(url, options)
fetchChatHistory(runId)
fetchDiff(base, target)
fetchCode(runId, path, line)
fetchRisks(runId)
fetchAdr(runId, tech)
fetchGrounding(runId, text)
fetchSemanticGrounding(runId, text)
streamChatRequest(payload, onEvent)
```

`fetchJSON` 统一处理：

- JSON/text；
- HTTP 错误 → `Error(message)`；
- 前端 catch 后显示 Toast。

SSE 不是 `EventSource`，而是 `fetch` + `ReadableStream`，因为追问是 POST，需要请求体。

---

## 11.6 报告页布局

```text
报告头
4 格统计
先看什么
摘要 + 亮点（默认 2 条）
警告一行
核心 Tab / 更多视图
Tab 内容
```

### 报告头

```text
仓库名 / 来源 / AI 状态
重新分析  更多 ▾
```

「更多」：

```text
对比历史 / 复制链接 / 导出 Markdown / 导出 JSON
```

### 统计

```text
文件 / 代码行数 / 技术项 / 风险提示
```

风险格点击进入风险面板。

### 先看什么

三列：

```text
先读文件 / 核心依赖 / 先注意
```

风险列有：

```text
首个风险
查看全部 N 项风险 →
30 分钟路线 · N 步  继续 →
```

不重复展示完整学习步骤。

---

## 11.7 核心 Tab 与更多视图

默认：

```text
技术栈
模块地图
架构解读
学习路线
追问
```

「更多视图」：

```text
依赖图
风险面板
分析过程
```

为什么：

- 初学者先看技术、模块、架构、学习、追问；
- 依赖图/过程属于调试或深度分析；
- 深链接打开高级 Tab 时，会临时显示该 Tab。

---

## 11.8 技术栈

`ReportView` 负责：

- 分类 chips；
- 分组/层级图；
- 搜索；
- 技术卡片。

`TechCard.vue`：

```text
编号 / 分类
技术名 / 版本
职责
置信度 / 模块数 / 箭头
```

证据数、AI 推断标记在 `TechDrawer` 里，不挤在卡片底部。

技术栈保留全量展示。
移动端分类 chips 单行横向滚动。

---

## 11.9 模块地图与依赖图

`ModuleMap.vue`：

- 按技术展开；
- 文件:行号；
- 模块角色；
- 大概功能；
- 复制路径 / 打开代码。

`DependencyGraph.vue`：

- 文件级有向图；
- 目录/文件视图；
- 搜索；
- 入边/出边；
- 循环标记。

两者用途不同：

```text
模块地图：某项技术用在哪
依赖图：文件之间怎么依赖
```

---

## 11.10 架构解读

`ArchitectureTab.vue` 现在只保留：

- 架构分层；
- 风险入口；
- 关键文件与目录规模。

它不再重复：

- 完整风险列表；
- 完整学习路径。

风险去风险面板，学习去学习路线 Tab。

---

## 11.11 风险面板

`RiskPanel.vue`：

- 总数 + 高/中/低计数；
- 筛选；
- 严重度；
- 详情；
- 建议；
- 证据路径 → 代码查看器。

不显示“26 分”这种伪精确分数。

---

## 11.12 学习路线

`LearningPath.vue`：

- 完整步骤；
- 勾选；
- 进度；
- 重置；
- 步骤中的文件 → 代码查看器。

进度：

```text
localStorage: repolens-learning:<run_id>
```

只保存在当前浏览器。

---

## 11.13 追问

`ChatTab.vue`：

- 消息气泡；
- 技术深挖模板；
- 引用核对徽标；
- 可选“深度核对”；
- 流式输出。

用户输入 → `store.sendChat` → POST SSE → 逐 token 更新 assistant 消息。

---

## 11.14 代码查看器

`CodeViewer.vue`：

- 行号；
- 高亮；
- 语言；
- 复制位置/片段；
- 脱敏标记；
- 截断标记。

从：

- 技术证据；
- 模块路径；
- 风险证据；
- 学习路线步骤；

打开。

---

## 11.15 深链接

URL 示例：

```text
http://127.0.0.1:8765/?report=<run_id>
http://127.0.0.1:8765/?report=<run_id>&tab=risks
```

`store` 解析：

- `report` → 加载报告；
- `tab` → 切换；
- 无效 tab → 忽略。

分享链接不需要登录，因为服务是本地单机。

---

## 11.16 响应式与移动端

目标：

- 390px 无横向溢出；
- 技术 chips 横向滚动；
- 统计 2×2；
- Tab 横向滚动；
- 代码块横向滚动；
- 抽屉全宽。

`ReportView` 的 `@media` 负责大部分。

---

## 11.17 Contact Sheet 设计

关键约束：

- 0px 圆角；
- 1px 边框；
- 红色只用于动作/选中；
- 不用渐变文字/玻璃拟态；
- 字体：显示、正文、mono；
- 深/浅主题都完整。

改 UI 时不要只改主色，检查：

```text
边框 / 面板 / 印样纸色 / 字号 / 对比度
```

---

## 11.18 构建

```powershell
cd frontend
npm install
npm run build
```

输出：

```text
static/dist/
```

Python 服务直接托管，不需要 Node 运行时。

开发模式：

```powershell
npm run dev
```

5173 代理 `/api` 到 8765。

---

## 11.19 调试

### 页面不更新

- 没有 `npm run build`；
- 浏览器缓存；
- 8765 仍是旧进程。

### API 404/500

- Network 看响应；
- Console 看异常；
- 后端终端看 traceback。

### 布局溢出

- Elements 看 `scrollWidth`；
- 检查固定宽度、`white-space`、长路径。

### SSE 不更新

- Network 看 `/api/events`；
- 看事件是否 `seq` 递增；
- 看 `from` 参数；
- 浏览器是否限流。

---

## 11.20 自测

1. `store.js` 为什么是单一状态源？
2. `ref` 和 `computed` 的区别？
3. 追问为什么不用 `EventSource`？
4. 默认 5 个 Tab 是什么？
5. “更多视图”里有什么？
6. 技术卡为什么不显示证据数？
7. 架构解读为什么没有学习路径？
8. `static/dist` 与 `frontend/src` 的关系？

能回答后进入：[12 测试与评测](12-测试与评测.md)。
