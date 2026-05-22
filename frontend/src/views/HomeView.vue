<template>
  <div>
    <SearchBar v-model="searchQuery" @update:modelValue="onSearch" />
    <Transition name="fade" mode="out-in">
      <div v-if="loading" class="space-y-4 mt-6">
        <div v-for="i in 3" :key="i" class="bg-white rounded-2xl p-4 animate-pulse">
          <div class="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
          <div class="h-3 bg-gray-100 rounded w-full mb-2"></div>
          <div class="h-3 bg-gray-100 rounded w-2/3"></div>
        </div>
      </div>
      <div v-else-if="notes.length === 0" class="text-center py-20 text-gray-400">
        <p class="text-lg">هنوز یادداشتی نداری!</p>
        <p class="text-sm mt-2">روی دکمهٔ + کلیک کن و شروع کن</p>
      </div>
      <div v-else class="space-y-4 mt-4">
        <NoteCard
          v-for="note in notes"
          :key="note.id"
          :note="note"
          @edit="openEditModal"
          @delete="handleDelete"
        />
      </div>
    </Transition>

<!-- FAB -->
<button
  @click="openCreateModal"
  class="fixed bottom-20 right-6 w-14 h-14 bg-indigo-600 mb-4 text-white rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform z-40 hover:bg-indigo-700"
>
  <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
  </svg>
</button>

    <!-- Note Modal (create / edit) -->
    <NoteModal
      v-if="modalOpen"
      :note="editingNote"
      @close="modalOpen = false"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SearchBar from '../components/notes/SearchBar.vue'
import NoteCard from '../components/notes/NoteCard.vue'
import NoteModal from '../components/notes/NoteModal.vue'
import { fetchNotes, searchNotes, deleteNote } from '../api'
import { useToast } from '../composables/useToast'

const notes = ref([])
const loading = ref(true)
const searchQuery = ref('')
const modalOpen = ref(false)
const editingNote = ref(null)

const { showToast } = useToast()

const loadNotes = async (query = '') => {
  loading.value = true
  try {
    const res = query ? await searchNotes(query) : await fetchNotes()
    notes.value = res.data?.results ?? res.data ?? []
  } catch (err) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

const onSearch = (query) => {
  loadNotes(query)
}

const openCreateModal = () => {
  editingNote.value = null
  modalOpen.value = true
}

const openEditModal = (note) => {
  editingNote.value = { ...note }
  modalOpen.value = true
}

const handleDelete = async (id) => {
  if (!window.confirm('یادداشت حذف شود؟')) return
  try {
    await deleteNote(id)
    notes.value = notes.value.filter(n => n.id !== id)
    showToast('یادداشت حذف شد', 'success')
  } catch (err) {
    // handled by interceptor
  }
}

const onSaved = () => {
  modalOpen.value = false
  editingNote.value = null
  loadNotes(searchQuery.value)
}

onMounted(() => {
  console.log('✅ HomeView mounted')
  loadNotes()
})


</script>