/* ==========================================================================
   RepoLens 前端逻辑（原生 JavaScript，无框架、无 CDN）
   --------------------------------------------------------------------------
   代码分成几块，方便对照阅读：
     1. 常量与工具函数
     2. 首页 / 示例 / 模型状态
     3. 分析运行：POST /api/analyze + SSE /api/events
     4. 报告渲染：技术栈、模块地图、架构、追问、过程回放
     5. 抽屉、审批弹窗、历史记录、知识点
   ========================================================================== */

"use strict";

// ---------------------------------------------------------------- 常量
const CATEGORY_COLORS = {
  "编程语言": "#94a3b8",
  "前端框架": "#f0abfc",
  "后端框架": "#67e8f9",
  "AI & Agent": "#a78bfa",
  "数据库": "#fbbf24",
  "缓存与消息": "#fb923c",
  "基础设施与运维": "#38bdf8",
  "测试与质量": "#34d399",
  "构建与工具链": "#cbd5e1",
  "数据科学": "#f472b6",
  "监控与观测": "#22d3ee",
  "其他依赖": "#64748b",
};

const TOOL_LABELS = {
  clone_github_repository: "克隆 GitHub 仓库",
  inspect_local_repository: "扫描本地仓库",
  list_technologies: "列出技术候选",
  inspect_technology: "核实技术与模块",
  read_project_file: "读取项目文件",
  remember_analysis: "写入长期记忆",
  write_todos: "更新任务清单",
  report_overview: "读取报告摘要",
  search_report: "检索报告",
  explain_technology: "查看技术详情",
};

const STAGES = [
  { key: "prepare", label: "检查环境", hint: "模型、路径、运行条件" },
  { key: "scan", label: "扫描仓库", hint: "文件、依赖、import" },
  { key: "agent", label: "Agent 核实", hint: "逐项确认技术与模块" },
  { key: "report", label: "生成报告", hint: "合并事实与 AI 解读" },
];

const state = {
  health: null,
  examples: [],
  current: null, // 当前运行
  report: null,
  lastSeq: -1,
  es: null,
  timer: null,
  view: "home",
  tab: "stack",
  filter: "全部",
  search: "",
  chat: { messages: [], streaming: false },
  concepts: null,
  hitlTimer: null,
  hitlDeadline: 0,
  pendingTab: "",
};

// ---------------------------------------------------------------- 工具
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function fmtNumber(value) {
  const number = Number(value || 0);
  return number.toLocaleString("zh-CN");
}

function fmtDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const mm = String(Math.floor(total / 60)).padStart(2, "0");
  const ss = String(total % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function fmtTime(tsSeconds) {
  try {
    return new Date(Number(tsSeconds) * 1000).toLocaleTimeString("zh-CN", { hour12: false });
  } catch {
    return "--:--:--";
  }
}

function fmtDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("zh-CN", { hour12: false });
  } catch {
    return iso;
  }
}

function basename(source) {
  const text = String(source || "").replace(/[\\/]+$/, "");
  return text.split(/[\\/]/).pop() || text;
}

function categoryColor(category) {
  return CATEGORY_COLORS[category] || "#64748b";
}

function confidenceClass(confidence) {
  return confidence === "高" ? "high" : confidence === "中" ? "mid" : "low";
}

function toolLabel(name) {
  return TOOL_LABELS[name] || name;
}

function truncate(text, limit = 120) {
  const value = String(text || "");
  return value.length > limit ? `${value.slice(0, limit)}…` : value;
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  let body;
  if (contentType.includes("application/json")) {
    body = await response.json();
  } else {
    body = await response.text();
  }
  if (!response.ok) {
    const message = body && body.error ? body.error : `请求失败（HTTP ${response.status}）`;
    throw new Error(message);
  }
  return body;
}

function toast(message, kind = "info", timeout = 4200) {
  const box = $("#toasts");
  const item = document.createElement("div");
  item.className = `toast ${kind}`;
  item.textContent = message;
  box.appendChild(item);
  window.setTimeout(() => {
    item.style.opacity = "0";
    item.style.transform = "translateY(8px)";
    item.style.transition = "0.25s";
    window.setTimeout(() => item.remove(), 260);
  }, timeout);
}

