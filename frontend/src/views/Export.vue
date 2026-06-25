<template>
  <div class="export-page">
    <div class="export-header">
      <h3>数据导出</h3>
      <p class="export-desc">选择导出格式和数据类型，下载您的资产与负债数据。</p>
    </div>

    <div class="export-cards">
      <!-- Excel -->
      <div class="export-card" :class="{ active: format === 'excel' }" @click="format = 'excel'">
        <div class="card-icon excel-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="8" y1="13" x2="16" y2="13"/>
            <line x1="8" y1="17" x2="16" y2="17"/>
          </svg>
        </div>
        <div class="card-label">Excel 格式</div>
        <div class="card-desc">分类分 Sheet，带样式表头</div>
        <div class="card-check" v-if="format === 'excel'">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </div>
      </div>

      <!-- CSV -->
      <div class="export-card" :class="{ active: format === 'csv' }" @click="format = 'csv'">
        <div class="card-icon csv-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="8" y1="13" x2="16" y2="13"/>
            <line x1="8" y1="17" x2="12" y2="17"/>
          </svg>
        </div>
        <div class="card-label">CSV 格式</div>
        <div class="card-desc">通用表格，Excel / 记事本都能打开</div>
        <div class="card-check" v-if="format === 'csv'">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </div>
      </div>
    </div>

    <!-- 数据类型选择 -->
    <div class="export-section">
      <div class="section-label">选择数据</div>
      <div class="category-tags">
        <label
          v-for="cat in allCategories"
          :key="cat.key"
          class="category-tag"
          :class="{ checked: selectedCats.has(cat.key) }"
        >
          <input
            type="checkbox"
            :checked="selectedCats.has(cat.key)"
            @change="toggleCat(cat.key)"
            class="tag-checkbox"
          />
          <span class="tag-dot" :style="{ background: cat.color }"></span>
          <span class="tag-name">{{ cat.label }}</span>
        </label>
      </div>
      <div class="category-actions">
        <button class="cat-action-btn" @click="selectAll">全选</button>
        <button class="cat-action-btn" @click="deselectAll">清空</button>
      </div>
    </div>

    <div class="export-actions">
      <button class="export-btn" :disabled="exporting || selectedCats.size === 0" @click="doExport">
        <svg v-if="exporting" class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"><animate attributeName="stroke-dashoffset" values="32;0" dur="1s" repeatCount="indefinite"/></circle>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        {{ exporting ? '导出中…' : `导出 ${format === 'excel' ? 'Excel' : 'CSV'}` }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

const format = ref('excel')
const exporting = ref(false)

const allCategories = [
  { key: 'cash', label: '现金存款', color: '#4CAF50' },
  { key: 'deposit', label: '定期存单', color: '#2196F3' },
  { key: 'fund', label: '基金投资', color: '#FF9800' },
  { key: 'stock', label: '股票持仓', color: '#E91E63' },
  { key: 'bond', label: '债券债权', color: '#9C27B0' },
  { key: 'precious_metal', label: '贵金属', color: '#FFD700' },
  { key: 'liability', label: '负债', color: '#F44336' },
]

const selectedCats = reactive(new Set(allCategories.map(c => c.key)))

function toggleCat(key) {
  if (selectedCats.has(key)) {
    selectedCats.delete(key)
  } else {
    selectedCats.add(key)
  }
}

function selectAll() {
  allCategories.forEach(c => selectedCats.add(c.key))
}

function deselectAll() {
  selectedCats.clear()
}

const categoriesParam = computed(() => {
  return selectedCats.size === allCategories.length ? '' : [...selectedCats].join(',')
})

