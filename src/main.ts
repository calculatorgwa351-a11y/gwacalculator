import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setupErrorHandler } from './utils/errorHandler'

// Import global styles (including Tailwind CSS)
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize global error handling strategy
setupErrorHandler(app)

app.mount('#app')
