import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Category from '../views/Category.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/category/:id', name: 'category', component: Category }
]

const router = createRouter({
  // 用 hash 模式，部署到静态托管（CloudBase、Netlify）更稳
  history: createWebHashHistory(),
  routes
})

export default router