<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>{{ cfg.pageTitle }}</h3>
      <div style="display:flex;gap:8px;align-items:center;">
        <el-button type="default" size="small" @click="apiKeyDialog = true" :title="cfg.apiDialogTitle">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="14" height="14" style="margin-right:4px;"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          API
        </el-button>
        <el-button type="default" size="small" @click="refreshPrices" :loading="refreshingPrices">刷新报价</el-button>
        <el-button type="primary" @click="openAdd">+ 添加{{ cfg.apiLabel }}</el-button>
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
      <el-table :data="list" v-loading="loading" empty-text="暂无{{ cfg.apiLabel }}持仓">
        <el-table-column v-for="col in cfg.columns" :key="col.prop" :prop="col.prop" :label="col.label" :width="col.width" :min-width="col.minWidth">
          <template v-if="col.slot" #default="{row}">
            <span v-if="col.slot === 'market_value'" :style="col.style ? col.style(row) : {}">¥{{ (row[cfg.quantityField] * row[cfg.currentField]).toLocaleString() }}</span>
            <span v-else-if="col.slot === 'pnl'" :style="{color: (computePnl(row) >= 0 ? '#10b981' : '#ef4444')}">
              {{ computePnlPct(row).toFixed(1) }}%
            </span>
            <el-tag v-else-if="col.slot === 'market'" size="small">{{ row.market.toUpperCase() }}</el-tag>
            <el-tag v-else-if="col.slot === 'fund_type'" size="small">{{ row.fund_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="净值变化趋势" :empty-text="'暂无净值快照<br/><span style=\'font-size:12px;\'>去「净值趋势」页面记录</span>'" />

    <!-- API Key / 行情来源对话框 -->
    <el-dialog v-model="apiKeyDialog" :title="cfg.apiDialogTitle" width="460px">
      <el-form label-position="top">
        <el-form-item v-if="cfg.apiKeyNeeded" :label="cfg.apiKeyLabel">
          <el-input v-model="apiKey" :placeholder="cfg.apiKeyPlaceholder" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <div style="font-size:12px;color:var(--c-text-tertiary);line-height:1.6;">
            {{ cfg.apiDescription }}
            <a v-if="cfg.apiProviderUrl" :href="cfg.apiProviderUrl" target="_blank" style="color:var(--md-primary);">{{ cfg.apiProviderUrl }}</a>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiKeyDialog = false">取消</el-button>
        <el-button v-if="cfg.apiKeyNeeded" type="primary" @click="saveApiKey" :loading="savingKey">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialog" :title="editing ? '编辑' + cfg.apiLabel : '添加' + cfg.apiLabel" width="500px">
      <el-form label-position="top">
        <component :is="'div'" v-for="row in cfg.formRows" :key="row.map(f=>f.prop).join()">
          <el-row :gutter="16">
            <el-col v-for="f in row" :key="f.prop" :span="f.span">
              <el-form-item :label="f.label">
                <el-input v-if="f.type === 'text'" v-model="form[f.prop]" />
                <el-input-number v-else-if="f.type === 'number'" v-model="form[f.prop]" :min="f.min ?? 0" :precision="f.precision ?? 0" style="width:100%" />
                <el-select v-else-if="f.type === 'select'" v-model="form[f.prop]" style="width:100%">
                  <el-option v-for="opt in f.options" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </component>
      </el-form>
      <template #footer>
        <el-button @click="dialog=false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">{{ editing ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import TrendChart from './TrendChart.vue'

const props = defineProps({
  config: { type: Object, required: true }
})

const cfg = props.config

// ---------- state ----------
const list = ref([]); const loading = ref(false); const saving = ref(false); const dialog = ref(false); const editing = ref(null)
const apiKeyDialog = ref(false); const apiKey = ref('')
const savingKey = ref(false); const refreshingPrices = ref(false)
const trendData = ref([])

const form = reactive({ ...cfg.defaultForm })

// ---------- computed ----------
function formatAmount(v) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function computePnl(row) {
  return (row[cfg.currentField] - row[cfg.costField]) * (row[cfg.quantityField] || 0)
}

function computePnlPct(row) {
  const cost = row[cfg.costField] || 0
  if (cost === 0) return 0
  return (row[cfg.currentField] - cost) / cost * 100
}

const summary = computed(() => {
  const items = list.value || []
  let total_cost = 0, total_market_value = 0
  for (const s of items) {
    total_cost += (s[cfg.costField] || 0) * (s[cfg.quantityField] || 0)
    total_market_value += (s[cfg.currentField] || 0) * (s[cfg.quantityField] || 0)
  }
  const total_profit = total_market_value - total_cost
  const total_profit_pct = total_cost > 0 ? (total_profit / total_cost * 100) : 0
  return { total_cost, total_market_value, total_profit, total_profit_pct }
})

// ---------- data ----------
async function load() {
  loading.value = true
  try { const { data } = await cfg.api.list(); list.value = data || [] }
  catch { list.value = [] }
  finally { loading.value = false }
}

async function loadTrend() {
  try {
    const { data } = await cfg.api.getTrend(cfg.trendType, 30)
    trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 }))
  } catch (e) { console.error(`[${cfg.assetType}] 趋势加载失败:`, e); trendData.value = [] }
}

// ---------- CRUD ----------
function openAdd() {
  editing.value = null
  Object.assign(form, cfg.defaultForm)
  dialog.value = true
}

function openEdit(row) {
  editing.value = row.id
  Object.assign(form, row)
  dialog.value = true
}

async function save() {
  if (!form.code || !form.name) return ElMessage.warning('代码和名称必填')
  saving.value = true
  try {
    editing.value ? await cfg.api.update(editing.value, { ...form }) : await cfg.api.create({ ...form })
    ElMessage.success(editing.value ? '已更新' : '已添加')
    dialog.value = false
    await load()
  } finally { saving.value = false }
}

async function del(id) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await cfg.api.delete(id)
  ElMessage.success('已删除')
  await load()
}

// ---------- API Key ----------
async function initApiKey() {
  if (!cfg.apiKeyNeeded) return
  try {
    const { data } = await cfg.api.getUserSettings()
    if (data?.[cfg.settingKey]) {
      apiKey.value = data[cfg.settingKey]
      localStorage.setItem(cfg.storageKey, data[cfg.settingKey])
      return
    }
  } catch {}
  apiKey.value = localStorage.getItem(cfg.storageKey) || ''
}

async function saveApiKey() {
  savingKey.value = true
  try {
    localStorage.setItem(cfg.storageKey, apiKey.value)
    await cfg.api.putUserSetting(cfg.settingKey, apiKey.value)
    ElMessage.success('API Key 已保存')
    apiKeyDialog.value = false
  } catch {
    ElMessage.warning('API Key 仅保存在本地浏览器')
  } finally { savingKey.value = false }
}

async function refreshPrices() {
  if (cfg.apiKeyNeeded && !apiKey.value) return ElMessage.warning('请先设置 ' + cfg.apiKeyLabel)
  refreshingPrices.value = true
  try {
    const args = cfg.apiKeyNeeded ? [apiKey.value] : []
    const { data } = await cfg.api.refreshPrices(...args)
    ElMessage.success(data?.message || '报价已刷新')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '刷新失败')
  } finally { refreshingPrices.value = false }
}

onMounted(() => { initApiKey(); load(); loadTrend() })
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
</style>
