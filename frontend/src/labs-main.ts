import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import LabsApp from './LabsApp.vue'
import labsRouter from './router/labsRouter'

const app = createApp(LabsApp)
app.use(createPinia())
app.use(labsRouter)
app.mount('#app')