function showView(name) {
  state.view = name;
  ["home", "run", "report"].forEach((key) => {
    const view = $(`#view-${key}`);
    if (view) view.classList.toggle("hidden", key !== name);
  });
  if (name === "home") {
    try {
      window.history.replaceState({}, "", window.location.pathname);
    } catch {
      /* 忽略 */
    }
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------------------------------------------------------------- 初始化
async function init() {
  renderTimeline();
  bindEvents();
  try {
    const [health, examples] = await Promise.all([
      fetchJSON("/api/health"),
      fetchJSON("/api/examples"),
    ]);
    state.health = health;
    state.examples = examples.items || [];
    renderModelBadge();
    renderExamples();
    // 支持直接分享报告：/?report=<run_id>
    // 也支持刷新后恢复正在运行的分析：/?run=<run_id>
    const params = new URLSearchParams(window.location.search);
    state.pendingTab = params.get("tab") || "";
    const reportId = params.get("report");
    const runId = params.get("run");
    if (reportId) {
      loadReport(reportId);
    } else if (runId) {
      resumeRun(runId);
    }
  } catch (error) {
    $("#model-badge-text").textContent = "服务连接失败";
    $("#model-badge").classList.add("warn");
    toast(`无法连接后端：${error.message}`, "error", 7000);
  }
}

function renderModelBadge() {
  const health = state.health;
  const badge = $("#model-badge");
  if (!health) return;
  const text = $("#model-badge-text");
  if (health.ai_available) {
    text.textContent = health.model;
    badge.classList.add("ok");
    badge.title = "AI 解读已启用。Agent 会调用工具并生成结构化报告。";
  } else {
    text.textContent = "未配置模型 · 仅规则扫描";
    badge.classList.add("warn");
    badge.title = "在 .env 中填写 GLM_API_KEY / DEEPSEEK_API_KEY 后可启用 AI 解读。";
  }
}

function renderExamples() {
  const box = $("#example-chips");
  box.innerHTML = "";
  for (const example of state.examples) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    button.title = example.description || "";
    button.innerHTML = `${example.kind === "github" ? "⌥" : "▸"} <b>${esc(example.label)}</b>`;
    button.addEventListener("click", () => {
      $("#source-input").value = example.value;
      $("#source-input").focus();
    });
    box.appendChild(button);
  }
}

function bindEvents() {
  $("#btn-analyze").addEventListener("click", () => startAnalysis($("#source-input").value));
  $("#source-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      startAnalysis($("#source-input").value);
    }
  });

  $("#brand-home").addEventListener("click", (event) => {
    event.preventDefault();
    if (state.current && state.current.status === "running") {
      showView("run");
      return;
    }
    showView("home");
  });
  $("#btn-run-back").addEventListener("click", leaveRun);
  $("#btn-report-back").addEventListener("click", () => showView("home"));
  $("#btn-reanalyze").addEventListener("click", () => {
    if (state.report) startAnalysis(state.report.source);
  });

  $("#btn-history").addEventListener("click", openHistory);
  $("#btn-concepts").addEventListener("click", openConcepts);
  $("#btn-concepts-2").addEventListener("click", openConcepts);

  $$("#report-tabs .tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
  $("#tech-search").addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLowerCase();
    renderTechGroups();
  });
  $("#category-chips").addEventListener("click", (event) => {
    const chip = event.target.closest("[data-category]");
    if (!chip) return;
    state.filter = chip.dataset.category;
    renderTechGroups();
    renderCategoryChips();
  });
  $("#tech-groups").addEventListener("click", (event) => {
    const card = event.target.closest(".tech-card");
    if (card) openTech(card.dataset.key);
  });

  $("#chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    sendChat($("#chat-input").value);
  });

  $("#btn-export-json").addEventListener("click", exportJSON);
  $("#btn-export-md").addEventListener("click", exportMarkdown);

  $$("[data-close]").forEach((button) => {
    button.addEventListener("click", () => closeOverlay(button.dataset.close));
  });
  ["history-overlay", "concepts-overlay", "tech-overlay"].forEach((id) => {
    const overlay = $(`#${id}`);
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) closeOverlay(id);
    });
  });
  $("#history-list").addEventListener("click", (event) => {
    const item = event.target.closest("[data-run-id]");
    if (!item) return;
    if (state.current && state.current.status === "running") {
      const ok = window.confirm("当前分析仍在进行。切换到历史报告会离开进度页面（后台任务不会中断），确定吗？");
      if (!ok) return;
      closeEvents();
      stopTimer();
    }
    closeOverlay("history-overlay");
    loadReport(item.dataset.runId);
  });

  $("#btn-hitl-approve").addEventListener("click", () => submitHitl("approve"));
  $("#btn-hitl-reject").addEventListener("click", () => submitHitl("reject"));

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const hitl = $("#hitl-modal");
    if (!hitl.classList.contains("hidden")) return; // 审批必须明确选择
    ["history-overlay", "concepts-overlay", "tech-overlay"].forEach((id) => {
      if (!$(`#${id}`).classList.contains("hidden")) closeOverlay(id);
    });
  });
}

