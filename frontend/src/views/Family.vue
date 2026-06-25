<template>
  <div class="page-card">
    <div class="page-card-header"><h3>家庭管理</h3></div>
    <div class="page-card-body">
      <div v-if="family" style="margin-bottom:24px;">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
          <div style="width:48px; height:48px; border-radius:12px; background:linear-gradient(135deg,#6366f1,#4f46e5); display:flex; align-items:center; justify-content:center; color:#fff; font-size:20px;">🏠</div>
          <div>
            <div style="font-size:16px; font-weight:600;">{{ family.family.name }}</div>
            <div style="font-size:13px; color:#94a3b8;">邀请码: <code style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-weight:600; letter-spacing:1px;">{{ family.family.invite_code }}</code></div>
          </div>
        </div>

        <h4 style="font-size:14px; margin-bottom:12px; color:#64748b;">家庭成员</h4>
        <el-table :data="family.members" size="small">
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{row}"><el-tag size="small" :type="row.role==='admin'?'primary':''">{{ row.role === 'admin' ? '管理员' : '成员' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="加入时间" />
        </el-table>
      </div>

      <div v-else class="empty-state" style="padding:32px;">
        <div class="icon">👨‍👩‍👧</div>
        <p>你还没有家庭？注册即自动创建家庭</p>
      </div>

      <el-divider />
      <h4 style="font-size:14px; margin-bottom:12px; color:#64748b;">加入其他家庭</h4>
      <div style="display:flex; gap:8px; max-width:400px;">
        <el-input v-model="inviteCode" placeholder="输入邀请码" style="flex:1" />
        <el-button type="primary" @click="join" :loading="joining">加入</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFamily, joinFamily } from '../api'
import { ElMessage } from 'element-plus'

const family = ref(null)
const inviteCode = ref('')
const joining = ref(false)

async function load() {
  try { const { data } = await getFamily(); family.value = data } catch { family.value = null }
}

async function join() {
  if (!inviteCode.value.trim()) return ElMessage.warning('请输入邀请码')
  joining.value = true
  try {
    const { data } = await joinFamily(inviteCode.value.trim())
    ElMessage.success(data.message)
    inviteCode.value = ''
    await load()
  } finally { joining.value = false }
}

onMounted(load)
</script>
