<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>定期存单</h3>
      <el-button type="primary" @click="openAdd">+ 添加存单</el-button>
    </div>
    <div class="page-card-body">
      <el-table :data="list" v-loading="loading" empty-text="暂无定期存单">
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="bank" label="银行" width="100" />
        <el-table-column label="本金" width="130">
          <template #default="{row}">{{ formatAmount(row.principal) }}</template>
        </el-table-column>
        <el-table-column prop="rate" label="年利率(%)" width="100" />
        <el-table-column label="已得利息" width="130">
          <template #default="{row}">
            <span class="interest-badge" @click="showInterest(row.id)">
              {{ row._interest ? formatAmount(row._interest.accrued_interest) : '点击查看' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="计息进度" width="110">
          <template #default="{row}">
            <el-progress v-if="row._interest" :percentage="row._interest.progress_pct" :stroke-width="6"
              :show-text="false" style="width:60px" />
            <span v-else style="color:#94a3b8; font-size:12px;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="起息日" width="110" />
        <el-table-column prop="end_date" label="到期日" width="110" />
        <el-table-column prop="note" label="备注" min-width="80" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="定期净值变化趋势" empty-text="暂无净值快照" />

    <el-dialog v-model="dialog" :title="editing ? '编辑存单' : '添加存单'" width="520px">
      <el-form @submit.prevent="save" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="银行"><el-input v-model="form.bank" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="本金"><el-input-number v-model="form.principal" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="年利率(%)"><el-input-number v-model="form.rate" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="起息日"><el-input v-model="form.start_date" type="date" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="到期日"><el-input v-model="form.end_date" type="date" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog=false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">{{ editing ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- Interest detail dialog -->
    <el-dialog v-model="interestDialog" title="利息详情" width="420px">
      <div v-if="interestData" class="interest-detail">
        <div class="id-row"><span>本金</span><strong>{{ formatAmount(interestData.principal) }}</strong></div>
        <div class="id-row"><span>年利率</span><strong>{{ interestData.rate_pct }}%</strong></div>
        <div class="id-row"><span>起息日</span><strong>{{ interestData.start_date }}</strong></div>
        <div class="id-row"><span>到期日</span><strong>{{ interestData.end_date }}</strong></div>
        <div class="id-row"><span>已计息天数</span><strong>{{ interestData.days_elapsed }} / {{ interestData.total_days }} 天</strong></div>
        <div class="id-row highlight"><span>已得利息</span><strong class="accrued">{{ formatAmount(interestData.accrued_interest) }}</strong></div>
        <div class="id-row"><span>到期总利息</span><strong>{{ formatAmount(interestData.total_interest) }}</strong></div>
        <el-progress :percentage="interestData.progress_pct" :stroke-width="8" style="margin-top:16px" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listDeposit, createDeposit, updateDeposit, deleteDeposit, getDepositInterest, getAssetTrend } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatAmount } from '../composables/useAmountFormat'
import TrendChart from '../components/TrendChart.vue'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const trendData = ref([])
const interestDialog = ref(false)
const interestData = ref(null)
const form = reactive({ name: '', bank: '', principal: 0, rate: 0, start_date: '', end_date: '', currency: 'CNY', note: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await listDeposit()
    list.value = data || []
    // Batch load interest
    for (const item of list.value) {
      try {
        const { data: ir } = await getDepositInterest(item.id)
        item._interest = ir
      } catch { item._interest = null }
    }
  } catch { list.value = [] }
  finally { loading.value = false }
}

async function showInterest(id) {
  try {
    const { data } = await getDepositInterest(id)
    interestData.value = data
    interestDialog.value = true
  } catch { ElMessage.warning('获取利息失败') }
}

function openAdd() { editing.value = null; Object.assign(form, { name: '', bank: '', principal: 0, rate: 0, start_date: '', end_date: '', currency: 'CNY', note: '' }); dialog.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); dialog.value = true }
async function save() {
  if (!form.name || !form.start_date) return ElMessage.warning('名称和起息日必填')
  saving.value = true
  try {
    editing.value ? await updateDeposit(editing.value, { ...form }) : await createDeposit({ ...form })
    ElMessage.success(editing.value ? '已更新' : '已添加')
    dialog.value = false; await load()
  } finally { saving.value = false }
}
async function del(id) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteDeposit(id); ElMessage.success('已删除'); await load()
}
async function loadTrend() {
  try { const { data } = await getAssetTrend('deposit', 30); trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 })) } catch { trendData.value = [] }
}

onMounted(() => { load(); loadTrend() })
</script>

<style scoped>
.interest-badge {
  color: #6366f1; cursor: pointer; font-variant-numeric: tabular-nums;
}
.interest-badge:hover { text-decoration: underline; }
.interest-detail { display: flex; flex-direction: column; gap: 10px; }
.id-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f1f5f9; }
.id-row span { color: #94a3b8; font-size: 13px; }
.id-row strong { font-variant-numeric: tabular-nums; }
.id-row.highlight { background: #f8f7ff; margin: 0 -12px; padding: 8px 12px; border-radius: 8px; }
.accrued { color: #10b981; font-size: 18px; }
</style>