async function doExport() {
  exporting.value = true
  try {
    const token = localStorage.getItem('token')
    const endpoint = format.value === 'excel' ? '/api/export/excel' : '/api/export/csv'
    const params = new URLSearchParams()
    if (categoriesParam.value) params.set('categories', categoriesParam.value)
    const qs = params.toString()
    const url = qs ? `${endpoint}?${qs}` : endpoint

    const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

    const blob = await resp.blob()
    const urlObj = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = urlObj
    a.download = format.value === 'excel' ? 'wealthhome_export.xlsx' : 'wealthhome_export.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(urlObj)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.export-page {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-6);
}

.export-header { margin-bottom: var(--space-6); }
.export-header h3 { font-size: 20px; font-weight: 600; margin: 0 0 4px; color: #1A1A1A; }
.export-desc { color: #757575; font-size: 14px; margin: 0; }

/* Cards */
.export-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

/* ── Category Tags ── */
.export-section {
  margin-bottom: var(--space-6);
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: #424242;
  margin-bottom: var(--space-3);
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: var(--space-3);
}

.category-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-2xl);
  border: 1.5px solid #E0E0E0;
  background: #fff;
  cursor: pointer;
  transition: border-color var(--dur-short4), background var(--dur-short4), box-shadow var(--dur-short4);
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
.category-tag:hover { border-color: #BDBDBD; }
.category-tag.checked {
  border-color: var(--md-primary);
  background: rgba(98, 80, 238, 0.06);
  box-shadow: 0 0 0 2px rgba(98, 80, 238, 0.1);
}

.tag-checkbox { display: none; }

.tag-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-name { font-size: 14px; color: #424242; font-weight: 500; }

.category-actions {
  display: flex;
  gap: 8px;
}

.cat-action-btn {
  padding: 4px 14px;
  border: 1px solid #E0E0E0;
  border-radius: var(--radius-lg);
  background: #fff;
  font-size: 13px;
  color: #757575;
  cursor: pointer;
  transition: border-color var(--dur-short4), color var(--dur-short4);
  -webkit-tap-highlight-color: transparent;
}
.cat-action-btn:hover { border-color: var(--md-primary); color: var(--md-primary); }

/* Cards (continued) */

.export-card {
  position: relative;
  padding: var(--space-6);
  border: 2px solid #E0E0E0;
  border-radius: var(--radius-2xl);
  cursor: pointer;
  transition: border-color var(--dur-short4), box-shadow var(--dur-short4), background var(--dur-short4);
  background: #fff;
}
.export-card:hover { border-color: #BDBDBD; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.export-card.active {
  border-color: var(--md-primary);
  background: rgba(98, 80, 238, 0.04);
  box-shadow: 0 0 0 3px rgba(98, 80, 238, 0.12);
}

.card-icon {
  width: 48px; height: 48px;
  border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: var(--space-4);
}
.card-icon svg { width: 24px; height: 24px; }
.excel-icon { background: #E8F5E9; color: #2E7D32; }
.csv-icon { background: #E3F2FD; color: #1565C0; }

.card-label { font-size: 16px; font-weight: 600; color: #1A1A1A; margin-bottom: 4px; }
.card-desc { font-size: 13px; color: #9E9E9E; }

.card-check {
  position: absolute; top: 12px; right: 12px;
  width: 24px; height: 24px;
  border-radius: 50%;
  background: var(--md-primary);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.card-check svg { width: 16px; height: 16px; }

/* Actions */
.export-actions { text-align: center; }
.export-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 32px;
  background: var(--md-primary);
  color: #fff;
  border: none; border-radius: var(--radius-2xl);
  font-size: 16px; font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-short4), box-shadow var(--dur-short4);
  -webkit-tap-highlight-color: transparent;
}
.export-btn:hover { background: #7C6FF7; box-shadow: 0 4px 12px rgba(98, 80, 238, 0.3); }
.export-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.export-btn svg { width: 20px; height: 20px; }

.spinner { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Mobile ── */
@media (max-width: 640px) {
  .export-page { padding: var(--space-4); }
  .export-cards { grid-template-columns: 1fr; }
  .export-card { padding: var(--space-5); }
  .export-btn { width: 100%; justify-content: center; }
}
</style>