// ---------------------------------------------------------------- 分析运行
async function startAnalysis(rawSource) {
  const source = String(rawSource || "").trim();
  if (!source) {
    toast("请先输入本地仓库路径或 GitHub 地址", "warn");
    $("#source-input").focus();
    return;
  }
  if (state.current && state.current.status === "running") {
    toast("已有一个分析正在进行，请稍等", "warn");
    showView("run");
    return;
  }

  const button = $("#btn-analyze");
  button.disabled = true;
  const original = button.innerHTML;
  button.innerHTML = "启动 Agent…";

  try {
    const data = await fetchJSON("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    setupRun(data, source, 0, false);
  } catch (error) {
    toast(error.message, "error", 7000);
    button.disabled = false;
    button.innerHTML = original;
    return;
  }
  button.disabled = false;
  button.innerHTML = original;
}

function setupRun(data, source, elapsedSeconds = 0, resumed = false) {
  closeEvents();
  stopTimer();
  state.lastSeq = -1;
  state.report = null;
  state.chat = { messages: [], streaming: false };
  state.current = {
    runId: data.run_id,
    source,
    sourceType: data.source_type,
    model: data.model || (state.health && state.health.model) || "",
    events: [],
    todos: [],
    status: "running",
    stage: 0,
    startedAt: Date.now() - Math.max(0, Number(elapsedSeconds) || 0) * 1000,
    repoName: data.repo_name || basename(source),
  };

  $("#run-repo").textContent = state.current.repoName;
  $("#run-source").textContent = source;
  $("#run-status-text").textContent = "准备中";
  $("#run-status").classList.remove("done", "error");
  $("#live-stage").textContent = "正在启动 Agent…";
  $("#live-feed").innerHTML = "";
  $("#todos").innerHTML = '<li class="muted">等待模型制定计划…</li>';
  $("#tok-in").textContent = "0";
  $("#tok-out").textContent = "0";
  $("#run-timer").textContent = "00:00";

  renderTimeline();
  appendFeed("info", resumed ? "↻" : "◆", resumed ? "正在恢复刷新前的分析进度…" : `开始分析：${source}`);
  showView("run");
  try {
    window.history.replaceState({}, "", `?run=${encodeURIComponent(data.run_id)}`);
  } catch {
    /* 忽略 */
  }
  startTimer();
  connectEvents(data.run_id);
}

async function resumeRun(runId) {
  try {
    const data = await fetchJSON(`/api/run?run_id=${encodeURIComponent(runId)}`);
    if (data.status === "done" || data.report_ready) {
      loadReport(runId);
      return;
    }
    if (data.status === "error") {
      toast(data.error || "这次分析已经失败，请重新分析", "error", 6000);
      showView("home");
      return;
    }
    setupRun(
      {
        run_id: runId,
        source_type: data.source_type,
        model: state.health ? state.health.model : "",
        repo_name: data.repo_name,
      },
      data.source,
      data.elapsed_seconds,
      true
    );
  } catch (error) {
    toast(`无法恢复这次分析：${error.message}`, "error", 6000);
    showView("home");
  }
}

function connectEvents(runId) {
  state.es = new EventSource(`/api/events?run_id=${encodeURIComponent(runId)}`);
  state.es.onmessage = (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch {
      return;
    }
    if (typeof payload.seq === "number") {
      if (payload.seq <= state.lastSeq) return; // 重连时去重
      state.lastSeq = payload.seq;
    }
    handleEvent(payload);
  };
  state.es.onerror = () => {
    if (state.current && state.current.status === "running") {
      setLiveStage("连接中断，正在自动重连…");
    }
  };
}

function closeEvents() {
  if (state.es) {
    state.es.close();
    state.es = null;
  }
}

function handleEvent(event) {
  if (!state.current) return;
  state.current.events.push(event);
  if (state.current.events.length > 800) state.current.events.splice(0, 200);

  const data = event.data || {};
  switch (event.type) {
    case "started":
      if (data.model) {
        state.current.model = data.model;
      }
      setLiveStage("Agent 已启动，正在读取仓库…");
      advanceStage(0);
      break;

    case "phase": {
      const label = data.label || "";
      if (label) setLiveStage(label);
      appendFeed("info", "◆", label);
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
      const statusText = {
        prepare: "准备中",
        init: "初始化模型",
        fallback: "规则扫描",
        agent: "分析中",
        reasoning: "分析中",
        waiting_human: "等待确认",
        finishing: "整理结论",
        report: "生成报告",
      };
      if (state.current && state.current.status === "running" && statusText[data.stage]) {
        $("#run-status-text").textContent = statusText[data.stage];
      }
      break;
    }

    case "progress": {
      const message = data.message || "";
      if (!message) break;
      setLiveStage(message);
      appendFeed("info", "·", message);
      if (/扫描|遍历|克隆|依赖|import|模块/i.test(message)) advanceStage(1);
      break;
    }

    case "tool": {
      const label = data.label || toolLabel(data.name);
      if (data.status === "start") {
        appendFeed("tool", "→", `调用「${label}」${argsPreview(data.args)}`);
        if (["clone_github_repository", "inspect_local_repository"].includes(data.name)) advanceStage(1);
        else advanceStage(2);
      } else if (data.status === "end") {
        const duration = data.duration ? ` · ${data.duration}s` : "";
        appendFeed("ok", "✓", `「${label}」完成${duration}`);
      } else if (data.status === "error") {
        appendFeed("error", "✗", data.message || `「${label}」失败`);
      }
      break;
    }

    case "plan": {
      const names = (data.tools || []).map((tool) => toolLabel(tool.name));
      if (names.length) appendFeed("plan", "↳", `计划调用：${names.join("、")}`);
      break;
    }

    case "todos": {
      state.current.todos = Array.isArray(data.todos) ? data.todos : [];
      renderTodos();
      break;
    }

    case "tokens":
      $("#tok-in").textContent = fmtNumber(data.input);
      $("#tok-out").textContent = fmtNumber(data.output);
      break;

    case "meta": {
      if (data.repo_name) {
        state.current.repoName = data.repo_name;
        $("#run-repo").textContent = data.repo_name;
      }
      const stats = data.stats || {};
      appendFeed(
        "ok",
        "✓",
        `扫描完成：${fmtNumber(stats.file_count)} 个文件 · ${fmtNumber(stats.code_file_count)} 个代码文件 · ${fmtNumber(stats.total_loc)} 行代码 · ${fmtNumber(data.tech_count)} 项技术`
      );
      advanceStage(2);
      break;
    }

    case "warning":
      appendFeed("warn", "!", data.message || "发生了一个警告");
      toast(data.message || "发生了一个警告", "warn", 6000);
      break;

    case "model":
    case "assistant": {
      const text = data.message || data.content || "";
      if (text.trim()) appendFeed("info", "✳", truncate(text.trim(), 280));
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
      state.current.status = "error";
      stopTimer();
      closeEvents();
      $("#run-status").classList.remove("done");
      $("#run-status").classList.add("error");
      $("#run-status-text").textContent = "分析失败";
      setLiveStage("分析失败");
      appendFeed("error", "✗", data.message || "分析失败");
      appendRetry();
      toast(data.message || "分析失败", "error", 8000);
      break;
    }

    case "done": {
      state.current.status = "done";
      stopTimer();
      closeEvents();
      advanceStage(4);
      $("#run-status").classList.remove("error");
      $("#run-status").classList.add("done");
      $("#run-status-text").textContent = `完成${data.duration ? ` · ${data.duration}s` : ""}`;
      setLiveStage("报告已生成");
      appendFeed("ok", "✓", `分析完成，共 ${fmtNumber(data.tech_count)} 项技术`);
      if (state.view === "run") {
        loadReport(state.current.runId);
      } else {
        toast("分析完成，可在「历史记录」中查看报告", "ok", 6000);
      }
      break;
    }

    default:
      break;
  }
}

function argsPreview(args) {
  if (!args || typeof args !== "object") return "";
  const parts = [];
  for (const key of ["path", "url", "relative_path"]) {
    if (args[key]) parts.push(truncate(String(args[key]), 90));
  }
  if (Array.isArray(args.names)) {
    parts.push(`核实 ${args.names.slice(0, 4).join("、")}${args.names.length > 4 ? "…" : ""}`);
  }
  return parts.length ? `（${parts.join("；")}）` : "";
}

function appendFeed(kind, icon, text) {
  const feed = $("#live-feed");
  const line = document.createElement("div");
  line.className = `feed-line ${kind}`;

  const time = document.createElement("span");
  time.className = "feed-time";
  time.textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });

  const mark = document.createElement("span");
  mark.className = "feed-icon";
  mark.textContent = icon;

  const content = document.createElement("span");
  content.className = "feed-text";
  content.textContent = text;

  line.append(time, mark, content);
  feed.appendChild(line);
  while (feed.children.length > 160) feed.removeChild(feed.firstChild);
  feed.scrollTop = feed.scrollHeight;
}

function appendRetry() {
  const feed = $("#live-feed");
  const line = document.createElement("div");
  line.className = "feed-line error";
  const mark = document.createElement("span");
  mark.className = "feed-icon";
  mark.textContent = "↻";
  const content = document.createElement("span");
  content.className = "feed-text";
  content.appendChild(document.createTextNode("可以返回首页修改路径后重试，或 "));
  const button = document.createElement("button");
  button.className = "link-btn";
  button.type = "button";
  button.textContent = "用相同来源重试";
  button.addEventListener("click", () => {
    if (state.current) startAnalysis(state.current.source);
  });
  content.appendChild(button);
  line.append(mark, content);
  feed.appendChild(line);
  feed.scrollTop = feed.scrollHeight;
}

function setLiveStage(text) {
  $("#live-stage").textContent = text;
}

