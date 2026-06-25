<template>
  <div class="login-page">
    <div class="login-left">
      <div class="login-left-content">
        <h1>Wealth<span>Home</span></h1>
        <p>家庭资产管理 · 一目了然</p>
      </div>
    </div>
    <div class="login-right">
      <div class="login-box">
        <h2>{{ isLogin ? '欢迎回来' : '创建账户' }}</h2>
        <p class="subtitle">{{ isLogin ? '登录你的家庭资产' : '开始管理你的财富' }}</p>
        <el-form @submit.prevent="submit" label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password />
          </el-form-item>
          <el-button type="primary" size="large" @click="submit" :loading="loading" style="width:100%; margin-top:8px;">
            {{ isLogin ? '登录' : '注册' }}
          </el-button>
        </el-form>
        <p style="text-align:center; margin-top:20px; font-size:14px; color:#94a3b8;">
          {{ isLogin ? '还没有账户？' : '已有账户？' }}
          <a href="javascript:void(0)" @click="isLogin = !isLogin" style="color:#6250EE; font-weight:500;">
            {{ isLogin ? '立即注册' : '去登录' }}
          </a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { loginApi, registerApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username || !form.password) return ElMessage.warning('请填写完整')
  loading.value = true
  try {
    const api = isLogin.value ? loginApi : registerApi
    const { data } = await api({ username: form.username, password: form.password })
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.user.username)
    ElMessage.success(isLogin.value ? '登录成功' : '注册成功')
    router.push('/')
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}
</script>
