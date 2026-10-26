import { computed, reactive } from "vue";

import { fetchJSON, streamChatRequest } from "./api";
import {
  DEFAULT_STYLE,
  STYLE_KEYS,
  STYLE_META,
  normalizeStyle,
  styleLabel,
} from "./theme";
import {
  argsPreview,
  basename,
  categoryColor,
  chatText,
  copyText,
  download,
  fmtDuration,
  fmtNumber,
  fmtTime,
  reportToMarkdown,
  safeFileName,
  toolLabel,
} from "./utils";

const THEME_KEY = "repolens-theme-field";
const STYLE_KEY = "repolens-style-field";
const savedTheme = localStorage.getItem(THEME_KEY);
const initialTheme = savedTheme === "light" || savedTheme === "dark" ? savedTheme : "light";
const initialStyle = normalizeStyle(localStorage.getItem(STYLE_KEY));

let eventSource = null;
let runTimer = null;
let hitlTimer = null;
let feedSeq = 0;
let toastSeq = 0;
let feedTs = null;

export const state = reactive({
  view: "home",
  health: null,
  examples: [],

  source: "",
  analyzing: false,

  run: null,
  report: null,
  reportLoading: false,
  events: [],
  lastSeq: -1,
  feed: [],
  feedFilter: "all",
  todos: [],
  tokens: { input: 0, output: 0 },
  elapsed: 0,
  stage: 0,
  runStatusText: "准备中",
  liveStage: "正在初始化…",

  tab: "stack",
  category: "全部",
  search: "",
  pendingTab: "",

  chat: { messages: [], streaming: false, status: "" },

  drawers: { history: false, concepts: false, styles: false, techKey: null },
  history: [],
  historyLoading: false,
  concepts: [],
  conceptsLoading: false,

  hitl: null,
  hitlRemaining: 0,
  hitlPending: "",

  toasts: [],
  theme: initialTheme,
  style: initialStyle,
  scrollProgress: 0,
});

export const currentTech = computed(() => {
  if (!state.report || !state.drawers.techKey) return null;
  return (state.report.techs || []).find((tech) => tech.key === state.drawers.techKey) || null;
});

export const stageProgress = computed(() => {
  const base = state.stage + (state.run?.status === "running" ? 0.42 : 1);
  return Math.min(100, Math.round((base / 4) * 100));
});

export const isAiAvailable = computed(() => Boolean(state.health?.ai_available));

export const filteredFeed = computed(() => {
  if (state.feedFilter === "all") return state.feed;
  return state.feed.filter((item) => item.kind === state.feedFilter);
});

// ---------------------------------------------------------------------------
// 主题 / Toast / URL
// ---------------------------------------------------------------------------
function syncMetaColor() {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) return;
  const color = STYLE_META[state.style]?.[state.theme] || STYLE_META[DEFAULT_STYLE][state.theme];
  meta.setAttribute("content", color);
}

export function applyTheme(theme) {
  state.theme = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = state.theme;
  localStorage.setItem(THEME_KEY, state.theme);
  syncMetaColor();
}

export function toggleTheme() {
  applyTheme(state.theme === "dark" ? "light" : "dark");
}

export function applyStyle(style) {
  const next = normalizeStyle(style);
  state.style = next;
  document.documentElement.dataset.style = next;
  localStorage.setItem(STYLE_KEY, next);
  syncMetaColor();
}

export function setStyle(style) {
  if (!STYLE_KEYS.includes(style)) return;
  if (style === state.style) {
    // 已经处于晴空深色时，再点一次晴空卡片 = 回到白天。
    if (style === "sky" && state.theme === "dark") {
      applyTheme("light");
      toast("晴空已切换到浅色模式", "ok", 2400);
    }
    return;
  }
  applyStyle(style);
  // 晴空是明确的「白天」风格：第一次选中时如果还在深色，自动切到浅色，
  // 避免用户看到的是深蓝夜空而不是蓝天白云。之后仍可手动切回深色。
  if (style === "sky" && state.theme === "dark") {
    applyTheme("light");
    toast("已切换到「晴空」并开启浅色模式", "ok", 2800);
    return;
  }
  toast(`已切换到「${styleLabel(style)}」风格`, "ok", 2200);
}

export function toast(message, kind = "info", timeout = 4200) {
  const id = ++toastSeq;
  state.toasts.push({ id, message: String(message), kind });
  window.setTimeout(() => dismissToast(id), timeout);
  return id;
}

export function dismissToast(id) {
  const index = state.toasts.findIndex((item) => item.id === id);
  if (index >= 0) state.toasts.splice(index, 1);
}