function renderTimeline() {
  const timeline = $("#timeline");
  const current = state.current ? state.current.stage : 0;
  timeline.innerHTML = STAGES.map((stage, index) => {
    let status = "";
    if (current >= STAGES.length || index < current) status = "done";
    else if (index === current) status = "active";
    return `<li class="${status}" data-stage="${stage.key}">
      <span class="tl-label">${esc(stage.label)}</span>
      <span class="tl-hint">${esc(stage.hint)}</span>
    </li>`;
  }).join("");
}

function advanceStage(index) {
  if (!state.current) return;
  const next = Math.max(state.current.stage || 0, index);
  if (next === state.current.stage) return;
  state.current.stage = next;
  renderTimeline();
}

function renderTodos() {
  const box = $("#todos");
  if (!state.current || !state.current.todos.length) {
    box.innerHTML = '<li class="muted">等待模型制定计划…</li>';
    return;
  }
  box.innerHTML = "";
  for (const todo of state.current.todos) {
    const item = document.createElement("li");
    const status = todo.status || "pending";
    item.className = status;
    const mark = document.createElement("span");
    mark.className = "todo-mark";
    mark.textContent = status === "completed" ? "✓" : status === "in_progress" ? "…" : "";
    const text = document.createElement("span");
    text.textContent = todo.content || "";
    item.append(mark, text);
    box.appendChild(item);
  }
}

function startTimer() {
  stopTimer();
  const update = () => {
    if (!state.current || state.current.status !== "running") return;
    $("#run-timer").textContent = fmtDuration((Date.now() - state.current.startedAt) / 1000);
  };
  update();
  state.timer = window.setInterval(update, 1000);
}

function stopTimer() {
  if (state.timer) {
    window.clearInterval(state.timer);
    state.timer = null;
  }
}

function leaveRun() {
  if (state.current && state.current.status === "running") {
    const ok = window.confirm("分析仍在进行。离开页面不会中断后台任务，完成后可以在「历史记录」里查看。确定离开吗？");
    if (!ok) return;
    closeEvents();
    stopTimer();
    toast("分析仍在后台进行，完成后可在历史记录查看", "warn", 6000);
  }
  showView("home");
}

async function loadReport(runId) {
  try {
    const report = await fetchJSON(`/api/report?run_id=${encodeURIComponent(runId)}`);
    showReport(report);
  } catch (error) {
    toast(`读取报告失败：${error.message}`, "error", 6000);
  }
}

// ---------------------------------------------------------------- 报告
function showReport(report) {
  state.report = report;
  const sameRun = state.current && state.current.runId === report.run_id;
  if (!sameRun) {
    state.current = {
      runId: report.run_id,
      source: report.source,
      sourceType: report.source_type,
      events: [],
      todos: [],
      status: "done",
      stage: 4,
      startedAt: Date.now(),
    };
  } else {
    state.current.status = "done";
    state.current.stage = 4;
  }
  closeEvents();
  stopTimer();
  try {
    const url = new URL(window.location.href);
    url.search = `?report=${encodeURIComponent(report.run_id)}`;
    window.history.replaceState({}, "", url);
  } catch {
    /* 忽略：某些浏览器在 file:// 下不允许修改地址 */
  }

  $("#report-repo").textContent = report.repo_name || "分析报告";
  const source = $("#report-source");
  source.innerHTML = "";
  if (report.source_type === "github") {
    const link = document.createElement("a");
    link.href = report.source.startsWith("http") ? report.source : `https://github.com/${report.source}`;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    link.textContent = `${report.source} ↗`;
    source.appendChild(link);
  } else {
    source.textContent = report.source;
  }

  const ai = report.ai || {};
  const badge = $("#report-ai-badge");
  badge.className = "tag";
  if (ai.used) {
    badge.classList.add("good");
    badge.textContent = `AI 解读 · ${ai.model || "模型"}`;
  } else if (ai.error) {
    badge.classList.add("warn");
    badge.textContent = "AI 解读失败 · 规则报告";
  } else {
    badge.classList.add("warn");
    badge.textContent = "仅规则扫描（未启用 AI 解读）";
  }
  $("#summary-note").textContent = ai.used
    ? "由大模型基于扫描事实生成"
    : ai.error
    ? "AI 不可用，本报告由本地规则生成"
    : "由本地规则生成";

  state.filter = "全部";
  state.search = "";
  $("#tech-search").value = "";
  renderStats(report);
  $("#summary-text").textContent = report.summary || "暂无摘要。";
  renderHighlights(report.highlights || []);
  renderWarnings(report.warnings || []);
  renderCategoryChips();
  renderTechGroups();
  renderModules();
  renderArchitecture(report);
  renderProcess(report);
  resetChat();

  const pending = state.pendingTab;
  state.pendingTab = "";
  const validTabs = ["stack", "modules", "architecture", "chat", "process"];
  switchTab(validTabs.includes(pending) ? pending : "stack");
  showView("report");
}

function renderStats(report) {
  const stats = report.stats || {};
  const cards = [
    { value: fmtNumber(stats.file_count), label: "文件总数" },
    { value: fmtNumber(stats.code_file_count), label: "代码文件" },
    { value: fmtNumber(stats.total_loc), label: "代码行数" },
    { value: fmtNumber((report.techs || []).length), label: "技术项" },
    { value: fmtNumber((report.languages || []).filter((item) => item.is_code).length), label: "编程语言" },
    { value: `${Number(stats.scan_seconds || 0).toFixed(1)}s`, label: "扫描耗时" },
  ];
  $("#stat-row").innerHTML = cards
    .map((card) => `<div class="stat-card"><div class="v">${esc(card.value)}</div><div class="l">${esc(card.label)}</div></div>`)
    .join("");
}

function renderHighlights(highlights) {
  const box = $("#highlights");
  box.innerHTML = "";
  for (const text of highlights) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = text;
    box.appendChild(chip);
  }
}

function renderWarnings(warnings) {
  const box = $("#report-warnings");
  if (!warnings.length) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }
  box.classList.remove("hidden");
  box.innerHTML = warnings.map((text) => `<p>⚠ ${esc(text)}</p>`).join("");
}

function renderCategoryChips() {
  if (!state.report) return;
  const box = $("#category-chips");
  const total = (state.report.techs || []).length;
  const categories = state.report.categories || [];
  const items = [{ name: "全部", count: total, icon: "◈" }, ...categories];
  box.innerHTML = items
    .map((item) => {
      const active = state.filter === item.name ? " active" : "";
      return `<button type="button" class="chip${active}" data-category="${esc(item.name)}">${esc(item.icon || "◈")} ${esc(item.name)} · ${fmtNumber(item.count)}</button>`;
    })
    .join("");
}

