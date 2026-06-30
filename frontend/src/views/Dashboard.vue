<template>
  <div>
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
      <el-radio-group v-model="scope" @change="loadAll" size="small">
        <el-radio-button value="mine">我的资产</el-radio-button>
        <el-radio-button value="family">家庭汇总</el-radio-button>
      </el-radio-group>
      <div style="font-size:12px; color:#86868b; display:flex; align-items:center; gap:4px;">
        <span>点击金额切换单位</span>
        <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:#f5f5f7; text-align:center; line-height:18px; font-size:10px; font-weight:700; color:var(--c-accent);">{{ label() }}</span>
      </div>
    </div>

    <!-- Family mode -->
    <template v-if="scope === 'family' && familyData.members">
      <div v-for="(m, mid) in familyData.members" :key="mid" style="margin-bottom:28px;">
        <h4 style="font-size:14px; font-weight:700; margin-bottom:10px; color:var(--c-text-secondary); letter-spacing:-0.2px;">
          {{ m.display_name || m.username }}
        </h4>
        <div class="stat-grid">
          <div class="stat-card card-info" @click="cycle">
            <div class="label">总资产</div><div class="value">{{ format(adjustedMember(mid, m).total_asset) }}</div>
          </div>
          <div v-if="adjustedMember(mid, m).total_liability > 0" class="stat-card card-danger" @click="cycle">
            <div class="label">总负债</div><div class="value">{{ format(adjustedMember(mid, m).total_liability) }}</div>
          </div>
          <div class="stat-card card-success" @click="cycle">
            <div class="label">净资产</div><div class="value">{{ format(adjustedMember(mid, m).net_worth) }}</div>
          </div>
          <div
            v-for="cfg in visibleFamilyCards(String(mid))"
            :key="cfg.key"
            class="stat-card family-cat-card"
            @click="cycle"
          >
            <div class="family-cat-top">
              <div class="label">{{ cfg.label }}</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, cfg.key) }" @click.stop="toggleFamilyHidden(mid, cfg.key)" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, cfg.key)) }}</div>
          </div>
        </div>
      </div>

      <div v-if="familyData.family" class="family-total-card" @click="cycle">
        <div style="font-size:13px; font-weight:600; margin-bottom:16px; letter-spacing:.3px; text-transform:uppercase;">Family Total</div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px,1fr)); gap:16px;">
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">总资产</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;" v-html="formatHtml(adjustedFamilyTotal.total_asset)"></div></div>
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">总负债</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;">{{ format(adjustedFamilyTotal.total_liability) }}</div></div>
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">净资产</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;">{{ format(adjustedFamilyTotal.net_worth) }}</div></div>
        </div>
      </div>

      <InvestSummaryCard :summary="familyInvestSummary" title="投资汇总" />
      <HiddenAssetsFab :hidden-items="familyHiddenList" title="已隐藏的家庭资产" @restore="(key, mid) => mid ? toggleFamilyHidden(mid, key) : toggleAssetVisibility(key)" />

      <!-- Family net worth trend chart -->
      <div class="page-card" style="margin-top:24px;">
        <div class="page-card-header"><h3>家庭净值变化趋势</h3></div>
        <div class="page-card-body">
          <TrendChart :data="familyTrendForChart" :color="'#E8654A'" :privacy="privacyMode" :tooltip-prefix="'家庭净值'" :empty-text="'暂无家庭净值快照'" embedded>
            <template #empty>
              <div class="icon"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg></div>
              <p>暂无家庭净值快照<br><span style="font-size:12px;">家庭成员各自记录净值快照后，此处自动汇总展示</span></p>
            </template>
          </TrendChart>
        </div>
      </div>
    </template>

    <!-- Personal mode -->
    <template v-else>
      <div class="top-fixed-grid">
        <div class="stat-card glass-card card-primary" @click="cycle">
          <div class="label">净资产<el-tag size="small" style="margin-left:6px; vertical-align:middle;">{{ label() }}</el-tag></div>
          <div class="asset-value" v-html="formatPrivacy(formatHtml(adjustedSummary.net_worth))"></div>
          <div class="sub">净值 = 总资产 - 总负债</div>
          <div class="card-icon">🏠</div>
        </div>
        <div class="stat-card glass-card card-info" @click="cycle">
          <div class="label">总资产</div>
          <div class="asset-value" v-html="formatPrivacy(formatHtml(adjustedSummary.total_asset))"></div>
          <div class="sub">所有资产总和</div>
          <div class="card-icon">💰</div>
        </div>
      </div>

      <div class="dynamic-grid" v-if="hasAnyAsset">
        <div
          v-for="cfg in visiblePersonalCards()"
          :key="cfg.key"
          class="stat-card asset-card"
          :class="cfg.css"
          @click.stop="cycle"
        >
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">{{ cfg.icon }}</span>
              <span>{{ cfg.label }}</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden(cfg.key) }" @click.stop="toggleAssetVisibility(cfg.key)" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value" v-html="formatPrivacy(formatHtml(cardAssetValue(cfg.key)))"></div>
          <div class="asset-sub">
            <template v-if="cfg.key === 'deposit'">已得利息 ¥{{ formatPrivacy(formatCompact(depositInterest)) }}</template>
            <template v-else>{{ cfg.sub }}</template>
          </div>
        </div>
      </div>

      <div v-if="!hasAnyAsset && !hiddenAssetList.length" class="empty-assets">
        <div class="empty-icon">📊</div>
        <h4>暂无资产记录</h4>
        <p>点击左侧菜单添加现金、定期、基金、股票、债券或贵金属，它们会动态出现在这里。</p>
      </div>

      <InvestSummaryCard :summary="investSummary" title="投资汇总" />
      <HiddenAssetsFab :hidden-items="hiddenAssetList" title="已隐藏的资产" @restore="(key) => toggleAssetVisibility(key)" />

      <!-- Net worth chart -->
      <div class="page-card" style="margin-top:24px;">
        <div class="page-card-header"><h3>净值变化趋势</h3></div>
        <div class="page-card-body">
          <TrendChart :data="displayTrendData" :color="'#6250EE'" :privacy="privacyMode" empty-text="暂无净值快照" embedded>
            <template #empty>
              <div class="icon"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg></div>
              <p>暂无净值快照<br><span style="font-size:12px;">添加资产后点击「净值趋势」页面记录</span></p>
            </template>
          </TrendChart>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { getSummary, getTrend, getDetail, getDepositInterest, getFamilyTrend, getInvestmentSummary, getFamilyInvestmentSummary } from '../api'
