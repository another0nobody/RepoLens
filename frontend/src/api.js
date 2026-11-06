/** 与 Python 后端通信的薄封装。 */

/** 检查回答中的文件/行号引用是否能在报告中核对。 */
export async function fetchGrounding(runId, text) {
  return fetchJSON("/api/ground", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, text }),
  });
}

/** 可选的语义核对：让模型判断引用是否真的支持回答结论。 */
export async function fetchSemanticGrounding(runId, text) {
  return fetchJSON("/api/ground/semantic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, text }),
  });
}

/** 读取报告的风险面板。 */
export async function fetchRisks(runId) {
  return fetchJSON(`/api/risks?run_id=${encodeURIComponent(runId)}`);
}

/** 生成某技术的 ADR Markdown。 */
export async function fetchAdr(runId, tech) {
  return fetchJSON(
    `/api/adr?run_id=${encodeURIComponent(runId)}&tech=${encodeURIComponent(tech)}`
  );
}

/** 读取证据对应的一小段源码。 */
export async function fetchCode(runId, path, line = 1) {
  return fetchJSON(
    `/api/file?run_id=${encodeURIComponent(runId)}&path=${encodeURIComponent(path)}&line=${encodeURIComponent(line)}`
  );
}

/** 对比两份报告。 */
export async function fetchDiff(baseId, targetId) {
  return fetchJSON(
    `/api/diff?base=${encodeURIComponent(baseId)}&target=${encodeURIComponent(targetId)}`
  );
}

/** 读取一次运行的历史追问（SQLite 持久化后，刷新页面仍能恢复）。 */
export async function fetchChatHistory(runId) {
  return fetchJSON(`/api/chat/history?run_id=${encodeURIComponent(runId)}`);
}

export async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  const type = response.headers.get("content-type") || "";
  const body = type.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = body && body.error ? body.error : `请求失败（HTTP ${response.status}）`;
    throw new Error(message);
  }
  return body;
}

/**
 * 读取 POST 的 SSE 响应（追问接口使用）。
 *
 * @param {Object} payload 请求参数
 * @param {string} payload.runId 分析运行 ID
 * @param {string} payload.message 用户追问内容
 * @param {AbortSignal} [payload.signal] 可选的取消信号
 * @param {Function} onEvent 收到 SSE 事件时调用
 * @returns {Promise<void>} 流读取完成
 */
export async function streamChatRequest(payload, onEvent) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: payload.runId, message: payload.message }),
    signal: payload.signal,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `请求失败（HTTP ${response.status}）`);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式读取");
  }

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
      const lines = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart());
      if (!lines.length) continue;
      try {
        onEvent(JSON.parse(lines.join("\n")));
      } catch {
        /* 忽略无法解析的心跳/片段 */
      }
    }
  }
}
