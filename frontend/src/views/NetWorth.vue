<template>
  <div>
    <div class="page-card" style="margin-bottom:24px;">
      <div class="page-card-header">
        <h3>当前净值</h3>
        <el-button type="primary" @click="takeSnap">记录当前快照</el-button>
      </div>
      <div class="page-card-body">
        <div class="stat-grid">
          <div class="stat-card card-primary">
            <div class="label">当前净值</div>
            <div class="value">{{ fmt(rawNetWorth) }}</div>
          </div>
          <div class="stat-card card-info">
            <div class="label">总资产</div>
            <div class="value">{{ fmt(rawTotalAsset) }}</div>
          </div>
          <div class="stat-card card-danger">
            <div class="label">总负债</div>
            <div class="value">{{ fmt(current.total_liability || 0) }}</div>
          </div>
          <div class="stat-card" v-if="lastSnapshot">
            <div class="label">上次快照 ({{ lastSnapshot.snap_date }})</div>
            <div class="value" :style="privacyMode ? {} : { color: rawDiff >= 0 ? '#10b981' : '#ef4444' }">
              {{ fmt(lastSnapshot.net_worth) }}
            </div>
            <div class="sub">
              {{ privacyMode ? '***' : (rawDiff >= 0 ? '+' : '') + formatAmount(rawDiff) + ' 变动' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-card">
      <div class="page-card-header">
        <h3>净值趋势</h3>
        <el-button size="small" @click="loadAll">刷新</el-button>
      </div>
      <div class="page-card-body">
        <div ref="chartRef" class="chart-container" v-show="displaySnapshots.length > 0"></div>
        <div v-if="displaySnapshots.length === 0" class="empty-state">
          <div class="icon">📈</div>
          <p>暂无快照，点击上方按钮记录</p>
        </div>
      </div>
    </div>

    <div class="page-card" style="margin-top:24px;">
      <div class="page-card-header"><h3>历史快照</h3></div>
      <div class="page-card-body">
        <el-table :data="snapshots" empty-text="暂无快照">
          <el-table-column prop="snap_date" label="日期" width="120" />
          <el-table-column label="总资产" width="150">
            <template #default="{ row }">{{ fmt(row.total_asset) }}</template>
          </el-table-column>
          <el-table-column label="总负债" width="150">
            <template #default="{ row }">{{ fmt(row.total_debt) }}</template>
          </el-table-column>
          <el-table-column label="净值" width="150">
            <template #default="{ row }">{{ fmt(row.net_worth) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { getSummary, takeSnapshot, listSnapshots, deleteSnapshot } from '../api'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatAmount } from '../composables/useAmountFormat'
import { usePrivacy } from '../composables/usePrivacy'

const { privacyMode, hiddenAssets } = usePrivacy()

const current = reactive({
  net_worth: 0, total_asset: 0, total_liability: 0,
  cash: 0, deposit: 0, fund: 0, stock: 0, bond: 0, precious_metal: 0,
})
const lastSnapshot = ref(null)
const snapshots = ref([])
const chartRef = ref(null)
let chart = null

// ── 工具函数 ──
function fmt(val) {
  if (privacyMode.value) return '***'
  return formatAmount(val)
}

// ── 第1层：hiddenAssets 计算排除 ──
// 从当前汇总中扣除被隐藏的资产类别金额
const hiddenExcluded = computed(() =>
  hiddenAssets.value.reduce((sum, cat) => sum + (current[cat] || 0), 0)
)

const rawNetWorth = computed(() => current.net_worth - hiddenExcluded.value)
const rawTotalAsset = computed(() => current.total_asset - hiddenExcluded.value)
const rawDiff = computed(() =>
  lastSnapshot.value ? (current.net_worth || 0) - lastSnapshot.value.net_worth : 0
)

// 快照排除隐藏类别（用于图表渲染），不受 privacyMode 影响
const displaySnapshots = computed(() => {
  if (hiddenAssets.value.length === 0) return snapshots.value
  return snapshots.value.map(s => {
    const excluded = hiddenAssets.value.reduce((sum, cat) => sum + (s[cat] || 0), 0)
    return {
      ...s,
      net_worth: s.net_worth - excluded,
      total_asset: s.total_asset - excluded,
    }
  })
})

// ── 数据加载 ──
async function loadAll() {
  try {
    const { data: s } = await getSummary()
    Object.assign(current, s)
    const { data: snaps } = await listSnapshots()
    snapshots.value = snaps || []
    if (snaps.length > 0) lastSnapshot.value = snaps[snaps.length - 1]
    await nextTick()
    if (displaySnapshots.value.length > 0) renderChart()
  } catch { /* empty */ }
}

async function takeSnap() {
  try {
    await takeSnapshot()
    ElMessage.success('快照已记录')
    await loadAll()
  } catch (e) { /* 409 handled by interceptor */ }
}

// ── 图表渲染 ──
function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const snaps = displaySnapshots.value
  const dates = snaps.map(d => d.snap_date)
  const values = snaps.map(d => d.net_worth)
  const isPrivate = privacyMode.value

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: isPrivate
        ? () => '***'
        : undefined,
    },
    grid: { left: 60, right: 30, top: 20, bottom: 30 },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
        formatter: isPrivate ? () => '***' : v => '¥' + (v / 10000).toFixed(0) + 'w',
      },
    },
    series: [{
      data: values, type: 'line', smooth: true,
      symbol: isPrivate ? 'none' : 'circle', symbolSize: 6,
      lineStyle: { color: '#6366f1', width: 2 },
      itemStyle: { color: '#6366f1' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(99,102,241,.15)' },
          { offset: 1, color: 'rgba(99,102,241,0)' },
        ]),
      },
    }],
  })
}

// ── 删除快照 ──
async function del(id) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteSnapshot(id); ElMessage.success('已删除'); await loadAll()
}

// ── 监听隐私模式 / 隐藏资产变化，自动重绘 ──
watch([privacyMode, hiddenAssets], () => {
  nextTick(() => {
    if (displaySnapshots.value.length > 0) renderChart()
  })
}, { deep: true })

onMounted(loadAll)
</script>
