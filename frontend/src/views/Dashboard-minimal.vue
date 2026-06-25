<template>
  <div>
    <div style="background:lime;color:black;padding:10px;font-size:18px;font-weight:bold;margin-bottom:10px;">MINIMAL TEST: Dashboard 渲染成功</div>
    <div class="top-fixed-grid">
      <div class="stat-card glass-card card-primary">
        <div class="label">净资产</div>
        <div class="value">¥1,080,327.05</div>
        <div class="sub">净值 = 总资产 - 总负债</div>
      </div>
      <div class="stat-card glass-card card-info">
        <div class="label">总资产</div>
        <div class="value">¥1,100,000.00</div>
        <div class="sub">所有资产总和</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const test = ref('hello')
</script>

<style scoped>
/* 复用原始 Dashboard 中的关键 CSS */
.top-fixed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.glass-card {
  background: rgba(255, 251, 254, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 0.5px solid rgba(103, 80, 164, 0.08);
  box-shadow: var(--md-elevation-3);
}
.card-primary .value { color: var(--md-primary); }
.card-info .value { color: var(--md-secondary); }
</style>
