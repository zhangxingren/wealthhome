import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTimeRangeStore = defineStore('timeRange', () => {
  const preset = ref('all') // 'all' | '1w' | '1m' | '3m' | '6m' | '1y' | 'custom'
  const customStart = ref(null)
  const customEnd = ref(null)

  const PRESET_DAYS = { '1w': 7, '1m': 30, '3m': 90, '6m': 180, '1y': 365 }

  function fmtDate(d) {
    if (d instanceof Date && !isNaN(d)) return d.toISOString().slice(0, 10)
    // 如果已经是字符串（"YYYY-MM-DD"），直接返回
    if (typeof d === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(d)) return d
    return null
  }

  const start = computed(() => {
    if (preset.value === 'all') return null
    if (preset.value === 'custom') return fmtDate(customStart.value)
    const days = PRESET_DAYS[preset.value] || 30
    const d = new Date()
    d.setDate(d.getDate() - days)
    return fmtDate(d)
  })

  const end = computed(() => {
    if (preset.value === 'all') return null
    if (preset.value === 'custom') return fmtDate(customEnd.value)
    return fmtDate(new Date())
  })

  const label = computed(() => {
    const map = { 'all': '全部', '1w': '近一周', '1m': '近一月', '3m': '近三月', '6m': '近半年', '1y': '近一年', 'custom': '自定义' }
    return map[preset.value] || '全部'
  })

  function setPreset(p) {
    preset.value = p
    console.log('[timeRange] setPreset called:', p, 'start=', start.value, 'end=', end.value)
  }

  function setCustom(s, e) {
    preset.value = 'custom'
    customStart.value = s
    customEnd.value = e
  }

  function reset() {
    preset.value = 'all'
    customStart.value = null
    customEnd.value = null
  }

  return { preset, customStart, customEnd, start, end, label, setPreset, setCustom, reset }
})
