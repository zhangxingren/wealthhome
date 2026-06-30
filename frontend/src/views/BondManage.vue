<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>债券债权</h3>
      <el-button type="primary" @click="openAdd">+ 添加债券</el-button>
    </div>

    <!-- 盈亏汇总卡片 -->
    <div class="pm-summary-cards" v-if="bondSummary.total_cost > 0">
      <div class="pm-summary-item">
        <div class="pm-summary-label">总成本</div>
        <div class="pm-summary-value">{{ formatAmount(bondSummary.total_cost) }}</div>
      </div>
      <div class="pm-summary-item">
        <div class="pm-summary-label">总市值</div>
        <div class="pm-summary-value">{{ formatAmount(bondSummary.total_market_value) }}</div>
      </div>
      <div class="pm-summary-item" :class="{ profit: bondSummary.total_profit >= 0, loss: bondSummary.total_profit < 0 }">
        <div class="pm-summary-label">总盈亏</div>
        <div class="pm-summary-value">{{ bondSummary.total_profit >= 0 ? formatAmount(bondSummary.total_profit) : '¥-' + formatAmountNumber(Math.abs(bondSummary.total_profit)) }}</div>
      </div>
      <div class="pm-summary-item" :class="{ profit: bondSummary.total_profit >= 0, loss: bondSummary.total_profit < 0 }">
        <div class="pm-summary-label">盈亏率</div>
        <div class="pm-summary-value">{{ bondSummary.total_profit_pct >= 0 ? '+' : '' }}{{ bondSummary.total_profit_pct.toFixed(2) }}%</div>
      </div>
    </div>

    <div class="page-card-body">
      <el-table :data="list" v-loading="loading" empty-text="暂无债券">
        <el-table-column prop="code" label="代码" width="75" />
        <el-table-column prop="name" label="名称" min-width="90" show-overflow-tooltip />
        <el-table-column prop="issuer" label="发行方" min-width="85" show-overflow-tooltip />
        <el-table-column label="面值" width="80">
          <template #default="{row}">{{ formatAmount(row.face_value) }}</template>
        </el-table-column>
        <el-table-column label="票面利率" width="78">
          <template #default="{row}">{{ row.rate }}%</template>
        </el-table-column>
        <el-table-column label="数量" width="60">
          <template #default="{row}">{{ row.quantity || 1 }}</template>
        </el-table-column>
        <el-table-column label="成本单价" width="80">
          <template #default="{row}">{{ formatAmount(row.cost_price || row.face_value) }}</template>
        </el-table-column>
        <el-table-column label="投入成本" min-width="95">
          <template #default="{row}">{{ formatAmount((row.quantity || 1) * (row.cost_price || row.face_value)) }}</template>
        </el-table-column>
        <el-table-column label="当前市价" min-width="80">
          <template #default="{row}">
            <span v-if="row.current_price">{{ formatAmount(row.current_price) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="市值" min-width="95">
          <template #default="{row}">
            <span v-if="row.current_price">{{ formatAmount((row.quantity || 1) * row.current_price) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="盈亏金额" min-width="110">
          <template #default="{row}">
            <span v-if="row.current_price" :style="{color: row._pnl >= 0 ? '#10b981' : '#ef4444'}" class="font-mono">
              {{ row._pnl >= 0 ? formatAmount(row._pnl) : '¥-' + formatAmountNumber(Math.abs(row._pnl)) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="盈亏%" width="75">
          <template #default="{row}">
            <span v-if="row.current_price && row._pnl_pct !== null" :style="{color: row._pnl >= 0 ? '#10b981' : '#ef4444'}">
              {{ row._pnl_pct >= 0 ? '+' : '' }}{{ row._pnl_pct.toFixed(1) }}%
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="maturity_date" label="到期日" width="100" />
        <el-table-column prop="type" label="类型" width="65" />
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="债券净值变化趋势" empty-text="暂无净值快照" />

    <el-dialog v-model="dialog" :title="editing ? '编辑债券' : '添加债券'" width="520px">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="发行方"><el-input v-model="form.issuer" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="面值"><el-input-number v-model="form.face_value" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="票面利率(%)"><el-input-number v-model="form.rate" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="数量"><el-input-number v-model="form.quantity" :min="1" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="成本单价"><el-input-number v-model="form.cost_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="当前市价"><el-input-number v-model="form.current_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="到期日"><el-input v-model="form.maturity_date" type="date" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
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
import { listBond, createBond, updateBond, deleteBond, getAssetTrend } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatAmount, formatAmountNumber } from '../composables/useAmountFormat'
import { useTimeRangeStore } from '../stores/timeRange'
import TrendChart from '../components/TrendChart.vue'

const list = ref([]); const loading = ref(false); const saving = ref(false); const dialog = ref(false); const editing = ref(null)
const trendData = ref([])
const timeStore = useTimeRangeStore()
const form = reactive({ name: '', issuer: '', face_value: 0, rate: 0, quantity: 1, cost_price: 0, current_price: 0, maturity_date: '', currency: 'CNY', note: '' })

const bondSummary = computed(() => {
  const items = list.value || []
  let total_cost = 0, total_market_value = 0
  for (const b of items) {
    const qty = b.quantity || 1
    const cp = b.cost_price || b.face_value || 0
    const curp = b.current_price || b.cost_price || b.face_value || 0
    total_cost += qty * cp
    total_market_value += qty * curp
  }
  const total_profit = total_market_value - total_cost
  const total_profit_pct = total_cost > 0 ? (total_profit / total_cost * 100) : 0
  return { total_cost, total_market_value, total_profit, total_profit_pct }
})

async function load() {
  loading.value = true
  try {
    const { data } = await listBond()
    list.value = (data || []).map(row => {
      const cost = row.cost_price || row.face_value || 0
      const qty = row.quantity || 1
      row._pnl = row.current_price ? (row.current_price - cost) * qty : null
      row._pnl_pct = row.current_price && cost > 0 ? ((row.current_price - cost) / cost * 100) : null
      return row
    })
  } catch { list.value = [] }
  finally { loading.value = false }
}
function openAdd() { editing.value = null; Object.assign(form, { name: '', issuer: '', face_value: 0, rate: 0, quantity: 1, cost_price: 0, current_price: 0, maturity_date: '', currency: 'CNY', note: '' }); dialog.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); dialog.value = true }
async function save() {
  if (!form.name || !form.maturity_date) return ElMessage.warning('名称和到期日必填')
  saving.value = true
  try { editing.value ? await updateBond(editing.value, { ...form }) : await createBond({ ...form }); ElMessage.success(editing.value ? '已更新' : '已添加'); dialog.value = false; await load() } finally { saving.value = false }
}
async function del(id) { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await deleteBond(id); ElMessage.success('已删除'); await load() }
async function loadTrend() { try { const { data } = await getAssetTrend('bond', 30, timeStore.start, timeStore.end); trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 })) } catch { trendData.value = [] } }
// 时间范围变化时重新加载趋势
watch(() => [timeStore.start, timeStore.end], () => { loadTrend() })

onMounted(() => { load(); loadTrend() })
</script>

