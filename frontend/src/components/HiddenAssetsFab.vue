<template>
  <div v-if="hiddenItems.length" class="hidden-fab" :class="{ open: show }">
    <button class="hidden-fab-btn" @click="show = !show" :title="'已隐藏 ' + hiddenItems.length + ' 项'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
      </svg>
      <span class="hidden-fab-badge">{{ hiddenItems.length }}</span>
    </button>
    <div v-if="show" class="hidden-popover">
      <div class="hidden-popover-title">{{ title }}</div>
      <template v-for="item in hiddenItems" :key="item.key">
        <div v-if="item.children" class="hidden-item" style="flex-direction:column; align-items:flex-start; gap:6px;">
          <span style="font-size:11px; color:var(--c-text-tertiary);">{{ item.label }}</span>
          <div v-for="child in item.children" :key="child.key" style="display:flex; align-items:center; justify-content:space-between; width:100%;">
            <span class="hidden-item-label">{{ child.label }}</span>
            <button class="restore-btn" @click="$emit('restore', child.key, item.mid)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              恢复
            </button>
          </div>
        </div>
        <div v-else class="hidden-item">
          <span class="hidden-item-label">{{ item.label }}</span>
          <button class="restore-btn" @click="$emit('restore', item.key)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            恢复
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  hiddenItems: { type: Array, default: () => [] },
  title: { type: String, default: '已隐藏的资产' },
})
defineEmits(['restore'])

const show = ref(false)
</script>

<style scoped>
.hidden-fab { position: fixed; bottom: 24px; right: 24px; z-index: 100; }
.hidden-fab-btn {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--md-surface-container-highest);
  color: var(--c-text); border: none; box-shadow: var(--md-elevation-3);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  position: relative; transition: all 0.2s var(--ease-emphasized);
}
.hidden-fab-btn:hover { background: var(--md-surface-container-high); box-shadow: var(--md-elevation-4); transform: scale(1.05); }
.hidden-fab-btn svg { width: 24px; height: 24px; }
.hidden-fab-badge {
  position: absolute; top: -4px; right: -4px; background: var(--md-error);
  color: var(--md-on-error); font-size: 11px; font-weight: 700; min-width: 18px; height: 18px;
  border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px;
}
.hidden-popover {
  position: absolute; bottom: 64px; right: 0; width: 240px;
  background: var(--md-surface); border-radius: var(--radius-xl);
  box-shadow: var(--md-elevation-4); border: 1px solid var(--md-outline-variant); overflow: hidden;
}
.hidden-popover-title {
  padding: 16px; font-weight: 600; font-size: 14px; color: var(--c-text-secondary);
  border-bottom: 1px solid var(--md-outline-variant);
}
.hidden-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--md-outline-variant); }
.hidden-item:last-child { border-bottom: none; }
.hidden-item-label { font-size: 14px; color: var(--c-text); }
.restore-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px;
  border-radius: var(--radius-full); background: var(--md-surface-container-highest);
  color: var(--c-text); font-size: 13px; font-weight: 500; border: none; cursor: pointer; transition: all 0.2s;
}
.restore-btn:hover { background: var(--md-surface-container-high); color: var(--md-primary); }
.restore-btn svg { width: 14px; height: 14px; }
@media (max-width: 600px) {
  .hidden-fab { bottom: 80px; right: 16px; }
  .hidden-fab-btn { width: 48px; height: 48px; }
  .hidden-popover { bottom: 56px; right: 0; width: 220px; }
}
</style>
