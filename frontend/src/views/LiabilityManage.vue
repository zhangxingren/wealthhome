<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>负债管理</h3>
      <el-button type="primary" @click="openAdd">+ 添加负债</el-button>
    </div>
    <div class="page-card-body">
      <el-table :data="list" v-loading="loading" empty-text="暂无负债">
        <el-table-column prop="name" label="名称" min-width="90" show-overflow-tooltip />
        <el-table-column prop="principal" label="本金" min-width="110">
          <template #default="{row}">{{ formatAmount(row.principal) }}</template>
        </el-table-column>
        <el-table-column prop="rate" label="年利率(%)" width="90" />
        <el-table-column prop="term_months" label="期限(月)" width="80" />
        <el-table-column prop="repay_type" label="还款方式" width="90" />
        <el-table-column prop="monthly_payment" label="月供" width="110">
          <template #default="{row}">{{ formatAmount(row.monthly_payment) }}</template>
        </el-table-column>
        <el-table-column prop="remaining" label="剩余本金" min-width="105">
          <template #default="{row}">{{ formatAmount(row.remaining) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="viewPlan(row)">还款计划</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="负债变化趋势" empty-text="暂无净值快照" />

    <el-dialog v-model="dialog" :title="editing ? '编辑负债' : '添加负债'" width="500px">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="16"><el-form-item label="名称"><el-input v-model="form.name" placeholder="如：房贷" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="本金"><el-input-number v-model="form.principal" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="年利率(%)"><el-input-number v-model="form.rate" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="期限(月)"><el-input-number v-model="form.term_months" :min="1" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="还款方式">
            <el-select v-model="form.repay_type" style="width:100%">
              <el-option label="等额本息" value="等额本息"/><el-option label="等额本金" value="等额本金"/>
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="起贷日期"><el-input v-model="form.start_date" type="date" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog=false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">{{ editing ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="planDialog" title="还款计划表" width="700px">
      <div v-if="planData">
        <p style="margin-bottom:12px; color:#64748b;">月供: ¥{{ planData.liability.monthly_payment }} | 总利息: ¥{{ planData.total_interest }}</p>
        <el-table :data="planData.plan" max-height="400" size="small">
          <el-table-column prop="期数" label="期数" width="60" />
          <el-table-column prop="还款日期" label="日期" width="110" />
          <el-table-column prop="月供" label="月供" width="100">
            <template #default="{row}">{{ formatAmount(row.月供) }}</template>
          </el-table-column>
          <el-table-column prop="本金" label="本金" width="100">
            <template #default="{row}">{{ formatAmount(row.本金) }}</template>
          </el-table-column>
          <el-table-column prop="利息" label="利息" width="100">
            <template #default="{row}">{{ formatAmount(row.利息) }}</template>
          </el-table-column>
          <el-table-column prop="剩余本金" label="剩余本金" width="130">
            <template #default="{row}">{{ formatAmount(row.剩余本金) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { listLiabilities, createLiability, updateLiability, deleteLiability, getRepayPlan, getAssetTrend } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatAmount } from '../composables/useAmountFormat'
import { useTimeRangeStore } from '../stores/timeRange'
import TrendChart from '../components/TrendChart.vue'

const list = ref([]); const loading = ref(false); const saving = ref(false)
const dialog = ref(false); const planDialog = ref(false)
const editing = ref(null); const planData = ref(null)
const trendData = ref([])
const timeStore = useTimeRangeStore()
const form = reactive({ name: '', principal: 0, rate: 0, term_months: 12, repay_type: '等额本息', start_date: '', note: '' })

async function load() { loading.value = true; try { const { data } = await listLiabilities(); list.value = data || [] } catch { list.value = [] } finally { loading.value = false } }
function openAdd() { editing.value = null; Object.assign(form, { name: '', principal: 0, rate: 0, term_months: 12, repay_type: '等额本息', start_date: '', note: '' }); dialog.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); dialog.value = true }
async function save() {
  if (!form.name || !form.start_date) return ElMessage.warning('名称和起贷日期必填')
  saving.value = true
  try { editing.value ? await updateLiability(editing.value, { ...form }) : await createLiability({ ...form }); ElMessage.success(editing.value ? '已更新' : '已添加'); dialog.value = false; await load() } finally { saving.value = false }
}
async function viewPlan(row) { const { data } = await getRepayPlan(row.id); planData.value = data; planDialog.value = true }
async function del(id) { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await deleteLiability(id); ElMessage.success('已删除'); await load() }
async function loadTrend() { try { const { data } = await getAssetTrend('total_liability', 30, timeStore.start, timeStore.end); trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 })) } catch { trendData.value = [] } }
// 时间范围变化时重新加载趋势
watch(() => [timeStore.start, timeStore.end], () => { loadTrend() })

onMounted(() => { load(); loadTrend() })
</script>
