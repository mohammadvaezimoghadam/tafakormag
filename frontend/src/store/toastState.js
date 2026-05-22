import { reactive } from 'vue'

export const toastState = reactive({
  messages: [],

  add({ message, type = 'info', duration = 4000 }) {
    const id = Date.now() + Math.random()
    this.messages.push({ id, message, type })
    if (type !== 'error') {
      setTimeout(() => {
        this.remove(id)
      }, duration)
    }
  },

  remove(id) {
    this.messages = this.messages.filter(m => m.id !== id)
  }
})