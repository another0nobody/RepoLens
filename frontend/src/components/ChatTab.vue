<script setup>
import { computed, nextTick, ref, watch } from "vue";

import Icon from "./Icon.vue";
import { chatText } from "../utils";
import { sendChat, state } from "../store";

const input = ref("");
const messagesRef = ref(null);
const suggestions = [
  "这个项目最核心的技术是什么？",
  "数据库和缓存分别用在哪里？",
  "我应该先读哪些文件？",
  "有没有测试，覆盖了什么？",
];

const DEEP_DIVE_LENSES = [
  {
    key: "advantages",
    label: "优势与场景",
    hint: "它擅长什么，在本项目解决了什么",
  },
  {
    key: "pitfalls",
    label: "难点与易错点",
    hint: "常见坑、边界与规避方式",
  },
  {
    key: "compare",
    label: "相似方案差异",
    hint: "和 2–3 个同类技术比，差在哪",
  },
  {
    key: "why",
    label: "为什么选它",
    hint: "选型理由、代价与替代方案",
  },
];

const techOptions = computed(() => {
  const techs = (state.report?.techs || []).filter((tech) => tech?.name);
  const score = (tech) => {
    const modules = (tech.modules || []).length;
    const confidence = tech.confidence === "高" ? 2 : tech.confidence === "中" ? 1 : 0;
    const languagePenalty = tech.category === "编程语言" ? 2 : 0;
    return modules * 3 + confidence - languagePenalty;
  };
  return [...techs].sort((a, b) => score(b) - score(a) || String(a.name).localeCompare(String(b.name))).slice(0, 12);
});
const selectedTechKey = ref("");
const selectedTech = computed(() => techOptions.value.find((tech) => tech.key === selectedTechKey.value) || null);
const busy = computed(() => state.chat.streaming);
const lastIndex = computed(() => state.chat.messages.length - 1);

watch(
  () => techOptions.value.map((tech) => tech.key).join("|"),
  () => {
    if (!techOptions.value.some((tech) => tech.key === selectedTechKey.value)) {
      selectedTechKey.value = techOptions.value[0]?.key || "";
    }
  },
  { immediate: true }
);

function deepDivePrompt(lens) {
  const tech = selectedTech.value;
  if (!tech) return "";
  const name = `${tech.name}（${tech.category}）`;
  if (lens.key === "advantages") {
    return `请从项目实际出发，深入分析 ${name} 的优势、适用场景，以及它在这个仓库里具体解决了什么问题。`;
  }
  if (lens.key === "pitfalls") {
    return `围绕 ${name}，分析在这个项目中使用它时最容易踩坑的难点、常见错误和规避方式。`;
  }
  if (lens.key === "compare") {
    return `${name} 和功能相似的其他技术（请给出 2–3 个同类方案）有什么区别？请结合本项目说明什么时候该选谁。`;
  }
  return `这个项目为什么选择 ${name} 而不是功能相似的方案？请区分报告中能确认的事实与基于技术常识的推断，不要编造项目动机。`;
}

function askDeepDive(lens) {
  if (busy.value || !selectedTech.value) return;
  sendChat(deepDivePrompt(lens));
}

async function scrollToBottom() {
  await nextTick();
  const el = messagesRef.value;
  if (el) el.scrollTop = el.scrollHeight;
}

function submit() {
  const text = input.value.trim();
  if (!text || busy.value) return;
  input.value = "";
  sendChat(text);
}

function useSuggestion(text) {
  input.value = text;
  submit();
}

watch(
  () => [state.chat.messages.length, state.chat.messages[lastIndex.value]?.content, state.chat.status],
  () => scrollToBottom()
);

watch(
  () => state.tab,
  async (tab) => {
    if (tab === "chat") {
      await nextTick();
      document.querySelector(".chat-form input")?.focus();
    }
  }
);
</script>