function renderTechGroups() {
  const report = state.report;
  if (!report) return;
  const box = $("#tech-groups");
  const keyword = state.search;
  const filter = state.filter;

  const techs = (report.techs || []).filter((tech) => {
    if (filter !== "全部" && tech.category !== filter) return false;
    if (!keyword) return true;
    const haystack = [
      tech.name,
      tech.category,
      tech.role,
      ...(tech.modules || []).map((module) => module.path),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(keyword);
  });

  if (!techs.length) {
    box.innerHTML = '<div class="empty-state">没有匹配的技术。试试清空搜索条件。</div>';
    return;
  }

  const order = (report.categories || []).map((item) => item.name);
  const groups = new Map();
  for (const tech of techs) {
    if (!groups.has(tech.category)) groups.set(tech.category, []);
    groups.get(tech.category).push(tech);
  }

  const sortedCategories = Array.from(groups.keys()).sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });

  box.innerHTML = sortedCategories
    .map((category) => {
      const items = groups.get(category);
      const icon = (report.categories || []).find((item) => item.name === category)?.icon || "◈";
      return `<section class="tech-group">
        <div class="group-head">
          <h3>${esc(icon)} ${esc(category)}</h3>
          <span class="count">${items.length}</span>
          <span class="line"></span>
        </div>
        <div class="tech-grid">
          ${items.map(techCardHTML).join("")}
        </div>
      </section>`;
    })
    .join("");
}

function techCardHTML(tech) {
  const color = categoryColor(tech.category);
  const confidence = confidenceClass(tech.confidence);
  const version = tech.version ? `v${esc(tech.version)}` : "版本未知";
  const aiFlag = tech.ai_inferred ? '<span class="ai-flag">AI 推断</span><span class="sep"></span>' : "";
  const keyModules = (tech.key_modules || tech.modules?.map((module) => module.path) || []).slice(0, 6);
  return `<article class="tech-card" data-key="${esc(tech.key)}" style="--c:${color}" title="${esc(keyModules.join("\n") || tech.name)}">
    <div class="tech-card-top">
      <div>
        <div class="tech-name">${esc(tech.name)}</div>
        <div class="tech-version">${version}</div>
      </div>
      <span class="tag">${esc(tech.category)}</span>
    </div>
    <p class="tech-role">${esc(tech.role || tech.hint || "暂无说明")}</p>
    <div class="tech-foot">
      <span><i class="conf ${confidence}"></i>置信度 ${esc(tech.confidence || "中")}</span>
      <span class="sep"></span>
      <span>${fmtNumber(tech.module_count)} 个模块</span>
      ${aiFlag}
      <span>${fmtNumber((tech.evidence || []).length)} 条证据</span>
    </div>
  </article>`;
}

function renderModules() {
  const report = state.report;
  if (!report) return;
  const box = $("#module-map");
  const withModules = (report.techs || [])
    .filter((tech) => (tech.modules || []).length)
    .sort((a, b) => b.module_count - a.module_count);
  const withoutModules = (report.techs || []).filter((tech) => !(tech.modules || []).length);

  if (!withModules.length) {
    box.innerHTML = '<div class="empty-state">没有找到直接 import 的技术。项目可能只提供了依赖清单，或者代码主要在配置中体现。</div>';
    return;
  }

  box.innerHTML = withModules
    .map((tech, index) => {
      const rows = (tech.modules || [])
        .map(
          (module) => `<tr>
            <td class="path">${esc(module.path)}</td>
            <td class="line">:${esc(module.line)}</td>
            <td class="role">${esc(module.role || "源码")}</td>
            <td class="snippet">${esc(truncate(module.snippet, 150))}</td>
          </tr>`
        )
        .join("");
      return `<details class="module-group" ${index < 3 ? "open" : ""}>
        <summary>
          <span class="name">${esc(tech.name)}</span>
          <span class="tag">${esc(tech.category)}</span>
          <span class="meta">${fmtNumber(tech.module_count)} 个模块 · ${fmtNumber((tech.evidence || []).length)} 条证据</span>
        </summary>
        <table class="module-table">
          <thead><tr><th>文件</th><th>行号</th><th>角色</th><th>代码片段 / 导入语句</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </details>`;
    })
    .join("");

  if (withoutModules.length) {
    box.insertAdjacentHTML(
      "beforeend",
      `<p class="no-module-note">仅出现在依赖清单或配置中（没有找到直接 import）：${withoutModules
        .map((tech) => esc(tech.name))
        .join("、")}</p>`
    );
  }
}

function renderArchitecture(report) {
  const architecture = report.architecture || [];
  const risks = report.risks || [];
  const learning = report.learning_path || [];

  $("#architecture-list").innerHTML = architecture.length
    ? architecture.map((text) => `<li>${esc(text)}</li>`).join("")
    : '<li class="muted">报告没有提供架构说明。</li>';

  $("#risk-list").innerHTML = risks.length
    ? risks.map((text) => `<li>${esc(text)}</li>`).join("")
    : '<li class="empty">没有发现明显的风险信号。仍建议人工检查依赖版本与密钥配置。</li>';

  $("#learning-list").innerHTML = learning.length
    ? learning.map((text) => `<li>${esc(text)}</li>`).join("")
    : '<li class="muted">报告没有提供学习路径。</li>';

  const keyFiles = $("#key-files");
  const entryPoints = report.entry_points || [];
  const manifests = report.manifests || [];
  const topDirs = report.top_dirs || [];
  const languages = (report.languages || []).filter((item) => item.is_code).slice(0, 5);
  const maxDir = Math.max(1, ...topDirs.map((item) => item.files || 0));

  const blocks = [];
  if (entryPoints.length) {
    blocks.push(`<div class="kf-block"><h4>入口 / 关键文件</h4>${entryPoints
      .map((path) => `<div class="kf-item"><span>${esc(path)}</span></div>`)
      .join("")}</div>`);
  }
  if (manifests.length) {
    blocks.push(`<div class="kf-block"><h4>依赖清单</h4>${manifests
      .map(
        (item) =>
          `<div class="kf-item"><span>${esc(item.path)}</span><b>${fmtNumber(item.dependency_count)} 条依赖</b></div>`
      )
      .join("")}</div>`);
  }
  if (topDirs.length) {
    blocks.push(`<div class="kf-block"><h4>目录规模</h4><div class="dir-bars">${topDirs
      .slice(0, 6)
      .map(
        (item) => `<div class="dir-bar">
          <span>${esc(item.name)}/</span>
          <span class="bar" style="width:${Math.max(6, Math.round((item.files / maxDir) * 100))}%"></span>
          <span class="num">${fmtNumber(item.files)}</span>
        </div>`
      )
      .join("")}</div></div>`);
  }
  if (languages.length) {
    const maxLoc = Math.max(1, ...languages.map((item) => item.loc || 0));
    blocks.push(`<div class="kf-block"><h4>语言分布</h4><div class="dir-bars">${languages
      .map(
        (item) => `<div class="dir-bar">
          <span>${esc(item.name)}</span>
          <span class="bar" style="width:${Math.max(6, Math.round((item.loc / maxLoc) * 100))}%"></span>
          <span class="num">${esc(item.percent)}%</span>
        </div>`
      )
      .join("")}</div></div>`);
  }
  keyFiles.innerHTML = blocks.join("") || '<p class="muted">没有可展示的文件信息。</p>';
}

