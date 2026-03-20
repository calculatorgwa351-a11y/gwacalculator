import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminView from '../views/AdminView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/ProfileView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAdmin: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true }
    }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  const needsAuth = !!to.meta.requiresAuth || !!to.meta.requiresAdmin
  if ((needsAuth || !!to.meta.guestOnly) && !auth.hydrated) {
    await auth.fetchMe()
  }

  // If we need auth but don't have a user yet, re-check (login can happen after initial hydration).
  if (needsAuth && !auth.isAuthenticated) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAdmin) {
    if (!auth.isAuthenticated) return { path: '/' }
    if (!auth.isAdmin) return { path: '/dashboard' }
  }

  if (to.meta.requiresAuth) {
    if (!auth.isAuthenticated) return { path: '/' }
  }

  if (to.meta.guestOnly) {
    if (auth.isAuthenticated) return { path: auth.isAdmin ? '/admin' : '/dashboard' }
  }
})

export default router
