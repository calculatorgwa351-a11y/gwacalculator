import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setupErrorHandler } from './utils/errorHandler'
import { useAuthStore } from './stores/auth'

// Import global styles (including Tailwind CSS)
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Hydrate auth state once on boot (so admin links & guards work immediately).
void useAuthStore(pinia).fetchMe()

// Initialize global error handling strategy
setupErrorHandler(app)

app.mount('#app')
