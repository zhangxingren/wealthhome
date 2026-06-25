import { ref, watch } from 'vue'
import { getUserSettings, putUserSetting } from '../api'

const STORAGE_KEY = 'wealthhome_privacy'

// ── localStorage fallback ──
function loadLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { privacyMode: false, hiddenAssets: [], familyHiddenAssets: {} }
}

function saveLocal(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

// ── 从后端拉取（优先），失败则退回 localStorage ──
async function loadRemote() {
  try {
    const res = await getUserSettings()
    const data = res.data || {}
    const ps = data.privacy_settings || {}
    return {
      privacyMode: ps.privacy || false,
      hiddenAssets: ps.hiddenAssets || [],
      familyHiddenAssets: ps.familyHiddenAssets || {},
    }
  } catch (e) {
    console.error('隐私设置加载失败，回退本地:', e)
    return loadLocal()
  }
}

// ── 全量保存到后端 + localStorage ──
let _savePending = null
async function saveRemote(state) {
  saveLocal({
    privacyMode: state.privacy,
    hiddenAssets: state.hiddenAssets,
    familyHiddenAssets: state.familyHiddenAssets,
  })

  if (_savePending) clearTimeout(_savePending)
  _savePending = setTimeout(async () => {
    try {
      await putUserSetting('privacy_settings', {
        privacy: state.privacy,
        hiddenAssets: state.hiddenAssets,
        familyHiddenAssets: state.familyHiddenAssets,
      })
    } catch {}
  }, 300)
}

// ── 全局共享状态 ──
const localFallback = loadLocal()
const privacyMode = ref(localFallback.privacyMode)
const hiddenAssets = ref(localFallback.hiddenAssets || [])
const familyHiddenAssets = ref(localFallback.familyHiddenAssets || {})
const remoteLoaded = ref(false)

// 启动时从后端同步
let initPromise = null
function ensureRemoteLoaded() {
  if (!initPromise) {
    initPromise = loadRemote().then((s) => {
      privacyMode.value = s.privacyMode
      hiddenAssets.value = s.hiddenAssets
      familyHiddenAssets.value = s.familyHiddenAssets
      remoteLoaded.value = true
    })
  }
  return initPromise
}
ensureRemoteLoaded()

// 持久化（后端 + localStorage）
watch(
  [privacyMode, hiddenAssets, familyHiddenAssets],
  () => {
    if (!remoteLoaded.value) return
    saveRemote({
      privacy: privacyMode.value,
      hiddenAssets: [...hiddenAssets.value],
      familyHiddenAssets: { ...familyHiddenAssets.value },
    })
  },
  { deep: true }
)

export function usePrivacy() {
  // 即时保存到后端（无 debounce），用于"保存设置"按钮
  async function saveSettings() {
    try {
      await putUserSetting('privacy_settings', {
        privacy: privacyMode.value,
        hiddenAssets: [...hiddenAssets.value],
        familyHiddenAssets: { ...familyHiddenAssets.value },
      })
      return true
    } catch {
      return false
    }
  }

  function togglePrivacy() {
    privacyMode.value = !privacyMode.value
  }

  // ── 个人（我的资产）隐藏 ──
  function toggleAssetVisibility(category) {
    const idx = hiddenAssets.value.indexOf(category)
    if (idx >= 0) {
      hiddenAssets.value.splice(idx, 1)
    } else {
      hiddenAssets.value.push(category)
    }
  }

  function isHidden(category) {
    return hiddenAssets.value.includes(category)
  }

  // ── 家庭汇总隐藏（按成员+类别） ──
  function getFamilyHidden(memberId) {
    return familyHiddenAssets.value[String(memberId)] || []
  }

  function toggleFamilyHidden(memberId, category) {
    const key = String(memberId)
    if (!familyHiddenAssets.value[key]) {
      familyHiddenAssets.value[key] = []
    }
    const arr = familyHiddenAssets.value[key]
    const idx = arr.indexOf(category)
    if (idx >= 0) {
      arr.splice(idx, 1)
    } else {
      arr.push(category)
    }
    familyHiddenAssets.value = { ...familyHiddenAssets.value }
  }

  function isFamilyHidden(memberId, category) {
    return (familyHiddenAssets.value[String(memberId)] || []).includes(category)
  }

  function formatPrivacy(formattedValue) {
    if (privacyMode.value) return '***'
    return formattedValue
  }

  return {
    privacyMode,
    hiddenAssets,
    familyHiddenAssets,
    saveSettings,
    togglePrivacy,
    toggleAssetVisibility,
    isHidden,
    getFamilyHidden,
    toggleFamilyHidden,
    isFamilyHidden,
    formatPrivacy,
  }
}