function renderProcess(report) {
  const box = $("#process-log");
  const events = (state.current && state.current.events) || [];
  if (!events.length) {
    box.innerHTML =
      '<li><span class="t">--:--</span><span class="n">提示</span><span class="c">历史报告只保存了最终结果，没有保存事件流。重新分析一次即可在这里回放 Agent 的每一步。</span></li>';
    return;
  }
  const lines = [];
  for (const event of events) {
    const data = event.data || {};
    let name = event.type;
    let content = "";
    switch (event.type) {
      case "phase":
        name = "阶段";
        content = data.label || data.stage || "";
        break;
      case "tool":
        name = "工具";
        content = `${toolLabel(data.name)} · ${data.status === "start" ? "开始" : data.status === "end" ? "完成" : "失败"}${
          data.duration ? ` · ${data.duration}s` : ""
        }`;
        break;
      case "progress":
        name = "进度";
        content = data.message || "";
        break;
      case "plan":
        name = "计划";
        content = (data.tools || []).map((tool) => toolLabel(tool.name)).join("、");
        break;
      case "todos":
        name = "待办";
        content = `更新为 ${(data.todos || []).length} 项`;
        break;
      case "meta":
        name = "扫描";
        content = `完成 ${fmtNumber((data.stats || {}).file_count)} 个文件，识别 ${fmtNumber(data.tech_count)} 项技术`;
        break;
      case "warning":
        name = "警告";
        content = data.message || "";
        break;
      case "error":
        name = "错误";
        content = data.message || "";
        break;
      case "interrupt":
        name = "审批";
        content = "等待用户批准克隆仓库";
        break;
      case "interrupt_resolved":
        name = "审批";
        content = `用户选择：${data.decision}`;
        break;
      case "done":
        name = "完成";
        content = `生成 ${fmtNumber(data.tech_count)} 项技术的报告`;
        break;
      default:
        continue;
    }
    lines.push(
      `<li><span class="t">${esc(fmtTime(event.ts))}</span><span class="n">${esc(name)}</span><span class="c">${esc(
        truncate(content, 240)
      )}</span></li>`
    );
  }
  box.innerHTML = lines.join("") || '<li><span class="t">--:--</span><span class="n">空白</span><span class="c">没有事件。</span></li>';
}

function switchTab(name) {
  state.tab = name;
  $$("#report-tabs .tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
  ["stack", "modules", "architecture", "chat", "process"].forEach((key) => {
    const panel = $(`#tab-${key}`);
    if (panel) panel.classList.toggle("hidden", key !== name);
  });
  try {
    const url = new URL(window.location.href);
    if (url.searchParams.has("report")) {
      if (name === "stack") url.searchParams.delete("tab");
      else url.searchParams.set("tab", name);
      window.history.replaceState({}, "", url);
    }
  } catch {
    /* 忽略 */
  }
  if (name === "chat") {
    window.setTimeout(() => $("#chat-input").focus(), 80);
  }
}

// ---------------------------------------------------------------- 技术详情
function openTech(key) {
  if (!state.report) return;
  const tech = (state.report.techs || []).find((item) => item.key === key);
  if (!tech) return;

  $("#tech-category").textContent = tech.category;
  $("#tech-title").textContent = tech.name;
  const meta = [
    tech.version ? `版本 ${tech.version}` : "版本未知",
    `置信度 ${tech.confidence}`,
    tech.ai_inferred ? "AI 推断（无代码证据）" : "来自扫描结果",
  ];
  $("#tech-meta").textContent = meta.join(" · ");

  const modules = tech.modules || [];
  const evidence = tech.evidence || [];
  const body = [];

  body.push(`<p class="tb-role">${esc(tech.role || tech.hint || "暂无职责说明。")}</p>`);
  body.push(`<div class="info-grid">
    <div class="ig"><b>${fmtNumber(tech.module_count)}</b><span>使用模块</span></div>
    <div class="ig"><b>${fmtNumber(evidence.length)}</b><span>证据条数</span></div>
    <div class="ig"><b>${esc((tech.sources || []).join(" / ") || "扫描")}</b><span>识别来源</span></div>
  </div>`);

  if (tech.ai_inferred) {
    body.push('<p class="warnings" style="display:block;margin-bottom:16px">这项技术是 AI 根据上下文推断的，代码中没有找到直接证据，请人工确认。</p>');
  }

  if (evidence.length) {
    body.push("<h4>证据（来自依赖清单 / import）</h4>");
    body.push(
      `<ul class="evidence-list">${evidence
        .map(
          (item) =>
            `<li><b>${esc(item.path)}${item.line ? `:${esc(item.line)}` : ""}</b> · ${esc(item.kind)}<br>${esc(
              item.text
            )}</li>`
        )
        .join("")}</ul>`
    );
  }

  body.push("<h4>使用它的模块</h4>");
  if (modules.length) {
    body.push(
      `<div class="tech-modules">${modules
        .map(
          (module) => `<div class="tech-module">
            <div class="tm-head"><span>${esc(module.path)}:${esc(module.line)}</span><span class="tm-role">${esc(
            module.role || "源码"
          )}</span></div>
            <div class="tm-snippet">${esc(module.snippet || "（无代码片段）")}</div>
          </div>`
        )
        .join("")}</div>`
    );
  } else {
    body.push('<p class="muted">没有找到直接 import。它可能只出现在依赖清单、Docker 镜像或配置文件中。</p>');
  }

  if (tech.hint) {
    body.push(`<h4>技术说明</h4><p class="muted">${esc(tech.hint)}</p>`);
  }

  $("#tech-body").innerHTML = body.join("");
  $("#tech-overlay").classList.remove("hidden");
}

function closeOverlay(id) {
  const overlay = $(`#${id}`);
  if (overlay) overlay.classList.add("hidden");
}

// ---------------------------------------------------------------- 追问
function resetChat() {
  state.chat = { messages: [], streaming: false };
  renderChat();
  renderChatSuggestions();
  $("#chat-status").textContent = "";
  $("#chat-send").disabled = false;
  $("#chat-input").disabled = false;
}

function renderChat() {
  const box = $("#chat-messages");
  box.innerHTML = "";
  if (!state.chat.messages.length) {
    const empty = document.createElement("div");
    empty.className = "chat-empty";
    empty.innerHTML =
      "报告已经生成，接下来可以继续问它。<br>回答会先查报告和仓库文件，再组织语言，不会凭空编造。";
    box.appendChild(empty);
    return;
  }
  for (const message of state.chat.messages) {
    const row = document.createElement("div");
    row.className = `msg ${message.role}`;
    if (message.role === "system") {
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = message.content;
      row.appendChild(bubble);
    } else {
      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = message.role === "user" ? "你" : "◈";
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = message.role === "assistant" ? chatText(message.content) : message.content;
      row.append(avatar, bubble);
    }
    box.appendChild(row);
  }
  $("#chat-suggestions").classList.toggle("hidden", state.chat.messages.length > 0);
  box.scrollTop = box.scrollHeight;
}

function renderChatSuggestions() {
  const box = $("#chat-suggestions");
  const suggestions = [
    "这个项目最核心的技术是什么？",
    "数据库和缓存分别用在哪里？",
    "我应该先读哪些文件？",
    "有没有测试，覆盖了什么？",
  ];
  box.innerHTML = "";
  for (const text of suggestions) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = text;
    chip.addEventListener("click", () => sendChat(text));
    box.appendChild(chip);
  }
}