function updateURL(search) {
  try {
    const url = new URL(window.location.href);
    url.search = search || "";
    window.history.replaceState({}, "", url);
  } catch {
    /* 忽略 */
  }
}

function urlWithTab(tab) {
  const params = new URLSearchParams();
  if (state.report?.run_id) params.set("report", state.report.run_id);
  if (tab && tab !== "stack") params.set("tab", tab);
  return params.toString();
}

// ---------------------------------------------------------------------------
// 初始化 / 页面切换
// ---------------------------------------------------------------------------
export async function initApp() {
  applyTheme(state.theme);
  applyStyle(state.style);
  try {
    const [health, examples] = await Promise.all([fetchJSON("/api/health"), fetchJSON("/api/examples")]);
    state.health = health;
    state.examples = examples.items || [];
  } catch (error) {
    toast(`无法连接后端：${error.message}`, "error", 7000);
  }

  const params = new URLSearchParams(window.location.search);
  state.pendingTab = params.get("tab") || "";
  const reportId = params.get("report");
  const runId = params.get("run");
  if (reportId) {
    await loadReport(reportId);
  } else if (runId) {
    await resumeRun(runId);
  }
}

export function goHome() {
  if (state.run?.status === "running") {
    state.view = "run";
    return;
  }
  state.view = "home";
  updateURL("");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

export function leaveRun() {
  if (state.run?.status === "running") {
    const ok = window.confirm("分析仍在进行。离开页面不会中断后台任务，完成后可以在「历史记录」里查看。确定离开吗？");
    if (!ok) return;
    closeEvents();
    stopTimer();
    state.run.status = "background";
    toast("分析仍在后台进行，完成后可在历史记录查看", "warn", 6000);
  }
  state.view = "home";
  updateURL("");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------------------------------------------------------------------------
// 启动分析 / SSE
// ---------------------------------------------------------------------------
export async function startAnalysis(rawSource) {
  const source = String(rawSource || "").trim();
  if (!source) {
    toast("请先输入本地仓库路径或 GitHub 地址", "warn");
    return;
  }
  state.source = source;
  if (state.analyzing || state.run?.status === "running") {
    toast("已有一个分析正在进行，请稍等", "warn");
    if (state.run?.status === "running") state.view = "run";
    return;
  }

  state.analyzing = true;
  try {
    const data = await fetchJSON("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    setupRun(data, source, 0, false);
  } catch (error) {
    toast(error.message, "error", 7000);
  } finally {
    state.analyzing = false;
  }
}

function setupRun(data, source, elapsedSeconds = 0, resumed = false) {
  closeEvents();
  stopTimer();
  state.lastSeq = -1;
  state.feed = [];
  state.feedFilter = "all";
  state.events = [];
  state.todos = [];
  state.tokens = { input: 0, output: 0 };
  state.report = null;
  state.reportLoading = false;
  state.elapsed = Math.max(0, Number(elapsedSeconds) || 0);
  state.stage = 0;
  state.chat = { messages: [], streaming: false, status: "" };
  state.run = {
    runId: data.run_id,
    source,
    sourceType: data.source_type,
    repoName: data.repo_name || basename(source),
    model: data.model || state.health?.model || "",
    startedAt: Date.now() - state.elapsed * 1000,
    status: "running",
    error: "",
  };
  state.runStatusText = resumed ? "恢复进度" : "准备中";
  state.liveStage = resumed ? "正在恢复刷新前的进度…" : "正在启动 Agent…";
  feedTs = null;
  state.view = "run";
  updateURL(`run=${encodeURIComponent(data.run_id)}`);
  addFeed(resumed ? "plan" : "info", resumed ? "正在恢复刷新前的分析进度…" : `开始分析：${source}`, resumed ? "↻" : "◆");
  startTimer();
  connectEvents(data.run_id);
}

function connectEvents(runId) {
  eventSource = new EventSource(`/api/events?run_id=${encodeURIComponent(runId)}`);
  eventSource.onmessage = (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch {
      return;
    }
    if (typeof payload.seq === "number") {
      if (payload.seq <= state.lastSeq) return;
      state.lastSeq = payload.seq;
    }
    handleEvent(payload);
  };
  eventSource.onerror = () => {
    if (state.run?.status === "running") state.liveStage = "连接中断，正在自动重连…";
  };
}

function closeEvents() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

function startTimer() {
  stopTimer();
  const tick = () => {
    if (!state.run || state.run.status !== "running") return;
    state.elapsed = Math.max(0, (Date.now() - state.run.startedAt) / 1000);
  };
  tick();
  runTimer = window.setInterval(tick, 1000);
}

function stopTimer() {
  if (runTimer) {
    window.clearInterval(runTimer);
    runTimer = null;
  }
}

async function handleEvent(event) {
  const data = event.data || {};
  feedTs = Number(event.ts) || Math.floor(Date.now() / 1000);
  state.events.push(event);
  if (state.events.length > 800) state.events.splice(0, 200);

  switch (event.type) {
    case "started":
      if (data.model) state.run.model = data.model;
      state.liveStage = "Agent 已启动，正在读取仓库…";
      advanceStage(0);
      break;

    case "phase": {
      const label = data.label || "";
      if (label) state.liveStage = label;
      addFeed("info", label, "◆");
      const map = {
        prepare: 0,
        init: 0,
        fallback: 1,
        agent: 2,
        reasoning: 2,
        waiting_human: 2,
        finishing: 2,
        report: 3,
        done: 4,
      };
      if (data.stage in map) advanceStage(map[data.stage]);
      const statusMap = {
        prepare: "准备中",
        init: "初始化模型",
        fallback: "规则扫描",
        agent: "分析中",
        reasoning: "分析中",
        waiting_human: "等待确认",
        finishing: "整理结论",
        report: "生成报告",
      };
      if (state.run?.status === "running" && statusMap[data.stage]) {
        state.runStatusText = statusMap[data.stage];
      }
      break;
    }

    case "progress": {
      const message = data.message || "";
      if (!message) break;
      state.liveStage = message;
      addFeed("info", message, "·");
      if (/扫描|遍历|克隆|依赖|import|模块/i.test(message)) advanceStage(1);
      break;
    }

    case "tool": {
      const label = data.label || toolLabel(data.name);
      if (data.status === "start") {
        addFeed("tool", `调用「${label}」${argsPreview(data.args)}`, "→");
        if (["clone_github_repository", "inspect_local_repository"].includes(data.name)) advanceStage(1);
        else advanceStage(2);
      } else if (data.status === "end") {
        addFeed("ok", `「${label}」完成${data.duration ? ` · ${data.duration}s` : ""}`, "✓");
      } else if (data.status === "error") {
        addFeed("error", data.message || `「${label}」失败`, "✗");
      }
      break;
    }

    case "plan": {
      const names = (data.tools || []).map((tool) => toolLabel(tool.name));
      if (names.length) addFeed("plan", `计划调用：${names.join("、")}`, "↳");
      break;
    }

    case "todos":
      state.todos = Array.isArray(data.todos) ? data.todos : [];
      break;

    case "tokens":
      state.tokens = { input: Number(data.input || 0), output: Number(data.output || 0) };
      break;

    case "meta": {
      if (data.repo_name) state.run.repoName = data.repo_name;
      const stats = data.stats || {};
      state.run.stats = stats;
      state.run.techCount = data.tech_count || 0;
      addFeed(
        "ok",
        `扫描完成：${fmtNumber(stats.file_count)} 个文件 · ${fmtNumber(stats.code_file_count)} 个代码文件 · ${fmtNumber(
          stats.total_loc
        )} 行代码 · ${fmtNumber(data.tech_count)} 项技术`,
        "✓"
      );
      advanceStage(2);
      break;
    }

    case "warning":
      addFeed("warn", data.message || "发生了一个警告", "!");
      toast(data.message || "发生了一个警告", "warn", 6000);
      break;

    case "model":
    case "assistant": {
      const text = data.message || data.content || "";
      if (text.trim()) addFeed("info", text.trim().slice(0, 280), "✳");
      break;
    }

    case "interrupt":
      showHitl(data);
      break;

    case "interrupt_resolved":
      hideHitl();
      if (data.decision === "approve") toast("已批准，Agent 继续执行", "ok");
      else if (data.decision === "reject") toast("已拒绝克隆，Agent 将结束本次分析", "warn");
      else toast("等待超时，已自动拒绝", "warn");
      break;

    case "error": {
      state.run.status = "error";
      state.run.error = data.message || "分析失败";
      stopTimer();
      closeEvents();
      state.runStatusText = "分析失败";
      state.liveStage = "分析失败";
      addFeed("error", data.message || "分析失败", "✗");
      toast(data.message || "分析失败", "error", 8000);
      break;
    }

    case "done": {
      state.run.status = "done";
      stopTimer();
      closeEvents();
      state.stage = 4;
      state.runStatusText = `完成${data.duration ? ` · ${data.duration}s` : ""}`;
      state.liveStage = "报告已生成";
      addFeed("ok", `分析完成，共 ${fmtNumber(data.tech_count)} 项技术`, "✓");
      if (state.view === "run") {
        await loadReport(state.run.runId);
      } else {
        toast("分析完成，可在「历史记录」中查看报告", "ok", 6000);
      }
      break;
    }

    default:
      break;
  }
}

function addFeed(kind, text, icon) {
  if (!text) return;
  state.feed.push({
    id: ++feedSeq,
    kind,
    icon,
    text: String(text),
    // 回放历史事件时使用事件本身的 ts，避免所有行显示成“现在”。
    time: fmtTime(feedTs || Math.floor(Date.now() / 1000)),
  });
  if (state.feed.length > 160) state.feed.splice(0, state.feed.length - 160);
}

function advanceStage(index) {
  state.stage = Math.max(state.stage || 0, index);
}

export function retryAnalysis() {
  if (state.run?.source) startAnalysis(state.run.source);
}

// ---------------------------------------------------------------------------
// 报告
// ---------------------------------------------------------------------------
export async function loadReport(runId) {
  if (state.report?.run_id !== runId) state.report = null;
  state.reportLoading = true;
  state.view = "report";
  window.scrollTo({ top: 0, behavior: "smooth" });
  try {
    const report = await fetchJSON(`/api/report?run_id=${encodeURIComponent(runId)}`);
    showReport(report);
  } catch (error) {
    state.reportLoading = false;
    toast(`读取报告失败：${error.message}`, "error", 6000);
    if (!state.report) state.view = "home";
  }
}

function showReport(report) {
  const sameRun = state.run?.runId === report.run_id;
  state.report = report;
  state.reportLoading = false;
  if (!sameRun) {
    state.run = {
      runId: report.run_id,
      source: report.source,
      sourceType: report.source_type,
      repoName: report.repo_name,
      model: report.ai?.model || "",
      startedAt: Date.now(),
      status: "done",
      error: "",
    };
    // 历史报告没有本次会话的事件流，避免「分析过程」串到上一份报告。
    state.events = [];
    state.feed = [];
    state.todos = [];
    state.lastSeq = -1;
  } else {
    state.run.status = "done";
    state.run.stage = 4;
  }
  closeEvents();
  stopTimer();
  state.stage = 4;
  state.category = "全部";
  state.search = "";
  state.chat = { messages: [], streaming: false, status: "" };
  state.view = "report";
  const validTabs = ["stack", "modules", "architecture", "chat", "process"];
  state.tab = validTabs.includes(state.pendingTab) ? state.pendingTab : "stack";
  state.pendingTab = "";
  updateURL(urlWithTab(state.tab));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

export async function resumeRun(runId) {
  try {
    const data = await fetchJSON(`/api/run?run_id=${encodeURIComponent(runId)}`);
    if (data.status === "done" || data.report_ready) {
      await loadReport(runId);
      return;
    }
    if (data.status === "error") {
      toast(data.error || "这次分析已经失败，请重新分析", "error", 6000);
      state.view = "home";
      return;
    }
    setupRun(
      {
        run_id: runId,
        source_type: data.source_type,
        model: state.health?.model || "",
        repo_name: data.repo_name,
      },
      data.source,
      data.elapsed_seconds,
      true
    );
  } catch (error) {
    toast(`无法恢复这次分析：${error.message}`, "error", 6000);
    state.view = "home";
  }
}

export function switchTab(tab) {
  if (!["stack", "modules", "architecture", "chat", "process"].includes(tab)) return;
  state.tab = tab;
  if (state.report) updateURL(urlWithTab(tab));
}

export function setCategory(category) {
  state.category = category;
}

export function setSearch(value) {
  state.search = String(value || "");
}

export function setFeedFilter(kind) {
  state.feedFilter = kind;
}

export function openTech(key) {
  if (key) state.drawers.techKey = key;
}

export function closeTech() {
  state.drawers.techKey = null;
}

export function openHistory() {
  state.drawers.history = true;
  loadHistory();
}

export function closeHistory() {
  state.drawers.history = false;
}

export function openStyles() {
  state.drawers.styles = true;
}

export function closeStyles() {
  state.drawers.styles = false;
}

export async function loadHistory() {
  state.historyLoading = true;
  try {
    const data = await fetchJSON("/api/history");
    state.history = data.items || [];
  } catch (error) {
    toast(`历史记录加载失败：${error.message}`, "error", 5000);
  } finally {
    state.historyLoading = false;
  }
}

export async function loadHistoryReport(runId) {
  if (state.run?.status === "running") {
    const ok = window.confirm("当前分析仍在进行。切换到历史报告会离开进度页面（后台任务不会中断），确定吗？");
    if (!ok) return;
    closeEvents();
    stopTimer();
    state.run.status = "background";
  }
  closeHistory();
  await loadReport(runId);
}

export function openConcepts() {
  state.drawers.concepts = true;
  loadConcepts();
}

export function closeConcepts() {
  state.drawers.concepts = false;
}

export async function loadConcepts() {
  if (state.concepts.length) return;
  state.conceptsLoading = true;
  try {
    const data = await fetchJSON("/api/concepts");
    state.concepts = data.concepts || [];
  } catch (error) {
    toast(`知识点加载失败：${error.message}`, "error", 5000);
  } finally {
    state.conceptsLoading = false;
  }
}

export function closeOverlays() {
  if (state.drawers.history) state.drawers.history = false;
  if (state.drawers.concepts) state.drawers.concepts = false;
  if (state.drawers.styles) state.drawers.styles = false;
  if (state.drawers.techKey) state.drawers.techKey = null;
}

// ---------------------------------------------------------------------------
// 追问
// ---------------------------------------------------------------------------
export async function sendChat(raw) {
  const message = String(raw || "").trim();
  if (!message || !state.report || state.chat.streaming) return;
  const assistant = { role: "assistant", content: "" };
  state.chat.messages.push({ role: "user", content: message });
  state.chat.messages.push(assistant);
  state.chat.streaming = true;
  state.chat.status = "思考中…";
  let failed = false;

  try {
    await streamChatRequest({ runId: state.report.run_id, message }, (event) => {
      if (event.type === "token") {
        assistant.content += event.data?.text || "";
      } else if (event.type === "tool") {
        state.chat.status = `正在调用：${toolLabel(event.data?.name)}`;
      } else if (event.type === "done") {
        state.chat.status = "";
      } else if (event.type === "error") {
        failed = true;
        const text = event.data?.message || "未知错误";
        state.chat.messages.push({ role: "system", content: `追问失败：${text}` });
        toast(text, "error", 6000);
      } else if (event.type === "meta") {
        state.chat.status = "正在生成…";
      }
    });
  } catch (error) {
    failed = true;
    state.chat.messages.push({ role: "system", content: `追问失败：${error.message}` });
    toast(error.message, "error", 6000);
  } finally {
    state.chat.streaming = false;
    state.chat.status = "";
    if (!failed && !assistant.content.trim()) {
      assistant.content = "（模型没有返回内容，请换个问法再试一次。）";
    }
  }
}

// ---------------------------------------------------------------------------
// 人机协同
// ---------------------------------------------------------------------------
function showHitl(payload) {
  state.hitl = { ...payload, first: (payload.action_requests || [])[0] || null };
  state.hitlRemaining = Number(payload.timeout || 300);
  state.hitlPending = "";
  window.clearInterval(hitlTimer);
  hitlTimer = window.setInterval(() => {
    state.hitlRemaining = Math.max(0, state.hitlRemaining - 1);
    if (state.hitlRemaining <= 0) window.clearInterval(hitlTimer);
  }, 1000);
}

function hideHitl() {
  state.hitl = null;
  state.hitlPending = "";
  state.hitlRemaining = 0;
  window.clearInterval(hitlTimer);
  hitlTimer = null;
}

export async function submitHitl(decision) {
  if (!state.hitl || !state.run || state.hitlPending) return;
  state.hitlPending = decision;
  try {
    await fetchJSON("/api/hitl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: state.run.runId,
        decision,
        message: decision === "reject" ? "用户在网页上拒绝" : "",
      }),
    });
    hideHitl();
  } catch (error) {
    state.hitlPending = "";
    toast(error.message, "error", 6000);
  }
}

// ---------------------------------------------------------------------------
// 导出 / 复制
// ---------------------------------------------------------------------------
export function exportJSON() {
  if (!state.report) return;
  download(
    `${safeFileName(state.report.repo_name)}-repolens.json`,
    JSON.stringify(state.report, null, 2),
    "application/json;charset=utf-8"
  );
  toast("JSON 已导出", "ok");
}

export function exportMarkdown() {
  if (!state.report) return;
  download(
    `${safeFileName(state.report.repo_name)}-repolens.md`,
    reportToMarkdown(state.report),
    "text/markdown;charset=utf-8"
  );
  toast("Markdown 已导出", "ok");
}

export async function copy(value, label = "内容") {
  const ok = await copyText(value);
  toast(ok ? `${label}已复制` : "复制失败，请手动选择", ok ? "ok" : "warn");
}

export function setScrollProgress(value) {
  state.scrollProgress = Math.min(100, Math.max(0, value));
}

export function clearSearch() {
  state.search = "";
}

export { categoryColor, chatText, fmtDuration, fmtNumber, fmtTime, fmtDate } from "./utils";
