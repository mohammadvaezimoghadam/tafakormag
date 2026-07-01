import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

import { useLanguageStore } from '@/stores/languageStore'
const languageStore = useLanguageStore()
languageStore.init()

app.mount('#app')

