import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import LabsApp from './LabsApp.vue'
import labsRouter from './router/labsRouter'

const app = createApp(LabsApp)
const pinia = createPinia()
app.use(pinia)
app.use(labsRouter)

import { useLanguageStore } from '@/stores/languageStore'
const languageStore = useLanguageStore()
languageStore.init()

app.mount('#app')