import { useAmountFormat, formatHtml } from '../composables/useAmountFormat'
import { usePrivacy } from '../composables/usePrivacy'
import { useTimeRangeStore } from '../stores/timeRange'
import TrendChart from '../components/TrendChart.vue'
import HiddenAssetsFab from '../components/HiddenAssetsFab.vue'
import InvestSummaryCard from '../components/InvestSummaryCard.vue'

const scope = ref('mine')
const timeStore = useTimeRangeStore()
const summary = reactive({ net_worth: 0, total_asset: 0, total_liability: 0, cash: 0, deposit: 0, fund: 0, stock: 0, bond: 0, precious_metal: 0 })
const familyData = reactive({ members: null, family: null })
const trendData = ref([])
const depositInterest = ref(0)

const investSummary = reactive({ total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
const familyInvestSummary = reactive({ total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
const familyTrendData = ref({})

const { cycle, format, label } = useAmountFormat()
const { privacyMode, toggleAssetVisibility, isHidden, formatPrivacy, hiddenAssets, familyHiddenAssets, isFamilyHidden, toggleFamilyHidden, getFamilyHidden } = usePrivacy()

// ── 资产卡片 v-for 配置 ──
const personalAssetCardConfigs = [
  { key: 'cash', icon: '💵', label: '现金', css: 'asset-cash', sub: '活期存款' },
  { key: 'deposit', icon: '🏦', label: '定期', css: 'asset-deposit', sub: null },
  { key: 'fund', icon: '📊', label: '基金', css: 'asset-fund', sub: '市值' },
  { key: 'stock', icon: '📈', label: '股票', css: 'asset-stock', sub: '持仓市值' },
  { key: 'bond', icon: '📜', label: '债券', css: 'asset-bond', sub: '债权' },
  { key: 'precious_metal', icon: '🪙', label: '贵金属', css: 'asset-precious-metal', sub: '黄金/白银等' },
  { key: 'liability', icon: '🏠', label: '负债', css: 'asset-liability', sub: '总负债' },
]

const familyAssetCardConfigs = [
  { key: 'cash', label: '现金' },
  { key: 'deposit', label: '定期' },
  { key: 'fund', label: '基金' },
  { key: 'stock', label: '股票' },
  { key: 'bond', label: '债券' },
  { key: 'precious_metal', label: '贵金属' },
  { key: 'liability', label: '负债' },
]

const CAT_LABEL_MAP = { cash: '现金', deposit: '定期', fund: '基金', stock: '股票', bond: '债券', precious_metal: '贵金属', liability: '负债' }
const CAT_KEYS = ['cash', 'deposit', 'fund', 'stock', 'bond', 'precious_metal']

// ── 格式化辅助 ──
function formatCompact(amount) {
  const v = Number(amount) || 0
  if (v >= 10000) return (v / 10000).toFixed(1) + '万'
  if (v >= 1000) return (v / 1000).toFixed(1) + 'k'
  return v.toFixed(0)
}

function cardAssetValue(key) {
  if (key === 'liability') return summary.total_liability
  return summary[key] || 0
}

function familyCardValue(m, key) {
  if (key === 'liability') return m.summary.total_liability
  return m.summary[key] || 0
}

// ── 扣除隐藏资产的调整值 ──
const adjustedSummary = computed(() => {
  const s = { ...summary }
  let hiddenTotal = 0
  for (const cat of CAT_KEYS) {
    if (hiddenAssets.value.includes(cat)) hiddenTotal += (s[cat] || 0)
  }
  s.total_asset = (s.total_asset || 0) - hiddenTotal
  s.net_worth = s.total_asset - (hiddenAssets.value.includes('liability') ? 0 : (s.total_liability || 0))
  return s
})

function adjustedMember(memberId, m) {
  const s = { ...m.summary }
  let hiddenAssetTotal = 0
  for (const cat of CAT_KEYS) {
    if ((familyHiddenAssets.value[String(memberId)] || []).includes(cat)) hiddenAssetTotal += (s[cat] || 0)
  }
  s.total_asset = (s.total_asset || 0) - hiddenAssetTotal
  if ((familyHiddenAssets.value[String(memberId)] || []).includes('liability')) s.total_liability = 0
  s.net_worth = s.total_asset - (s.total_liability || 0)
  return s
}

const adjustedFamilyTotal = computed(() => {
  if (!familyData.members) return { total_asset: 0, total_liability: 0, net_worth: 0 }
  let ta = 0, tl = 0
  for (const [mid, m] of Object.entries(familyData.members)) {
    const adj = adjustedMember(mid, m)
    ta += adj.total_asset
    tl += adj.total_liability
  }
  return { total_asset: ta, total_liability: tl, net_worth: ta - tl }
})

// 个人资产卡片可见性：返回过滤后的配置数组
function visiblePersonalCards() {
  const _ = hiddenAssets.value // 强制建立响应式依赖
  return personalAssetCardConfigs.filter(cfg => !hiddenAssets.value.includes(cfg.key) && cardAssetValue(cfg.key) > 0)
}

// 家庭卡片可见性：返回过滤后的配置数组，隐藏的卡片直接不渲染
function visibleFamilyCards(memberId) {
  const _ = familyHiddenAssets.value // 强制建立响应式依赖
  const m = familyData.members?.[memberId]
  if (!m) return []
  const hidden = familyHiddenAssets.value[memberId] || []
  return familyAssetCardConfigs.filter(cfg => !hidden.includes(cfg.key) && familyCardValue(m, cfg.key) > 0)
}

// ── 隐藏资产列表 ──
const hiddenAssetList = computed(() => {
  const map = { cash: '现金', deposit: '定期', fund: '基金', stock: '股票', bond: '债券', precious_metal: '贵金属', liability: '负债' }
  return hiddenAssets.value.map(k => ({ key: k, label: map[k] || k }))
})

const familyHiddenList = computed(() => {
  const result = []
  if (!familyData.members) return result
  for (const [mid, m] of Object.entries(familyData.members)) {
    const cats = getFamilyHidden(mid)
    if (cats.length > 0) {
      result.push({
        mid,
        key: `${mid}_hidden`,
        label: m.display_name || m.username,
        children: cats.map(c => ({ key: c, label: CAT_LABEL_MAP[c] || c })),
      })
    }
  }
  return result
})

// ── 趋势数据 ──
const familyTrendForChart = computed(() => {
  const _ = familyHiddenAssets.value // 显式依赖
  const d = familyTrendData.value
  if (!d.dates || !d.values) return []
  return d.dates.map((date, i) => ({ snap_date: date, net_worth: d.values[i] || 0 }))
})

const displayTrendData = computed(() => {
  let data = trendData.value
  if (hiddenAssets.value.length > 0) {
    data = data.map(d => {
      const excluded = hiddenAssets.value.reduce((sum, cat) => sum + (d[cat] || 0), 0)
      return { ...d, net_worth: (d.net_worth || 0) - excluded }
    })
  }
  return data
})

const hasAnyAsset = computed(() => {
  return summary.cash > 0 || summary.deposit > 0 || summary.fund > 0 ||
         summary.stock > 0 || summary.bond > 0 || summary.precious_metal > 0 ||
         summary.total_liability > 0
})

// ── 数据加载 ──
async function loadAll() {
  try {
    const { data } = await getSummary(scope.value)
    if (scope.value === 'family') {
      familyData.members = data.members || null
      familyData.family = data.family || null
      try {
        const invRes = await getFamilyInvestmentSummary()
        Object.assign(familyInvestSummary, invRes.data || { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      } catch (e) {
        console.error('家庭投资汇总加载失败:', e)
        Object.assign(familyInvestSummary, { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      }
    } else {
      Object.assign(summary, data)
      try {
        const invRes = await getInvestmentSummary()
        Object.assign(investSummary, invRes.data || { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      } catch {
        Object.assign(investSummary, { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      }
      if (summary.deposit > 0) {
        try {
          const { data: detail } = await getDetail('deposit')
          const deposits = detail?.deposit || []
          let totalInterest = 0
          for (const d of deposits) {
            const { data: interest } = await getDepositInterest(d.id)
            totalInterest += interest.accrued_interest || 0
          }
          depositInterest.value = totalInterest
        } catch (e) {
          console.error('存款利息加载失败:', e)
        }
      }
    }
  } catch {
    console.error('加载汇总数据失败')
  }
}

async function loadTrend() {
  try {
    const { data } = await getTrend(30, timeStore.start, timeStore.end)
    trendData.value = data || []
  } catch {
    trendData.value = []
    console.error('加载趋势数据失败')
  }
}

async function loadFamilyTrend() {
  try {
    const { data } = await getFamilyTrend(30, timeStore.start, timeStore.end)
    familyTrendData.value = data || {}
  } catch {
    familyTrendData.value = {}
    console.error('加载家庭趋势数据失败')
  }
}

onMounted(() => { loadAll(); loadTrend() })
watch(scope, () => { loadAll(); if (scope.value === 'family') loadFamilyTrend() })
watch(() => [timeStore.start, timeStore.end], () => {
  loadTrend()
  if (scope.value === 'family') loadFamilyTrend()
})

let _familyTrendDelay = null
watch(familyHiddenAssets, () => {
  if (scope.value !== 'family') return
  clearTimeout(_familyTrendDelay)
  _familyTrendDelay = setTimeout(() => loadFamilyTrend(), 600)
}, { deep: true })
</script>

<style scoped>
.top-fixed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.glass-card {
  background: rgba(255,251,254,0.72); backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 0.5px solid rgba(103,80,164,0.08); box-shadow: var(--md-elevation-3);
}
.glass-card .card-icon {
  position: absolute; top: 20px; right: 20px; font-size: 28px; opacity: 0.2; transition: opacity 0.3s;
}
.glass-card:hover .card-icon { opacity: 0.4; }

.dynamic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px; margin-bottom: 24px;
}
.asset-card {
  position: relative; overflow: hidden; border-left: 4px solid;
  transition: transform 0.2s var(--ease-spring), box-shadow 0.2s;
}
.asset-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-card-hover); }
.asset-card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.asset-label { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 14px; color: var(--c-text-secondary); }
.asset-icon { font-size: 20px; }
.asset-value { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 4px; }
.asset-sub { font-size: 12px; color: var(--c-text-tertiary); }

.eye-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: var(--radius-full);
  cursor: pointer; opacity: 0; transition: all 0.2s var(--ease-apple); color: var(--c-text-tertiary);
}
.eye-btn svg { width: 15px; height: 15px; }
.asset-card:hover .eye-btn { opacity: 0.5; }
.asset-card:hover .eye-btn:hover { opacity: 1 !important; color: var(--md-on-surface); background: rgba(0,0,0,0.06); }

/* Asset-specific border and value colors */
.asset-cash { border-left-color: #10B981; background: linear-gradient(135deg, rgba(16,185,129,0.05) 0%, rgba(16,185,129,0.02) 100%); }
.asset-cash .asset-value { color: #10B981; }
.asset-deposit { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.05) 0%, rgba(245,158,11,0.02) 100%); }
.asset-deposit .asset-value { color: #F59E0B; }
.asset-fund { border-left-color: #6366F1; background: linear-gradient(135deg, rgba(99,102,241,0.05) 0%, rgba(99,102,241,0.02) 100%); }
.asset-fund .asset-value { color: #6366F1; }
.asset-stock { border-left-color: #EF4444; background: linear-gradient(135deg, rgba(239,68,68,0.05) 0%, rgba(239,68,68,0.02) 100%); }
.asset-stock .asset-value { color: #EF4444; }
.asset-bond { border-left-color: #8B5CF6; background: linear-gradient(135deg, rgba(139,92,246,0.05) 0%, rgba(139,92,246,0.02) 100%); }
.asset-bond .asset-value { color: #8B5CF6; }
.asset-precious-metal { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(218,165,32,0.03) 100%); }
.asset-precious-metal .asset-value { color: #DAA520; }
.asset-liability { border-left-color: #F97316; background: linear-gradient(135deg, rgba(249,115,22,0.05) 0%, rgba(249,115,22,0.02) 100%); }
.asset-liability .asset-value { color: #F97316; }

.empty-assets {
  text-align: center; padding: 60px 20px; background: var(--md-surface-container-low);
  border-radius: var(--radius-xl); margin-bottom: 24px; border: 1px dashed var(--md-outline-variant);
}
.empty-assets .empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.3; }
.empty-assets h4 { font-size: 18px; font-weight: 700; margin-bottom: 8px; color: var(--c-text); }

/* Family category cards */
.family-cat-card { position: relative; }
.family-cat-card .eye-btn:hover { opacity: 1 !important; color: var(--md-on-surface); background: rgba(0,0,0,0.04); }
.family-cat-card.family-hidden { opacity: 0.45; filter: grayscale(0.3); }
.family-cat-card.family-hidden:hover { opacity: 0.7; filter: grayscale(0.1); }

/* 家庭卡片标签行：label + 眼睛图标保持一行 */
.family-cat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 4px;
}
.family-cat-top .label {
  flex: 1;
  min-width: 0;
  text-transform: none;
}

@media (max-width: 600px) {
  .glass-card .value { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
}
</style>
