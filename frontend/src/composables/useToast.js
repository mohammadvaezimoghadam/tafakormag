import { toastState } from '../store/toastState'

export function useToast() {
  const showToast = (message, type = 'info') => {
    toastState.add({ message, type })
  }

  return { showToast }
}