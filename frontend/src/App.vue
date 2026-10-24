<script setup>
import { computed, onBeforeUnmount, onMounted, watch } from "vue";

import AppHeader from "./components/AppHeader.vue";
import ConceptsDrawer from "./components/ConceptsDrawer.vue";
import HistoryDrawer from "./components/HistoryDrawer.vue";
import HitlModal from "./components/HitlModal.vue";
import Icon from "./components/Icon.vue";
import TechDrawer from "./components/TechDrawer.vue";
import ToastHost from "./components/ToastHost.vue";
import HomeView from "./views/HomeView.vue";
import ReportView from "./views/ReportView.vue";
import RunView from "./views/RunView.vue";
import {
  closeOverlays,
  goHome,
  initApp,
  openConcepts,
  openHistory,
  state,
  toggleTheme,
} from "./store";

const overlayOpen = computed(
  () => Boolean(state.hitl) || state.drawers.history || state.drawers.concepts || Boolean(state.drawers.techKey)
);

watch(overlayOpen, (open) => document.body.classList.toggle("no-scroll", Boolean(open)));

function onKeydown(event) {
  const target = event.target;
  const typing = target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);

  if (event.key === "Escape") {
    if (state.hitl) return; // 审批必须明确选择
    if (state.drawers.history || state.drawers.concepts || state.drawers.techKey) {
      closeOverlays();
    }
    return;
  }

  if (typing) return;

  if (event.key === "/" && state.view === "report" && state.tab === "stack") {
    event.preventDefault();
    document.querySelector(".search-wrap input")?.focus();
  }
}

onMounted(() => {
  initApp();
  window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.body.classList.remove("no-scroll");
});
</script>

<template>
  <div class="app">
    <div class="app-bg" aria-hidden="true">
      <div class="bg-grid"></div>
      <div class="bg-glow glow-a"></div>
      <div class="bg-glow glow-b"></div>
      <div class="bg-glow glow-c"></div>
    </div>

    <AppHeader
      :health="state.health"
      :theme="state.theme"
      @brand="goHome"
      @history="openHistory"
      @concepts="openConcepts"
      @toggle-theme="toggleTheme"
    />

    <main class="shell">
      <Transition name="page" mode="out-in">
        <HomeView v-if="state.view === 'home'" key="home" />
        <RunView v-else-if="state.view === 'run'" key="run" />
        <ReportView v-else key="report" />
      </Transition>
    </main>

    <footer class="foot">
      <span>RepoLens · 一个用来学习 LangChain Agent 的小项目</span>
      <span class="foot-right">
        <span>扫描在本地完成 · 只有必要的事实会发送给模型</span>
        <a href="https://github.com/another0nobody/RepoLens" target="_blank" rel="noreferrer noopener">
          <Icon name="github" :size="14" /> GitHub
        </a>
      </span>
    </footer>

    <TechDrawer />
    <HistoryDrawer />
    <ConceptsDrawer />
    <HitlModal />
    <ToastHost />
  </div>
</template>

<style scoped lang="less">
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.shell {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 40px 26px 90px;
}

.foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: 20px 26px 30px;
  border-top: 1px solid var(--line);
  color: var(--faint);
  font-size: 11px;
}

.foot-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;

  a {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: var(--muted);

    &:hover {
      color: var(--accent);
    }
  }
}

@media (max-width: @bp-md) {
  .shell {
    padding: 26px 16px 70px;
  }

  .foot {
    padding: 16px;
    flex-direction: column;
  }
}
</style>
