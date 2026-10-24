export const CATEGORY_COLORS = {
  编程语言: "#94a3b8",
  前端框架: "#f0abfc",
  后端框架: "#67e8f9",
  "AI & Agent": "#a78bfa",
  数据库: "#fbbf24",
  缓存与消息: "#fb923c",
  基础设施与运维: "#38bdf8",
  测试与质量: "#34d399",
  构建与工具链: "#cbd5e1",
  数据科学: "#f472b6",
  监控与观测: "#22d3ee",
  其他依赖: "#64748b",
};

export const CATEGORY_ICONS = {
  编程语言: "◇",
  前端框架: "◈",
  "后端框架": "▣",
  "AI & Agent": "✳",
  数据库: "▤",
  缓存与消息: "◫",
  基础设施与运维: "⬡",
  测试与质量: "✓",
  构建与工具链: "⚙",
  数据科学: "◔",
  监控与观测: "◉",
  其他依赖: "□",
};

export const TOOL_LABELS = {
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

export const STAGES = [
  { key: "prepare", label: "检查环境", hint: "模型、路径、运行条件" },
  { key: "scan", label: "扫描仓库", hint: "文件、依赖、import" },
  { key: "agent", label: "Agent 核实", hint: "逐项确认技术与模块" },
  { key: "report", label: "生成报告", hint: "合并事实与 AI 解读" },
];

export const TABS = [
  { key: "stack", label: "技术栈" },
  { key: "modules", label: "模块地图" },
  { key: "architecture", label: "架构解读" },
  { key: "chat", label: "追问" },
  { key: "process", label: "分析过程" },
];

export function fmtNumber(value) {
  return Number(value || 0).toLocaleString("zh-CN");
}

export function fmtDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

export function fmtTime(tsSeconds) {
  try {
    return new Date(Number(tsSeconds) * 1000).toLocaleTimeString("zh-CN", { hour12: false });
  } catch {
    return "--:--:--";
  }
}

export function fmtDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("zh-CN", { hour12: false });
  } catch {
    return iso;
  }
}

export function basename(source) {
  const text = String(source || "").replace(/[\\/]+$/, "");
  return text.split(/[\\/]/).pop() || text || "仓库";
}

export function detectSource(source) {
  const text = String(source || "").trim();
  if (!text) return { kind: "empty", label: "等待输入" };
  if (/^https?:\/\/(www\.)?github\.com\/[^/\s]+\/[^/\s]+\/?$/i.test(text)) {
    return { kind: "github", label: "GitHub 仓库" };
  }
  // 浏览器无法访问文件系统，所以出现「恰好两段」时无法判断是 owner/repo 还是 examples/demo_shop。
  // 交给后端的路径校验决定；这里显示为“模糊”，避免误导。
  if (/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(text) && !/[\\:]/.test(text) && !text.startsWith(".")) {
    return { kind: "ambiguous", label: "GitHub 简写或相对路径" };
  }
  return { kind: "local", label: "本地目录" };
}

export function categoryColor(category) {
  return CATEGORY_COLORS[category] || "#64748b";
}

export function categoryIcon(category) {
  return CATEGORY_ICONS[category] || "◇";
}

export function confidenceClass(confidence) {
  return confidence === "高" ? "high" : confidence === "中" ? "mid" : "low";
}

export function toolLabel(name) {
  return TOOL_LABELS[name] || name;
}

export function truncate(text, limit = 140) {
  const value = String(text || "");
  return value.length > limit ? `${value.slice(0, limit)}…` : value;
}

export function argsPreview(args) {
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

/** 对话气泡按纯文本展示，模型偶尔残留的 Markdown 做轻量清理。 */
export function chatText(text) {
  return String(text || "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "");
}

export function safeFileName(name) {
  return String(name || "repo").replace(/[\\/:*?"<>|\s]+/g, "-").slice(0, 60) || "repo";
}

export function download(filename, content, mime) {
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

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(String(text));
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = String(text);
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch {
      ok = false;
    }
    area.remove();
    return ok;
  }
}

export function reportToMarkdown(report) {
  const lines = [];
  const stats = report.stats || {};
  lines.push(`# ${report.repo_name} · 技术栈报告`, "");
  lines.push(`> 来源：${report.source}  `);
  lines.push(`> 生成时间：${report.generated_at}  `);
  lines.push(`> 生成方式：${report.ai?.used ? `AI 解读（${report.ai.model}）` : "规则扫描"}`, "");
  lines.push("## 摘要", "", report.summary || "", "");
  lines.push(
    `**规模**：${fmtNumber(stats.file_count)} 个文件 · ${fmtNumber(stats.code_file_count)} 个代码文件 · ${fmtNumber(
      stats.total_loc
    )} 行代码 · ${fmtNumber((report.techs || []).length)} 项技术`,
    ""
  );

  if ((report.highlights || []).length) {
    lines.push("## 亮点", "");
    report.highlights.forEach((item) => lines.push(`- ${item}`));
    lines.push("");
  }

  lines.push("## 技术栈", "");
  for (const category of report.categories || []) {
    const techs = (report.techs || []).filter((tech) => tech.category === category.name);
    if (!techs.length) continue;
    lines.push(`### ${category.name}`, "");
    for (const tech of techs) {
      lines.push(`- **${tech.name}**${tech.version ? ` v${tech.version}` : ""}（${tech.confidence}置信度）`);
      if (tech.role) lines.push(`  - 职责：${tech.role}`);
      if ((tech.modules || []).length) {
        lines.push(
          `  - 使用模块：${tech.modules
            .slice(0, 8)
            .map((module) => `\`${module.path}:${module.line}\``)
            .join("、")}`
        );
      } else {
        lines.push("  - 使用模块：仅依赖/配置中出现");
      }
    }
    lines.push("");
  }

  for (const [key, title] of [
    ["architecture", "架构解读"],
    ["risks", "风险与建议"],
  ]) {
    if ((report[key] || []).length) {
      lines.push(`## ${title}`, "");
      report[key].forEach((item) => lines.push(`- ${item}`));
      lines.push("");
    }
  }

  if ((report.learning_path || []).length) {
    lines.push("## 学习路径", "");
    report.learning_path.forEach((item, index) => lines.push(`${index + 1}. ${item}`));
    lines.push("");
  }

  if ((report.manifests || []).length) {
    lines.push("## 依赖清单", "");
    report.manifests.forEach((item) => lines.push(`- \`${item.path}\`：${item.dependency_count} 条依赖`));
    lines.push("");
  }

  lines.push("---", "", "由 RepoLens 生成 · 扫描事实与 AI 解读已分别标注");
  return lines.join("\n");
}
