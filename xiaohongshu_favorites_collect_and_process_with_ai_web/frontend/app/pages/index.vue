<script setup lang="ts">
import { ref, computed } from 'vue'
import type { NoteDetailsItem } from '~/types/notes'
import { useNotes } from '~/composables/useNotes'
import NoteCard from '~/components/NoteCard.vue'
import SearchFilter from '~/components/SearchFilter.vue'

const { notes, status } = useNotes()

const searchQuery = ref('')
const selectedPlatform = ref('all')

function getNotePlatform(note: NoteDetailsItem): string {
  if (note.platform) return note.platform
  const pools: string[] = []
  if (note.images && note.images.length) pools.push(...note.images)
  if (note.author_info?.avatar) pools.push(note.author_info.avatar)
  if (note.desc) pools.push(note.desc)
  const blob = pools.join(' ').toLowerCase()
  if (blob.includes('xhscdn.com')) return 'xiaohongshu'
  if (blob.includes('bilibili.com') || blob.includes('hdslb.com')) return 'bilibili'
  if (blob.includes('zhihu.com') || blob.includes('zhimg.com')) return 'zhihu'
  return 'unknown'
}

const filteredNotes = computed(() => {
  let result = notes.value || []

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(note =>
      note.title.toLowerCase().includes(q) ||
      (note.ai_summary?.summary || '').toLowerCase().includes(q) ||
      (note.ai_summary?.keywords || []).some(tag => tag.toLowerCase().includes(q)) ||
      (note.tags || []).some(tag => tag.toLowerCase().includes(q))
    )
  }

  if (selectedPlatform.value !== 'all') {
    result = result.filter(note => getNotePlatform(note) === selectedPlatform.value)
  }

  return result
})

function updateSearchQuery(query: string) {
  searchQuery.value = query
}

function updatePlatform(platform: string) {
  selectedPlatform.value = platform
}
</script>

<template>
  <div>
    <header>
      <SearchFilter
        @update:searchQuery="updateSearchQuery"
        @update:platform="updatePlatform"
      />
    </header>

    <main class="container mx-auto p-4 sm:p-6 lg:p-8">
      <div v-if="status === 'pending'" class="text-center py-12">
        <p>Loading notes...</p>
      </div>
      <div v-else-if="status === 'error'" class="text-center py-12 text-red-500">
        <p>Failed to load notes. Please try again later.</p>
      </div>
      <div v-else-if="filteredNotes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <NoteCard
          v-for="note in filteredNotes"
          :key="note.id"
          :note="note"
        />
      </div>
      <div v-else class="text-center py-12">
        <p class="text-xl font-semibold">No notes found</p>
        <p class="text-muted-foreground mt-2">Try adjusting your search or filter criteria.</p>
      </div>
    </main>
  </div>
</template>