async function sendChat(raw) {
  const message = String(raw || "").trim();
  if (!message || !state.report) return;
  if (state.chat.streaming) {
    toast("上一条回答还在生成，请稍等", "warn");
    return;
  }

  state.chat.messages.push({ role: "user", content: message });
  const assistant = { role: "assistant", content: "" };
  state.chat.messages.push(assistant);
  state.chat.streaming = true;
  renderChat();
  $("#chat-input").value = "";
  $("#chat-send").disabled = true;
  $("#chat-input").disabled = true;
  $("#chat-status").textContent = "思考中…";

  const bubble = $("#chat-messages").lastElementChild?.querySelector(".bubble");
  const assistantIndex = state.chat.messages.length - 1;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: state.report.run_id, message }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || `请求失败（HTTP ${response.status}）`);
    }
    if (!response.body) throw new Error("浏览器不支持流式读取");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let index;
      while ((index = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, index);
        buffer = buffer.slice(index + 2);
        const payload = parseSSEBlock(block);
        if (!payload) continue;
        handleChatEvent(payload, assistantIndex, bubble);
      }
    }
  } catch (error) {
    state.chat.messages.push({ role: "system", content: `追问失败：${error.message}` });
    renderChat();
    toast(error.message, "error", 6000);
  } finally {
    state.chat.streaming = false;
    $("#chat-send").disabled = false;
    $("#chat-input").disabled = false;
    $("#chat-status").textContent = "";
    if (!state.chat.messages[assistantIndex]?.content.trim()) {
      state.chat.messages[assistantIndex].content = "（模型没有返回内容，请换个问法再试一次。）";
      renderChat();
    }
    $("#chat-input").focus();
  }
}

function chatText(text) {
  // 模型偶尔仍会输出 Markdown。对话气泡按纯文本展示，这里做一次轻量清理。
  return String(text || "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "");
}

function parseSSEBlock(block) {
  const lines = block.split("\n");
  const dataLines = [];
  for (const line of lines) {
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  }
  if (!dataLines.length) return null;
  try {
    return JSON.parse(dataLines.join("\n"));
  } catch {
    return null;
  }
}

function handleChatEvent(payload, assistantIndex, bubble) {
  const data = payload.data || {};
  if (payload.type === "token") {
    state.chat.messages[assistantIndex].content += data.text || "";
    if (bubble) {
      bubble.textContent = chatText(state.chat.messages[assistantIndex].content);
      const box = $("#chat-messages");
      box.scrollTop = box.scrollHeight;
    }
  } else if (payload.type === "tool") {
    $("#chat-status").textContent = `正在调用：${toolLabel(data.name)}`;
  } else if (payload.type === "done") {
    $("#chat-status").textContent = "";
  } else if (payload.type === "error") {
    state.chat.messages.push({ role: "system", content: `追问失败：${data.message || "未知错误"}` });
    renderChat();
  } else if (payload.type === "meta") {
    $("#chat-status").textContent = "正在生成…";
  }
}

// ---------------------------------------------------------------- 历史
async function openHistory() {
  $("#history-overlay").classList.remove("hidden");
  const list = $("#history-list");
  list.innerHTML = '<p class="muted">加载中…</p>';
  try {
    const data = await fetchJSON("/api/history");
    const items = data.items || [];
    if (!items.length) {
      list.innerHTML = '<div class="empty-state">还没有历史报告。先分析一个仓库吧。</div>';
      return;
    }
    list.innerHTML = items
      .map(
        (item) => `<div class="history-item" data-run-id="${esc(item.run_id)}">
          <div class="h-top">
            <span class="h-name">${esc(item.repo_name)}</span>
            <span class="tag ${item.ai_used ? "good" : "warn"}">${item.ai_used ? "AI" : "规则"}</span>
          </div>
          <div class="h-meta">${esc(fmtDate(item.generated_at))} · ${fmtNumber(item.tech_count)} 项技术 · ${fmtNumber(
          item.code_files
        )} 个代码文件 · ${fmtNumber(item.total_loc)} 行</div>
          <div class="h-meta mono">${esc(truncate(item.source, 80))}</div>
        </div>`
      )
      .join("");
  } catch (error) {
    list.innerHTML = `<p class="muted">加载失败：${esc(error.message)}</p>`;
  }
}

// ---------------------------------------------------------------- 知识点
async function openConcepts() {
  $("#concepts-overlay").classList.remove("hidden");
  const list = $("#concepts-list");
  if (state.concepts) {
    renderConcepts();
    return;
  }
  list.innerHTML = '<p class="muted">加载中…</p>';
  try {
    const data = await fetchJSON("/api/concepts");
    state.concepts = data.concepts || [];
    renderConcepts();
  } catch (error) {
    list.innerHTML = `<p class="muted">加载失败：${esc(error.message)}</p>`;
  }
}

function renderConcepts() {
  const list = $("#concepts-list");
  list.innerHTML = (state.concepts || [])
    .map(
      (item) => `<details class="concept">
        <summary>
          <span class="c-title">${esc(item.title)}</span>
          <span class="c-chapter">${esc(item.chapter)}</span>
        </summary>
        <div class="c-summary">${esc(item.summary)}</div>
        <div class="c-detail">${esc(item.detail)}</div>
      </details>`
    )
    .join("");
}

// ---------------------------------------------------------------- 人工审批
function showHitl(data) {
  const modal = $("#hitl-modal");
  const actions = data.action_requests || [];
  const first = actions[0] || {};
  const args = first.args || {};
  const url = args.url || args.path || "";
  const description =
    first.description || data.description || "Agent 想要执行一个会联网/写磁盘的操作，是否允许？";
  $("#hitl-desc").textContent = description;
  $("#hitl-detail").textContent = url ? `目标：${url}` : JSON.stringify(args);

  const timeout = Number(data.timeout || 300);
  state.hitlDeadline = Date.now() + timeout * 1000;
  window.clearInterval(state.hitlTimer);
  const update = () => {
    const left = Math.max(0, Math.round((state.hitlDeadline - Date.now()) / 1000));
    $("#hitl-countdown").textContent = `剩余 ${fmtDuration(left)}，超时会自动拒绝。`;
    if (left <= 0) window.clearInterval(state.hitlTimer);
  };
  update();
  state.hitlTimer = window.setInterval(update, 1000);

  $("#btn-hitl-approve").disabled = false;
  $("#btn-hitl-reject").disabled = false;
  modal.classList.remove("hidden");
}

function hideHitl() {
  $("#hitl-modal").classList.add("hidden");
  window.clearInterval(state.hitlTimer);
  state.hitlTimer = null;
}

async function submitHitl(decision) {
  if (!state.current) return;
  $("#btn-hitl-approve").disabled = true;
  $("#btn-hitl-reject").disabled = true;
  try {
    await fetchJSON("/api/hitl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: state.current.runId, decision }),
    });
    hideHitl();
  } catch (error) {
    toast(error.message, "error", 6000);
    $("#btn-hitl-approve").disabled = false;
    $("#btn-hitl-reject").disabled = false;
  }
}

