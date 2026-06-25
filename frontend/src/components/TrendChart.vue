<template>
  <template v-if="embedded">
    <div ref="chartEl" class="chart-container" v-show="data.length > 0"></div>
    <div v-if="data.length === 0" class="empty-state">
      <slot name="empty">
        <div class="icon">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
        </div>
        <p>{{ emptyText }}</p>
      </slot>
    </div>
  </template>
  <template v-else>
    <div class="page-card" style="margin-top:24px;">
      <div class="page-card-header"><h3>{{ title }}</h3></div>
      <div class="page-card-body">
        <div ref="chartEl" class="chart-container" v-show="data.length > 0"></div>
        <div v-if="data.length === 0" class="empty-state">
          <div class="icon">
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
          </div>
          <p>{{ emptyText }}</p>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  title: { type: String, default: '净值变化趋势' },
  emptyText: { type: String, default: '暂无数据记录' },
  valueKey: { type: String, default: 'net_worth' },
  dateKey: { type: String, default: 'snap_date' },
  color: { type: String, default: '#6750A4' },
  embedded: { type: Boolean, default: false },
  privacy: { type: Boolean, default: false },
  tooltipPrefix: { type: String, default: '净值' }
})

const chartEl = ref(null)
let chart = null

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function initChart() {
  if (!chartEl.value || props.data.length === 0) return
  if (!chart) chart = echarts.init(chartEl.value)
  const dates = props.data.map(d => d[props.dateKey]?.slice(5) || d.date || '')
  const values = props.data.map(d => d[props.valueKey] || 0)
  const isPrivate = props.privacy
  chart.setOption({
    grid: { top: 20, right: 20, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: '#ddd' } }, axisLabel: { color: '#999', fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { color: '#999', fontSize: 11, formatter: isPrivate ? () => '***' : (v => v >= 10000 ? (v / 10000).toFixed(1) + '万' : v) }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    series: [{
      type: 'line', data: values, smooth: true,
      symbol: isPrivate ? 'none' : 'circle', symbolSize: isPrivate ? 0 : 4,
      lineStyle: { color: props.color, width: 2 },
      itemStyle: { color: props.color },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: hexToRgba(props.color, 0.2) },
        { offset: 1, color: hexToRgba(props.color, 0.02) }
      ]) }
    }],
    tooltip: { trigger: 'axis', formatter: isPrivate ? () => '***' : (p => {
      const v = p[0]?.value || 0
      return `${p[0]?.axisValue}<br/><b>¥${v.toLocaleString(undefined, { minimumFractionDigits: 2 })}</b>`
    })}
  })
}

watch(() => props.data, () => {
  nextTick(() => initChart())
}, { deep: true })

watch(() => props.privacy, () => {
  nextTick(() => initChart())
})

onMounted(() => {
  nextTick(() => initChart())
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => chart?.resize())
  if (chart) { chart.dispose(); chart = null }
})
</script>

<style scoped>
.chart-container { width: 100%; height: 280px; }
.empty-state { text-align: center; padding: 40px 20px; color: var(--c-text-tertiary); }
.empty-state .icon { margin-bottom: 12px; }
.empty-state p { font-size: 14px; }
</style>
