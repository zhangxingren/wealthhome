import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { auth: true } },
  { path: '/cash', name: 'Cash', component: () => import('../views/CashManage.vue'), meta: { auth: true } },
  { path: '/deposit', name: 'Deposit', component: () => import('../views/DepositManage.vue'), meta: { auth: true } },
  { path: '/fund', name: 'Fund', component: () => import('../views/FundManage.vue'), meta: { auth: true } },
  { path: '/stock', name: 'Stock', component: () => import('../views/StockManage.vue'), meta: { auth: true } },
  { path: '/bond', name: 'Bond', component: () => import('../views/BondManage.vue'), meta: { auth: true } },
  { path: '/precious-metal', name: 'PreciousMetal', component: () => import('../views/PreciousMetalManage.vue'), meta: { auth: true } },
  { path: '/liability', name: 'Liability', component: () => import('../views/LiabilityManage.vue'), meta: { auth: true } },
  { path: '/networth', name: 'NetWorth', component: () => import('../views/NetWorth.vue'), meta: { auth: true } },
  { path: '/family', name: 'Family', component: () => import('../views/Family.vue'), meta: { auth: true } },
  { path: '/export', name: 'Export', component: () => import('../views/Export.vue'), meta: { auth: true } },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) return '/login'
  if (to.path === '/login' && token) return '/'
})

export default router