<template>
  <div class="chat-card">
    <header class="chat-head">
      <div>
        <h3>追问这份报告</h3>
        <p class="muted">回答基于报告与仓库文件，不会凭空编造；多轮对话有记忆。</p>
      </div>
      <span class="chat-status">
        <span v-if="busy" class="typing-dot"></span>
        {{ state.chat.status }}
      </span>
    </header>

    <section v-if="techOptions.length" class="deep-dive" aria-label="技术深挖模板">
      <div class="dd-head">
        <span class="dd-title"><Icon name="layers" :size="14" /> 技术深挖</span>
        <label class="dd-picker">
          <span class="sr-only">选择要深挖的技术</span>
          <select v-model="selectedTechKey" class="dd-select" :disabled="busy">
            <option v-for="tech in techOptions" :key="tech.key" :value="tech.key">
              {{ tech.name }} · {{ tech.category }}
            </option>
          </select>
        </label>
      </div>

      <div class="dd-grid">
        <button
          v-for="lens in DEEP_DIVE_LENSES"
          :key="lens.key"
          class="dd-card"
          type="button"
          :disabled="busy"
          :title="`${lens.label}：${lens.hint}`"
          @click="askDeepDive(lens)"
        >
          <b>{{ lens.label }}</b>
          <span>{{ lens.hint }}</span>
        </button>
      </div>
      <p class="dd-note">回答会区分「报告中的事实」与「通用技术判断」，不编造项目动机。</p>
    </section>

    <div ref="messagesRef" class="chat-messages">
      <div v-if="!state.chat.messages.length" class="chat-empty">
        <div class="empty-icon"><Icon name="spark" :size="22" /></div>
        <b>报告已经生成，接下来可以继续问它。</b>
        <span v-if="techOptions.length">上方选择一项技术，可以从优势、难点、相似方案和选型理由四个方向深挖；也可以直接问下面的项目级问题。</span>
        <span v-else>回答会先查报告和仓库文件，再组织语言，不会凭空编造。</span>
      </div>

      <div v-for="(message, index) in state.chat.messages" :key="index" class="msg" :class="message.role">
        <template v-if="message.role === 'system'">
          <div class="bubble system-bubble">{{ message.content }}</div>
        </template>
        <template v-else>
          <div class="avatar" aria-hidden="true">
            {{ message.role === "user" ? "你" : "◈" }}
          </div>
          <div class="bubble">
            {{ message.role === "assistant" ? chatText(message.content) : message.content }}
            <span
              v-if="busy && index === lastIndex && message.role === 'assistant'"
              class="caret"
              aria-hidden="true"
            ></span>
          </div>
        </template>
      </div>
    </div>

    <div v-if="!state.chat.messages.length" class="chat-suggestions">
      <span class="suggestions-label">项目级问题</span>
      <button v-for="text in suggestions" :key="text" class="chip" type="button" @click="useSuggestion(text)">
        {{ text }}
      </button>
    </div>

    <form class="chat-form" @submit.prevent="submit">
      <input
        v-model="input"
        type="text"
        placeholder="例如：数据库和缓存分别用在哪里？"
        aria-label="追问内容"
        :disabled="busy"
      />
      <button class="btn btn-primary" type="submit" :disabled="busy || !input.trim()">
        <span v-if="busy" class="send-spinner"></span>
        <span v-else>发送</span>
      </button>
    </form>
  </div>
</template>

<style scoped lang="less">
.chat-card {
  display: flex;
  flex-direction: column;
  min-height: 580px;
  border-radius: @radius-xl;
  border: 1px solid var(--line);
  background: var(--panel);
  overflow: hidden;
}

.chat-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--line);

  h3 {
    margin: 0 0 3px;
    font-size: 14.5px;
  }

  p {
    margin: 0;
    font-size: 11.5px;
  }
}

.chat-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--accent);
  font-size: 10.5px;
  white-space: nowrap;
  min-height: 16px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.1s infinite;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 52vh;
  .scrollbar();
}

.deep-dive {
  margin: 12px 18px 0;
  padding: 11px 13px 10px;
  border: 1px solid var(--line);
  border-radius: @radius-md;
  background: color-mix(in srgb, var(--panel-soft) 75%, transparent);
}

.dd-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.dd-title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 650;
  letter-spacing: 0.2px;
}

