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
  () =>
    Boolean(state.hitl) ||
    state.drawers.history ||
    state.drawers.concepts ||
    state.drawers.styles ||
    Boolean(state.drawers.techKey)
);

watch(overlayOpen, (open) => document.body.classList.toggle("no-scroll", Boolean(open)));

function onKeydown(event) {
  const target = event.target;
  const typing = target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);

  if (event.key === "Escape") {
    if (state.hitl) return; // 审批必须明确选择
    if (state.drawers.history || state.drawers.concepts || state.drawers.styles || state.drawers.techKey) {
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
      <span>RepoLens · 证据先于解释</span>
      <span>本地只读扫描 · 敏感信息脱敏</span>
      <a href="https://github.com/another0nobody/RepoLens" target="_blank" rel="noreferrer noopener">
        <Icon name="github" :size="13" /> GitHub
      </a>
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
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 34px 34px 76px;
}

.foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  max-width: 1320px;
  width: 100%;
  margin: 0 auto;
  padding: 16px 34px 24px;
  border-top: 1px solid var(--line-strong);
  color: var(--faint);
  font-size: 9px;
  letter-spacing: 0.04em;

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
    padding: 22px 16px 60px;
  }

  .foot {
    padding: 14px 16px 18px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
