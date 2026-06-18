import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import MapaMorosidad from '../views/MapaMorosidad.vue'
import MisRutas from '../views/MisRutas.vue'
import Monitoreo from '../views/Monitoreo.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { requiresAuth: false } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/mapa', name: 'MapaMorosidad', component: MapaMorosidad, meta: { requiresAuth: true } },
  { path: '/mis-rutas', name: 'MisRutas', component: MisRutas, meta: { requiresAuth: true } },
  { path: '/monitoreo', name: 'Monitoreo', component: Monitoreo, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next(usuario.rol === 'NORMAL' ? '/mis-rutas' : '/dashboard')
  } else if (to.meta.requiresAuth && token) {
    if (usuario.rol === 'NORMAL' && (to.path === '/dashboard' || to.path === '/mapa' || to.path === '/monitoreo')) {
      next('/mis-rutas')
    } else if (to.path === '/monitoreo' && usuario.rol !== 'ADMIN') {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router