<template>
  <div class="page-card">
    <div class="page-card-header">
      <h3>现金存款</h3>
      <el-button type="primary" @click="openAdd">+ 添加现金</el-button>
    </div>
    <div class="page-card-body">
      <el-table :data="list" v-loading="loading" empty-text="暂无现金资产">
        <el-table-column prop="name" label="名称" min-width="90" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" min-width="120">
          <template #default="{row}">{{ formatAmount(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="account_name" label="账户" min-width="100" show-overflow-tooltip />
        <el-table-column prop="currency" label="币种" width="65" />
        <el-table-column prop="note" label="备注" min-width="100" show-overflow-tooltip />
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TrendChart :data="trendData" title="现金净值变化趋势" empty-text="暂无净值快照" />

    <el-dialog v-model="dialog" :title="editing ? '编辑现金' : '添加现金'" width="480px">
      <el-form @submit.prevent="save" label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如：工资卡" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="账户"><el-input v-model="form.account_name" placeholder="如：工商银行" /></el-form-item>
        <el-form-item label="币种"><el-input v-model="form.currency" placeholder="CNY" /></el-form-item>
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
import { ref, reactive, onMounted, watch } from 'vue'
import { listCash, createCash, updateCash, deleteCash, getAssetTrend } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatAmount } from '../composables/useAmountFormat'
import { useTimeRangeStore } from '../stores/timeRange'
import TrendChart from '../components/TrendChart.vue'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const trendData = ref([])
const timeStore = useTimeRangeStore()

const form = reactive({ name: '', amount: 0, currency: 'CNY', account_name: '', note: '' })

async function load() {
  loading.value = true
  try { const { data } = await listCash(); list.value = data || [] }
  catch { list.value = [] }
  finally { loading.value = false }
}

function openAdd() { editing.value = null; Object.assign(form, { name: '', amount: 0, currency: 'CNY', account_name: '', note: '' }); dialog.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); dialog.value = true }

async function save() {
  if (!form.name) return ElMessage.warning('名称必填')
  saving.value = true
  try {
    editing.value ? await updateCash(editing.value, { ...form }) : await createCash({ ...form })
    ElMessage.success(editing.value ? '已更新' : '已添加')
    dialog.value = false
    await load()
  } finally { saving.value = false }
}

async function del(id) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteCash(id)
  ElMessage.success('已删除')
  await load()
}

async function loadTrend() {
  try { const { data } = await getAssetTrend('cash', 30, timeStore.start, timeStore.end); trendData.value = (data || []).map(d => ({ snap_date: d.snap_date, net_worth: d.value || 0 })) } catch { trendData.value = [] }
}

// 时间范围变化时重新加载趋势
watch(() => [timeStore.start, timeStore.end], () => { loadTrend() })

onMounted(() => { load(); loadTrend() })
</script>
