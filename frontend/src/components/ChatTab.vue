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
const busy = computed(() => state.chat.streaming);
const lastIndex = computed(() => state.chat.messages.length - 1);

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

    <div ref="messagesRef" class="chat-messages">
      <div v-if="!state.chat.messages.length" class="chat-empty">
        <div class="empty-icon"><Icon name="spark" :size="22" /></div>
        <b>报告已经生成，接下来可以继续问它。</b>
        <span>回答会先查报告和仓库文件，再组织语言，不会凭空编造。</span>
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
  gap: 6px;
  padding: 0 20px 12px;
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
}
</style>
