import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api', timeout: 15000 })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
      return Promise.reject(err)
    }
    const msg = err.response?.data?.detail || err.message
    if (msg && msg !== 'Request failed with status code 404') {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default api

// ── CRUD 工厂（消除重复的 list/create/update/delete 模式）──
const crud = (path) => ({
  list: (params) => api.get(path, { params }),
  create: (data) => api.post(path, data),
  update: (id, data) => api.put(`${path}/${id}`, data),
  delete: (id) => api.delete(`${path}/${id}`),
})

// Auth
export const loginApi = (data) => api.post('/auth/login', data)
export const registerApi = (data) => api.post('/auth/register', data)
export const getProfile = () => api.get('/auth/me')
export const updateProfile = (data) => api.put('/auth/me', data)

// Assets — CRUD 工厂
const cashCrud = crud('/assets/cash')
export const listCash = cashCrud.list
export const createCash = cashCrud.create
export const updateCash = cashCrud.update
export const deleteCash = cashCrud.delete

const depositCrud = crud('/assets/deposit')
export const listDeposit = depositCrud.list
export const createDeposit = depositCrud.create
export const updateDeposit = depositCrud.update
export const deleteDeposit = depositCrud.delete
export const getDepositInterest = (id) => api.get(`/assets/deposit/${id}/interest`)

const fundCrud = crud('/assets/fund')
export const listFund = fundCrud.list
export const createFund = fundCrud.create
export const updateFund = fundCrud.update
export const deleteFund = fundCrud.delete
export const fetchFundPrices = () => api.post('/assets/fund/fetch-prices', {})

const stockCrud = crud('/assets/stock')
export const listStock = stockCrud.list
export const createStock = stockCrud.create
export const updateStock = stockCrud.update
export const deleteStock = stockCrud.delete
export const fetchStockPrices = (apiKey) => api.post('/assets/stock/fetch-prices', { api_key: apiKey })

const bondCrud = crud('/assets/bond')
export const listBond = bondCrud.list
export const createBond = bondCrud.create
export const updateBond = bondCrud.update
export const deleteBond = bondCrud.delete

export const getSummary = (scope = 'mine') => api.get('/assets/summary', { params: { scope } })
export const getDetail = (category) => api.get('/assets/detail', { params: { category } })
export const getInvestmentSummary = () => api.get('/assets/investment-summary')
export const getFamilyInvestmentSummary = () => api.get('/assets/family/investment-summary')

// Liabilities — CRUD 工厂
const liabilityCrud = crud('/liabilities')
export const listLiabilities = liabilityCrud.list
export const createLiability = liabilityCrud.create
export const updateLiability = liabilityCrud.update
export const deleteLiability = liabilityCrud.delete
export const getRepayPlan = (id) => api.get(`/liabilities/${id}/plan`)
export const updateRemaining = (id, remaining) => api.put(`/liabilities/${id}/remaining`, null, { params: { remaining } })

// Precious Metals — CRUD 工厂
const pmCrud = crud('/precious-metals')
export const listPreciousMetals = pmCrud.list
export const createPreciousMetal = pmCrud.create
export const updatePreciousMetal = pmCrud.update
export const deletePreciousMetal = pmCrud.delete
export const refreshPreciousMetalPrices = () => api.post('/precious-metals/refresh')
export const getPreciousMetalSummary = () => api.get('/precious-metals/summary')

// Net Worth
export const takeSnapshot = (snapDate) => api.post('/networth/snapshot', null, { params: { snap_date: snapDate } })
export const listSnapshots = (params) => api.get('/networth/snapshots', { params })
export const getTrend = (limit = 30, start = null, end = null) => {
  const params = { limit }
  if (start) params.start = start
  if (end) params.end = end
  return api.get('/networth/trend', { params })
}
export const getAssetTrend = (category, limit = 30, start = null, end = null) => {
  const params = { field: category, limit }
  if (start) params.start = start
  if (end) params.end = end
  return api.get('/networth/trend/category', { params })
}
export const deleteSnapshot = (id) => api.delete(`/networth/snapshot/${id}`)

// Family
export const getFamily = () => api.get('/family')
export const joinFamily = (code) => api.post('/family/join', { invite_code: code })
export const listFamilyMembers = () => api.get('/family/members')
export const getFamilyTrend = (days = 30, start = null, end = null) => {
  const params = { days }
  if (start) params.start = start
  if (end) params.end = end
  return api.get('/assets/family/trend', { params })
}

// User Settings (跨设备同步)
export const getUserSettings = () => api.get('/user/settings')
export const putUserSetting = (key, value) => api.put(`/user/settings/${key}`, { value })
