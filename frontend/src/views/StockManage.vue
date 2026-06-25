<template>
  <AssetManagePage :config="config" />
</template>

<script setup>
import { listStock, createStock, updateStock, deleteStock, getAssetTrend, fetchStockPrices, getUserSettings, putUserSetting } from '../api'
import AssetManagePage from '../components/AssetManagePage.vue'

const config = {
  assetType: 'stock',
  pageTitle: '股票持仓',
  apiLabel: '股票',
  trendType: 'stock',
  costField: 'cost_price',
  currentField: 'current_price',
  quantityField: 'shares',
  columns: [
    { prop: 'code', label: '代码', width: 90 },
    { prop: 'name', label: '名称', minWidth: '110' },
    { prop: 'shares', label: '股数', width: 80 },
    { prop: 'cost_price', label: '成本价', width: 90 },
    { prop: 'current_price', label: '现价', width: 90 },
    { prop: null, label: '市值', width: 120, slot: 'market_value' },
    { prop: null, label: '盈亏', width: 90, slot: 'pnl' },
    { prop: 'market', label: '市场', width: 60, slot: 'market' },
  ],
  formRows: [
    [{ prop:'code', label:'代码', type:'text', span:8 },
     { prop:'name', label:'名称', type:'text', span:12 },
     { prop:'market', label:'市场', type:'select', span:4, options:[{label:'SH',value:'sh'},{label:'SZ',value:'sz'},{label:'HK',value:'hk'},{label:'US',value:'us'}] }],
    [{ prop:'shares', label:'股数', type:'number', span:8 },
     { prop:'cost_price', label:'成本价', type:'number', precision:3, span:8 },
     { prop:'current_price', label:'现价', type:'number', precision:3, span:8 }],
    [{ prop:'note', label:'备注', type:'text', span:24 }],
  ],
  defaultForm: { code: '', name: '', shares: 0, cost_price: 0, current_price: 0, market: 'sh', note: '' },
  apiKeyNeeded: true,
  apiDialogTitle: 'Tushare API 设置',
  apiKeyLabel: 'Tushare API Token',
  apiKeyPlaceholder: '粘贴你的 Tushare token',
  apiDescription: '前往 ',
  apiProviderUrl: 'https://tushare.pro',
  settingKey: 'tushare_token',
  storageKey: 'tushare_apikey',
  api: {
    list: listStock, create: createStock, update: updateStock, delete: deleteStock,
    getTrend: getAssetTrend, refreshPrices: (apiKey) => fetchStockPrices(apiKey),
    getUserSettings, putUserSetting,
  },
}
</script>