// ---------------------------------------------------------------- 导出
function download(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function exportJSON() {
  if (!state.report) return;
  const name = `${safeFileName(state.report.repo_name)}-repolens.json`;
  download(name, JSON.stringify(state.report, null, 2), "application/json;charset=utf-8");
  toast("JSON 已导出", "ok");
}

function exportMarkdown() {
  if (!state.report) return;
  const name = `${safeFileName(state.report.repo_name)}-repolens.md`;
  download(name, reportToMarkdown(state.report), "text/markdown;charset=utf-8");
  toast("Markdown 已导出", "ok");
}

function safeFileName(name) {
  return String(name || "repo").replace(/[\\/:*?"<>|\s]+/g, "-").slice(0, 60) || "repo";
}

function reportToMarkdown(report) {
  const lines = [];
  const stats = report.stats || {};
  lines.push(`# ${report.repo_name} · 技术栈报告`);
  lines.push("");
  lines.push(`> 来源：${report.source}  `);
  lines.push(`> 生成时间：${report.generated_at}  `);
  lines.push(`> 生成方式：${report.ai?.used ? `AI 解读（${report.ai.model}）` : "规则扫描"}`);
  lines.push("");
  lines.push("## 摘要");
  lines.push("");
  lines.push(report.summary || "");
  lines.push("");
  lines.push(
    `**规模**：${fmtNumber(stats.file_count)} 个文件 · ${fmtNumber(stats.code_file_count)} 个代码文件 · ${fmtNumber(
      stats.total_loc
    )} 行代码 · ${fmtNumber((report.techs || []).length)} 项技术`
  );
  lines.push("");

  if ((report.highlights || []).length) {
    lines.push("## 亮点");
    lines.push("");
    for (const item of report.highlights) lines.push(`- ${item}`);
    lines.push("");
  }

  lines.push("## 技术栈");
  lines.push("");
  const categories = report.categories || [];
  for (const category of categories) {
    const techs = (report.techs || []).filter((tech) => tech.category === category.name);
    if (!techs.length) continue;
    lines.push(`### ${category.name}`);
    lines.push("");
    for (const tech of techs) {
      lines.push(`- **${tech.name}**${tech.version ? ` v${tech.version}` : ""}（${tech.confidence}置信度）`);
      if (tech.role) lines.push(`  - 职责：${tech.role}`);
      if ((tech.modules || []).length) {
        const modules = tech.modules
          .slice(0, 8)
          .map((module) => `\`${module.path}:${module.line}\``)
          .join("、");
        lines.push(`  - 使用模块：${modules}`);
      } else {
        lines.push("  - 使用模块：仅依赖/配置中出现");
      }
    }
    lines.push("");
  }

  if ((report.architecture || []).length) {
    lines.push("## 架构解读");
    lines.push("");
    for (const item of report.architecture) lines.push(`- ${item}`);
    lines.push("");
  }
  if ((report.risks || []).length) {
    lines.push("## 风险与建议");
    lines.push("");
    for (const item of report.risks) lines.push(`- ${item}`);
    lines.push("");
  }
  if ((report.learning_path || []).length) {
    lines.push("## 学习路径");
    lines.push("");
    report.learning_path.forEach((item, index) => lines.push(`${index + 1}. ${item}`));
    lines.push("");
  }
  if ((report.manifests || []).length) {
    lines.push("## 依赖清单");
    lines.push("");
    for (const item of report.manifests) lines.push(`- \`${item.path}\`：${item.dependency_count} 条依赖`);
    lines.push("");
  }
  lines.push("---");
  lines.push("");
  lines.push("由 RepoLens 生成 · 扫描事实与 AI 解读已分别标注");
  return lines.join("\n");
}

// ---------------------------------------------------------------- 启动
init().catch((error) => {
  console.error(error);
  toast(`页面初始化失败：${error.message}`, "error", 8000);
});
