<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>贵金属资产</h3>
      <div style="display:flex;gap:8px;align-items:center;">
        <el-button type="default" size="small" @click="refreshPrices" :loading="refreshingPrices">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="14" height="14" style="margin-right:4px;"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          刷新报价
        </el-button>
        <el-button type="primary" @click="openAdd">+ 添加贵金属</el-button>
      </div>
    </div>

    <!-- 盈亏汇总卡片 -->
    <div class="pm-summary-cards" v-if="summary.total_cost > 0">
      <div class="pm-summary-item">
        <div class="pm-summary-label">总成本</div>
        <div class="pm-summary-value">¥{{ formatAmount(summary.total_cost) }}</div>
      </div>
      <div class="pm-summary-item">
        <div class="pm-summary-label">总市值</div>
        <div class="pm-summary-value">¥{{ formatAmount(summary.total_market_value) }}</div>
      </div>
      <div class="pm-summary-item" :class="{ profit: summary.total_profit >= 0, loss: summary.total_profit < 0 }">
        <div class="pm-summary-label">总盈亏</div>
        <div class="pm-summary-value">{{ summary.total_profit >= 0 ? '+' : '' }}¥{{ formatAmount(summary.total_profit) }}</div>
      </div>
      <div class="pm-summary-item" :class="{ profit: summary.total_profit >= 0, loss: summary.total_profit < 0 }">
        <div class="pm-summary-label">盈亏率</div>
        <div class="pm-summary-value">{{ summary.total_profit_pct >= 0 ? '+' : '' }}{{ summary.total_profit_pct.toFixed(2) }}%</div>
      </div>
    </div>

    <div class="page-card-body">
      <el-table :data="list" v-loading="loading" empty-text="暂无贵金属持仓">
        <el-table-column prop="name" label="名称" min-width="100" />
        <el-table-column label="类型" width="80">
          <template #default="{row}">
            <el-tag :type="typeTagColor(row.type)" size="small">{{ row.type_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="持有克数" width="110">
          <template #default="{row}">{{ row.weight_grams.toLocaleString() }} g</template>
        </el-table-column>
        <el-table-column label="买入单价" width="110">
          <template #default="{row}">¥{{ row.buy_price_per_gram.toFixed(2) }}/g</template>
        </el-table-column>
        <el-table-column label="买入总价" width="130">
          <template #default="{row}">¥{{ formatAmount(row.buy_total) }}</template>
        </el-table-column>
        <el-table-column label="当前市价" width="110">
          <template #default="{row}">
            <span v-if="row.current_price_per_gram">¥{{ row.current_price_per_gram.toFixed(2) }}/g</span>
            <span v-else class="text-muted">未获取</span>
          </template>
        </el-table-column>
        <el-table-column label="当前市值" width="130">
          <template #default="{row}">
            <span v-if="row.current_price_per_gram">¥{{ formatAmount(row.current_value) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="盈亏金额" width="130">
          <template #default="{row}">
            <span v-if="row.current_price_per_gram" :style="{color: row.profit >= 0 ? '#10b981' : '#ef4444'}">
              {{ row.profit >= 0 ? '+' : '' }}¥{{ formatAmount(row.profit) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="盈亏%" width="90">
          <template #default="{row}">
            <span v-if="row.current_price_per_gram" :style="{color: row.profit >= 0 ? '#10b981' : '#ef4444'}">
              {{ row.profit_pct >= 0 ? '+' : '' }}{{ row.profit_pct.toFixed(1) }}%
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="买入日期" width="110">
          <template #default="{row}">{{ row.buy_date }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="贵金属净值变化趋势" empty-text="暂无净值快照" />

    <el-dialog v-model="dialog" :title="editing ? '编辑贵金属' : '添加贵金属'" width="520px">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="14"><el-form-item label="名称"><el-input v-model="form.name" placeholder="如：工商银行金条、纸黄金" /></el-form-item></el-col>
          <el-col :span="10"><el-form-item label="类型">
            <el-select v-model="form.type" style="width:100%">
              <el-option label="黄金" value="gold" />
              <el-option label="白银" value="silver" />
              <el-option label="铂金" value="platinum" />
              <el-option label="钯金" value="palladium" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="持有克数"><el-input-number v-model="form.weight_grams" :min="0.01" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="买入单价(元/克)"><el-input-number v-model="form.buy_price_per_gram" :min="0.01" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="买入日期"><el-input v-model="form.buy_date" type="date" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="买入总价"><el-input-number v-model="form.buy_total" :min="0" :precision="2" style="width:100%" @focus="onBuyTotalInput" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="当前市价(元/克)"><el-input-number v-model="form.current_price_per_gram" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" placeholder="购买渠道、品牌等信息" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog=false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">{{ editing ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import {
  listPreciousMetals, createPreciousMetal, updatePreciousMetal, deletePreciousMetal,
  refreshPreciousMetalPrices, getPreciousMetalSummary, getAssetTrend,
} from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import TrendChart from '../components/TrendChart.vue'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const refreshingPrices = ref(false)
const dialog = ref(false)
const editing = ref(null)
const summary = reactive({ total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0, count: 0 })
const trendData = ref([])

const form = reactive({
  name: '', type: 'gold', weight_grams: 0, buy_price_per_gram: 0,
  buy_date: '', buy_total: 0, current_price_per_gram: 0, notes: '',
})

// 跟踪用户是否手动修改了买入总价，若是则不自动覆盖
const buyTotalManuallySet = ref(false)

// 当持有克数或买入单价变化时，自动计算买入总价（除非用户已手动设置）
watch(
  () => [form.weight_grams, form.buy_price_per_gram],
  () => {
    if (!buyTotalManuallySet.value && form.weight_grams > 0 && form.buy_price_per_gram > 0) {
      form.buy_total = +(form.weight_grams * form.buy_price_per_gram).toFixed(2)
    }
  }
)

// 监听买入总价输入框的 focus 事件 — 用户一旦修改则标记为手动设置
function onBuyTotalInput() {
  buyTotalManuallySet.value = true
}

function formatAmount(v) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function typeTagColor(type) {
  const map = { gold: 'warning', silver: 'info', platinum: '', palladium: 'danger' }
  return map[type] || ''
}

async function load() {
  loading.value = true
  try {
    const { data } = await getPreciousMetalSummary()
    list.value = data.items || []
    summary.total_cost = data.total_cost || 0
    summary.total_market_value = data.total_market_value || 0
    summary.total_profit = data.total_profit || 0
    summary.total_profit_pct = data.total_profit_pct || 0
    summary.count = data.count || 0
  } catch {
    list.value = []
    Object.assign(summary, { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0, count: 0 })
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editing.value = null
  buyTotalManuallySet.value = false
  const today = new Date().toISOString().slice(0, 10)
  Object.assign(form, {
    name: '', type: 'gold', weight_grams: 0, buy_price_per_gram: 0,
    buy_date: today, buy_total: 0, current_price_per_gram: 0, notes: '',
  })
  dialog.value = true
}

function openEdit(row) {
  editing.value = row.id
  buyTotalManuallySet.value = row.buy_total > 0
  Object.assign(form, {
    name: row.name, type: row.type, weight_grams: row.weight_grams,
    buy_price_per_gram: row.buy_price_per_gram, buy_date: row.buy_date,
    buy_total: row.buy_total, current_price_per_gram: row.current_price_per_gram,
    notes: row.notes,
  })
  dialog.value = true
}

async function save() {
  if (!form.name || form.weight_grams <= 0 || form.buy_price_per_gram <= 0 || !form.buy_date) {
    return ElMessage.warning('名称、克数、买入单价和买入日期必填')
  }
  saving.value = true
  try {
    if (editing.value) {
      await updatePreciousMetal(editing.value, { ...form })
      ElMessage.success('已更新')
    } else {
      await createPreciousMetal({ ...form })
      ElMessage.success('已添加')
    }
    dialog.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function del(id) {
  await ElMessageBox.confirm('确定删除该贵金属资产？', '提示', { type: 'warning' })
  await deletePreciousMetal(id)
  ElMessage.success('已删除')
  await load()
}

async function refreshPrices() {
  refreshingPrices.value = true
  try {
    const { data } = await refreshPreciousMetalPrices()
    ElMessage.success(data?.message || '报价已刷新')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '刷新失败')
  } finally {
    refreshingPrices.value = false
  }
}

onMounted(() => { load(); loadTrend() })

async function loadTrend() {
  try { const { data } = await getAssetTrend('precious_metal', 30); trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 })) } catch { trendData.value = [] }
}
</script>

<style scoped>
.pm-summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--md-surface-container-low);
  border-radius: var(--radius-xl);
  border: 1px solid var(--md-outline-variant);
}

.pm-summary-item {
  text-align: center;
  padding: 8px;
}

.pm-summary-label {
  font-size: 12px;
  color: var(--c-text-tertiary);
  margin-bottom: 4px;
}

.pm-summary-value {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: var(--c-text);
}

.pm-summary-item.profit .pm-summary-value {
  color: #10b981;
}

.pm-summary-item.loss .pm-summary-value {
  color: #ef4444;
}

.text-muted {
  color: var(--c-text-tertiary);
  font-size: 13px;
}
</style>