.dd-picker {
  margin-left: auto;
}

.dd-select {
  max-width: 250px;
  padding: 5px 9px;
  border: 1px solid var(--line);
  border-radius: @radius-sm;
  background: var(--input-bg);
  color: var(--text);
  font-size: 11px;
  outline: none;
  cursor: pointer;

  &:focus {
    border-color: var(--accent-line);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
}

.dd-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  margin-top: 9px;
}

.dd-card {
  min-width: 0;
  padding: 8px 9px;
  border: 1px solid var(--line);
  border-radius: @radius-sm;
  background: var(--panel);
  color: var(--text);
  text-align: left;
  transition: border-color 0.16s, background 0.16s, transform 0.16s;
  .focus-ring();

  b {
    display: block;
    font-size: 11px;
    font-weight: 650;
    line-height: 1.4;
  }

  span {
    display: block;
    margin-top: 2px;
    color: var(--faint);
    font-size: 9.5px;
    line-height: 1.45;
  }

  &:hover:not(:disabled) {
    border-color: var(--accent-line);
    background: var(--accent-soft);
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

.dd-note {
  margin: 7px 0 0;
  color: var(--faint);
  font-size: 9.5px;
  line-height: 1.5;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 48px 20px;
  text-align: center;
  color: var(--faint);
  font-size: 12.5px;
  line-height: 1.8;

  b {
    color: var(--muted);
    font-weight: 600;
  }
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin-bottom: 4px;
  border-radius: 13px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-line);
}

.msg {
  display: flex;
  gap: 9px;
  max-width: 90%;
  animation: fade-up 0.24s @ease-out;

  .avatar {
    flex: none;
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 9px;
    border: 1px solid var(--line);
    background: var(--panel-soft);
    color: var(--muted);
    font-size: 11px;
  }

  .bubble {
    padding: 11px 14px;
    border-radius: 13px;
    border-top-left-radius: 4px;
    background: var(--panel-soft);
    border: 1px solid var(--line);
    color: var(--text);
    font-size: 13px;
    line-height: 1.75;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;

  .bubble {
    border-radius: 13px;
    border-top-right-radius: 4px;
    border-color: var(--accent-line);
    background: linear-gradient(140deg, var(--accent-soft), color-mix(in srgb, var(--accent-2) 14%, transparent));
  }

  .avatar {
    color: var(--accent);
    border-color: var(--accent-line);
  }
}

.msg.system {
  max-width: 100%;

  .system-bubble {
    background: transparent;
    border: 0;
    color: var(--faint);
    font-size: 11px;
    padding: 0 4px;
  }
}

.caret {
  display: inline-block;
  width: 6px;
  height: 13px;
  margin-left: 2px;
  vertical-align: -2px;
  background: var(--accent);
  border-radius: 1px;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.chat-suggestions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 0 20px 12px;
}

.suggestions-label {
  width: 100%;
  color: var(--faint);
  font-size: 9.5px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.chat-form {
  display: flex;
  gap: 8px;
  padding: 14px 18px 18px;
  border-top: 1px solid var(--line);

  input {
    flex: 1;
    min-width: 0;
    padding: 11px 14px;
    border-radius: 11px;
    border: 1px solid var(--line);
    background: var(--input-bg);
    outline: none;
    font-size: 12.5px;
    transition: border-color 0.18s, box-shadow 0.18s;

    &:focus {
      border-color: var(--accent-line);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }

    &:disabled {
      opacity: 0.6;
    }
  }

  .btn {
    min-width: 78px;
  }
}

.send-spinner {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(4, 18, 26, 0.25);
  border-top-color: #04121a;
  animation: spin 0.8s linear infinite;
}

@media (max-width: @bp-md) {
  .chat-messages {
    max-height: 44vh;
  }

  .chat-status {
    display: none;
  }

  .dd-grid {
    grid-template-columns: 1fr 1fr;
  }

  .dd-picker {
    width: 100%;
    margin-left: 0;
  }

  .dd-select {
    width: 100%;
    max-width: none;
  }
}
</style>
