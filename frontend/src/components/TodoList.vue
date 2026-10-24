<script setup>
defineProps({
  todos: { type: Array, default: () => [] },
});
</script>

<template>
  <ul v-if="todos.length" class="todos">
    <li v-for="(todo, index) in todos" :key="`${todo.content}-${index}`" :class="todo.status || 'pending'">
      <span class="mark" aria-hidden="true">
        {{ todo.status === "completed" ? "✓" : todo.status === "in_progress" ? "•" : "" }}
      </span>
      <span class="content">{{ todo.content }}</span>
    </li>
  </ul>
  <p v-else class="empty">等待模型制定计划…</p>
</template>

<style scoped lang="less">
.todos {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;

  li {
    display: flex;
    gap: 9px;
    font-size: 12px;
    line-height: 1.55;
    color: var(--muted);
    transition: color 0.25s;
  }

  .mark {
    display: grid;
    place-items: center;
    width: 16px;
    height: 16px;
    margin-top: 1px;
    flex: none;
    border-radius: 5px;
    border: 1px solid var(--line-strong);
    font-size: 10px;
    line-height: 1;
  }

  .completed {
    color: var(--faint);

    .content {
      text-decoration: line-through;
      text-decoration-color: var(--line-strong);
    }

    .mark {
      color: var(--good);
      border-color: color-mix(in srgb, var(--good) 50%, transparent);
      background: var(--good-soft);
    }
  }

  .in_progress {
    color: var(--text);

    .mark {
      color: var(--accent);
      border-color: var(--accent);
      background: var(--accent-soft);
      box-shadow: 0 0 10px -2px var(--accent);
    }
  }
}

.empty {
  margin: 0;
  color: var(--faint);
  font-size: 12px;
}
</style>
