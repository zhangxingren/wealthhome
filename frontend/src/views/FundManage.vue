<template>
  <AssetManagePage :config="config" />
</template>

<script setup>
import { listFund, createFund, updateFund, deleteFund, getAssetTrend, fetchFundPrices } from '../api'
import AssetManagePage from '../components/AssetManagePage.vue'

const config = {
  assetType: 'fund',
  pageTitle: '基金持仓',
  apiLabel: '基金',
  trendType: 'fund',
  costField: 'cost_nav',
  currentField: 'current_nav',
  quantityField: 'shares',
  columns: [
    { prop: 'code', label: '代码', width: 78 },
    { prop: 'name', label: '名称', minWidth: 90, showOverflowTooltip: true },
    { prop: 'shares', label: '份额', width: 70 },
    { prop: 'cost_nav', label: '成本净值', width: 80 },
    { prop: null, label: '投入成本', minWidth: 95, slot: 'invested_cost' },
    { prop: 'current_nav', label: '当前净值', minWidth: 82 },
    { prop: null, label: '市值', minWidth: 100, slot: 'market_value' },
    { prop: null, label: '盈亏金额', minWidth: 105, slot: 'pnl_amount' },
    { prop: null, label: '盈亏%', width: 70, slot: 'pnl' },
    { prop: 'fund_type', label: '类型', width: 65, slot: 'fund_type' },
  ],
  formRows: [
    [{ prop:'code', label:'代码', type:'text', span:8 },
     { prop:'name', label:'名称', type:'text', span:12 },
     { prop:'fund_type', label:'类型', type:'text', span:4 }],
    [{ prop:'shares', label:'份额', type:'number', precision:2, span:8 },
     { prop:'cost_nav', label:'成本净值', type:'number', precision:4, span:8 },
     { prop:'current_nav', label:'当前净值', type:'number', precision:4, span:8 }],
    [{ prop:'note', label:'备注', type:'text', span:24 }],
  ],
  defaultForm: { code: '', name: '', shares: 0, cost_nav: 0, current_nav: 0, fund_type: '', note: '' },
  apiKeyNeeded: false,
  apiDialogTitle: '行情来源说明',
  apiKeyLabel: '',
  apiKeyPlaceholder: '',
  apiDescription: '基金净值来自天天基金公开接口，无需 API Key。点击「刷新报价」即可获取最新净值。',
  apiProviderUrl: '',
  settingKey: '',
  storageKey: '',
  api: {
    list: listFund, create: createFund, update: updateFund, delete: deleteFund,
    getTrend: getAssetTrend, refreshPrices: () => fetchFundPrices(),
    // 基金不需要 key，提供空实现占位
    getUserSettings: async () => ({}),
    putUserSetting: async () => {},
  },
}
</script>
