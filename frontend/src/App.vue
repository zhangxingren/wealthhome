<template>
  <router-view v-if="isLoginPage" />
  <div v-else class="app-layout">
    <!-- === MD3 可折叠侧边栏 === -->
    <aside class="app-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-logo">
        <span class="nav-icon" style="transform:scale(1.2);margin-left:-2px;margin-right:6px;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="4"/><line x1="12" y1="9" x2="12" y2="15"/><line x1="9" y1="12" x2="15" y2="12"/></svg>
        </span>
        <span class="logo-text">Wealth<span class="logo-accent">Home</span></span>
      </div>

      <nav class="sidebar-nav">

        <!-- 概览 -->
        <div class="nav-group">
          <router-link to="/" class="nav-item" exact-active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            </span>
            <span>仪表盘</span>
          </router-link>
        </div>

        <div class="nav-divider"></div>

        <!-- 资产管理 -->
        <div class="nav-group">
          <div class="nav-label">资产管理</div>
          <router-link to="/cash" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M9 12h6"/><path d="M12 9v6"/></svg>
            </span>
            <span>现金存款</span>
          </router-link>
          <router-link to="/deposit" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
            </span>
            <span>定期存单</span>
          </router-link>
          <router-link to="/fund" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
            </span>
            <span>基金投资</span>
          </router-link>
          <router-link to="/stock" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3v18h18"/><polyline points="19 9 13.5 14.5 9 10 3 16"/></svg>
            </span>
            <span>股票持仓</span>
          </router-link>
          <router-link to="/bond" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
            <span>债券债权</span>
          </router-link>
          <router-link to="/precious-metal" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="1" y="6" width="22" height="12" rx="2"/><line x1="6" y1="12" x2="18" y2="12"/><line x1="12" y1="8" x2="12" y2="16"/></svg>
            </span>
            <span>贵金属</span>
          </router-link>
        </div>

        <div class="nav-divider"></div>

        <!-- 更多 -->
        <div class="nav-group">
          <div class="nav-label">更多</div>
          <router-link to="/liability" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="5" y1="8" x2="9" y2="8"/><line x1="5" y1="12" x2="13" y2="12"/></svg>
            </span>
            <span>负债管理</span>
          </router-link>
          <router-link to="/networth" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            </span>
            <span>净值趋势</span>
          </router-link>
          <router-link to="/family" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </span>
            <span>家庭管理</span>
          </router-link>
          <router-link to="/export" class="nav-item" active-class="active">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </span>
            <span>数据导出</span>
          </router-link>
        </div>
      </nav>

      <!-- 底部：折叠按钮 + 退出 -->
      <div class="sidebar-footer">
        <div class="sidebar-footer-row">
          <button class="sidebar-collapse-btn" @click="toggleSidebar" :title="sidebarCollapsed ? '展开导航' : '收起导航'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
          <button class="sidebar-save-btn" @click="handleSaveSettings" title="保存设置">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            <span class="save-btn-text">保存设置</span>
          </button>
        </div>
        <button class="logout-btn" @click="logout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          <span class="logout-btn-text">退出账号</span>
        </button>
      </div>
    </aside>

    <!-- === 主区域 === -->
    <div class="app-main">
      <header class="app-header">
        <div class="app-header-left">
          <h2>{{ pageTitle }}</h2>
          <div class="unit-toggle" @click="cycleFormat" title="点击切换金额单位">
            <span class="unit-toggle-option" :class="{ active: unitLabel === '元' }">元</span>
            <span class="unit-toggle-option" :class="{ active: unitLabel === '万' }">万</span>
            <span class="unit-toggle-option" :class="{ active: unitLabel === 'k' }">k</span>
          </div>
          <div class="privacy-toggle" :class="{ active: privacyMode }" @click="togglePrivacy" :title="privacyMode ? '关闭隐私模式' : '开启隐私模式'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="privacyMode">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
              </template>
              <template v-else>
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </template>
            </svg>
          </div>
        </div>
        <div class="header-right">
          <div class="account-display-name" :class="{ 'edit-mode': editingName }" @click="startEditName">
            <template v-if="editingName">
              <input ref="nameInput" v-model="nameValue" @blur="saveName" @keydown.enter="saveName" @keydown.escape="cancelEdit" />
              <span class="editing-hint">⏎ 保存</span>
            </template>
            <template v-else>
              <span>{{ displayName }}</span>
              <svg class="edit-pencil" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
            </template>
          </div>
          <button class="mobile-save-btn" :class="{ saving }" @click="handleSaveSettings" title="保存设置">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
          </button>
          <button class="mobile-logout-btn" @click="logout" title="退出登录">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </header>
      <div class="app-content">
        <router-view />
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProfile, updateProfile } from './api'
import { cycleFormat, formatLabel } from './composables/useAmountFormat'
import { usePrivacy } from './composables/usePrivacy'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isLoginPage = computed(() => route.path === '/login')
const username = computed(() => localStorage.getItem('username') || '用户')

const displayName = ref(localStorage.getItem('displayName') || username.value)
const editingName = ref(false)
const nameValue = ref(displayName.value)
const nameInput = ref(null)

// ── 侧边栏折叠状态持久化（按用户）──
function getSidebarKey() {
  return `wealthhome_sidebar_${localStorage.getItem('username') || 'default'}`
}
const sidebarCollapsed = ref(localStorage.getItem(getSidebarKey()) === 'true')

const unitLabel = computed(() => formatLabel())
const { privacyMode, togglePrivacy, saveSettings, resetPrivacy } = usePrivacy()

const titles = {
  '/': '仪表盘', '/cash': '现金存款', '/deposit': '定期存单',
  '/fund': '基金投资', '/stock': '股票持仓', '/bond': '债券债权',
  '/precious-metal': '贵金属资产',
  '/liability': '负债管理', '/networth': '净值趋势', '/family': '家庭管理', '/export': '数据导出',
}
const pageTitle = computed(() => titles[route.path] || '')

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem(getSidebarKey(), String(sidebarCollapsed.value))
}

async function loadProfile() {
  try {
    const { data } = await getProfile()
    if (data.display_name) {
      displayName.value = data.display_name
      localStorage.setItem('displayName', data.display_name)
    }
  } catch {}
}

async function startEditName() {
  if (editingName.value) return
  editingName.value = true
  nameValue.value = displayName.value
  await nextTick()
  nameInput.value?.focus()
  nameInput.value?.select()
}

async function saveName() {
  const trimmed = nameValue.value.trim()
  if (!trimmed) { editingName.value = false; return }
  try {
    await updateProfile({ display_name: trimmed })
    displayName.value = trimmed
    localStorage.setItem('displayName', trimmed)
    ElMessage.success('名称已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
  editingName.value = false
}

function cancelEdit() {
  editingName.value = false
}

function logout() {
  localStorage.clear()
  router.push('/login')
}

const saving = ref(false)
async function handleSaveSettings() {
  if (saving.value) return
  saving.value = true
  const ok = await saveSettings()
  if (ok) {
    ElMessage.success('设置已保存')
  } else {
    ElMessage.error('保存失败，请稍后重试')
  }
  saving.value = false
}

// 每次从登录页切回主界面时，重新从后端拉取用户信息（解决切换账号后用户名不更新问题）
watch(isLoginPage, (now) => {
  if (!now) {
    // 从登录页切回：先重置 displayName 为 localStorage 中的 username，再异步从 API 拉最新 profile
    resetPrivacy()
    displayName.value = localStorage.getItem('displayName') || localStorage.getItem('username') || '用户'
    loadProfile()
  }
})

onMounted(loadProfile)
</script>
