<template>
  <div v-if="summary.total_cost > 0" class="invest-summary-card">
    <div class="invest-summary-header">{{ title }}</div>
    <div class="invest-summary-grid">
      <div class="invest-summary-item">
        <div class="invest-summary-label">总成本</div>
        <div class="invest-summary-value">{{ format(summary.total_cost) }}</div>
      </div>
      <div class="invest-summary-item">
        <div class="invest-summary-label">总市值</div>
        <div class="invest-summary-value">{{ format(summary.total_market_value) }}</div>
      </div>
      <div class="invest-summary-item" :class="{ profit: summary.total_profit >= 0, loss: summary.total_profit < 0 }">
        <div class="invest-summary-label">总盈亏</div>
        <div class="invest-summary-value">{{ fmtProfit(summary.total_profit) }}</div>
      </div>
      <div class="invest-summary-item" :class="{ profit: summary.total_profit >= 0, loss: summary.total_profit < 0 }">
        <div class="invest-summary-label">盈亏率</div>
        <div class="invest-summary-value">{{ summary.total_profit_pct >= 0 ? '+' : '' }}{{ summary.total_profit_pct.toFixed(2) }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAmountFormat, formatAmountNumber } from '../composables/useAmountFormat'
defineProps({ summary: Object, title: { type: String, default: '投资汇总' } })
const { format } = useAmountFormat()

function fmtProfit(v) {
  return v >= 0 ? format(v) : '¥-' + formatAmountNumber(Math.abs(v))
}
</script>

<style scoped>
.invest-summary-card {
  margin-top: var(--space-4); margin-bottom: var(--space-4); padding: 20px;
  background: var(--md-surface-container-low); border-radius: var(--radius-xl); border: 1px solid var(--md-outline-variant);
}
.invest-summary-header {
  font-size: 14px; font-weight: 700; color: var(--c-text-secondary); margin-bottom: 16px;
  padding-bottom: 8px; border-bottom: 1px solid var(--md-outline-variant);
}
.invest-summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; }
.invest-summary-item { text-align: center; }
.invest-summary-label { font-size: 12px; color: var(--c-text-tertiary); margin-bottom: 4px; }
.invest-summary-value { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; color: var(--c-text); }
.invest-summary-item.profit .invest-summary-value { color: #10b981; }
.invest-summary-item.loss .invest-summary-value { color: #ef4444; }
</style>
