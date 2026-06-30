import { ref } from 'vue'

const formats = ['raw', 'wan', 'k']
const STORAGE_KEY_PREFIX = 'wealthhome_unit_'

function getStorageKey() {
  const username = localStorage.getItem('username')
  return username ? `${STORAGE_KEY_PREFIX}${username}` : STORAGE_KEY_PREFIX + 'default'
}

function loadUnitIdx() {
  try {
    const saved = localStorage.getItem(getStorageKey())
    if (saved !== null) {
      const idx = parseInt(saved, 10)
      if (idx >= 0 && idx < formats.length) return idx
    }
  } catch {}
  return 0
}

function saveUnitIdx(idx) {
  localStorage.setItem(getStorageKey(), String(idx))
}

const currentIdx = ref(loadUnitIdx())

export function useAmountFormat() {
  function cycle() {
    currentIdx.value = (currentIdx.value + 1) % formats.length
    saveUnitIdx(currentIdx.value)
  }

  function format(value, html = false) {
    const v = Number(value) || 0
    switch (formats[currentIdx.value]) {
      case 'wan': {
        const num = (v / 10000).toFixed(v >= 10000 ? 1 : 2)
        if (html) return '¥' + '<span style="margin-left:1px;">' + num + '</span>' + '<span style="margin-left:3px;font-weight:900;">万</span>'
        return '¥\u2009' + num + '\uFEFF万'
      }
      case 'k': {
        const num = (v / 1000).toFixed(v >= 1000 ? 1 : 2)
        return '¥\u2009' + num + 'k'
      }
      default: return '¥\u2009' + v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
  }

  function label() {
    switch (formats[currentIdx.value]) {
      case 'wan': return '万'
      case 'k': return 'k'
      default: return '元'
    }
  }

  return { cycle, format, label }
}

// Global standalone (shared state for all pages)
export const cycleFormat = () => { currentIdx.value = (currentIdx.value + 1) % formats.length; saveUnitIdx(currentIdx.value) }
export const formatLabel = () => useAmountFormat().label()
export function formatAmount(value) {
  return useAmountFormat().format(value)
}
export function formatHtml(value) {
  return useAmountFormat().format(value, true)
}

// 返回不带 ¥ 前缀的纯数字（用于正负号场景如 ¥+xxx / ¥-xxx）
export function formatAmountNumber(value) {
  const v = Math.abs(Number(value) || 0)
  switch (formats[currentIdx.value]) {
    case 'wan': return (v / 10000).toFixed(v >= 10000 ? 1 : 2) + '万'
    case 'k': return (v / 1000).toFixed(v >= 1000 ? 1 : 2) + 'k'
    default: return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
}
