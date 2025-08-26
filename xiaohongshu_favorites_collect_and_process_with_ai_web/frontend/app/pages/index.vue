<script setup lang="ts">
import { ref, computed } from 'vue'
import type { NoteDetailsItem } from '~/types/notes'
import { useNotes } from '~/composables/useNotes'
import NoteCard from '~/components/NoteCard.vue'
import SearchFilter from '~/components/SearchFilter.vue'

const { notes, status } = useNotes()

const searchQuery = ref('')
const selectedPlatform = ref('all')
const selectedTopic = ref('all')
const selectedSort = ref('date_desc')

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

const allTopics = computed(() => {
  const list = notes.value || []
  const pool: string[] = []
  for (const n of list) {
    const t = n.ai_topics
    if (!t) continue
    if (t.primary_topic) pool.push(t.primary_topic)
    if (Array.isArray(t.subtopics)) pool.push(...t.subtopics)
    if (t.content_intent) pool.push(t.content_intent)
    if (t.content_type) pool.push(t.content_type)
  }
  return pool
})

function toNum(v: unknown): number {
  if (typeof v === 'number') return v
  if (typeof v === 'string') {
    const n = Number(v.replace?.(/[,\s]/g, '') ?? v)
    return isNaN(n) ? 0 : n
  }
  return 0
}

const filteredNotes = computed(() => {
  let result = notes.value || []

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(note =>
      (note.title || '').toLowerCase().includes(q) ||
      (note.ai_summary?.summary || '').toLowerCase().includes(q) ||
      (note.ai_summary?.keywords || []).some(tag => tag.toLowerCase().includes(q)) ||
      (note.tags || []).some(tag => tag.toLowerCase().includes(q)) ||
      (note.desc || '').toLowerCase().includes(q)
    )
  }

  if (selectedPlatform.value !== 'all') {
    result = result.filter(note => getNotePlatform(note) === selectedPlatform.value)
  }

  if (selectedTopic.value !== 'all') {
    const t = selectedTopic.value.toLowerCase()
    result = result.filter(n => {
      const at = n.ai_topics
      if (!at) return false
      const hay = [
        at.primary_topic,
        ...(Array.isArray(at.subtopics) ? at.subtopics : []),
        at.content_intent,
        at.content_type,
      ]
        .filter(Boolean)
        .map(s => (s as string).toLowerCase())
      return hay.includes(t)
    })
  }

  // sorting
  const sortKey = selectedSort.value
  result = [...result].sort((a, b) => {
    if (sortKey === 'date_desc') return toNum(b.date) - toNum(a.date)
    if (sortKey === 'date_asc') return toNum(a.date) - toNum(b.date)
    if (sortKey === 'likes_desc') return toNum(b.statistic?.like_num) - toNum(a.statistic?.like_num)
    if (sortKey === 'collects_desc') return toNum(b.statistic?.collect_num) - toNum(a.statistic?.collect_num)
    if (sortKey === 'comments_desc') return toNum(b.statistic?.chat_num) - toNum(a.statistic?.chat_num)
    return 0
  })

  return result
})

const route = useRoute()
const router = useRouter()

watch(() => route.query.topic, (val) => {
  if (typeof val === 'string' && val) {
    selectedTopic.value = val
  } else if (!val) {
    selectedTopic.value = 'all'
  }
}, { immediate: true })

watch(() => route.query.q, (val) => {
  if (typeof val === 'string') searchQuery.value = val
}, { immediate: true })

watch(() => route.query.platform, (val) => {
  if (typeof val === 'string') selectedPlatform.value = val
}, { immediate: true })

watch(() => route.query.sort, (val) => {
  if (typeof val === 'string') selectedSort.value = val
}, { immediate: true })

function updateSearchQuery(query: string) {
  searchQuery.value = query
  router.replace({ query: { ...route.query, q: query || undefined } })
}

function updatePlatform(platform: string) {
  selectedPlatform.value = platform
  router.replace({ query: { ...route.query, platform: platform === 'all' ? undefined : platform } })
}

function updateTopic(topic: string) {
  selectedTopic.value = topic
  router.replace({ query: { ...route.query, topic: topic === 'all' ? undefined : topic } })
}

function updateSort(sortVal: string) {
  selectedSort.value = sortVal
  router.replace({ query: { ...route.query, sort: sortVal === 'date_desc' ? undefined : sortVal } })
}

function clearFilters() {
  searchQuery.value = ''
  selectedPlatform.value = 'all'
  selectedTopic.value = 'all'
  selectedSort.value = 'date_desc'
  router.replace({ query: {} })
}

</script>

<template>
  <div class="bg-background text-foreground min-h-screen">
    <header class="sticky top-0 z-10 backdrop-blur-md bg-background/80 border-b">
      <div class="container mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col sm:flex-row items-center justify-between py-4 gap-4">
          <div class="text-center sm:text-left">
            <h1 class="text-2xl font-bold tracking-tighter">Knowledge Hub</h1>
            <p class="text-muted-foreground text-sm mt-1">Your curated collection of insights.</p>
            <NuxtLink to="/topics" class="inline-block mt-2 text-sm text-primary hover:underline">浏览全部主题 →</NuxtLink>
          </div>
          <SearchFilter
            :topics="allTopics"
            :value-search-query="searchQuery"
            :value-platform="selectedPlatform"
            :value-topic="selectedTopic"
            :value-sort="selectedSort"
            @update:searchQuery="updateSearchQuery"
            @update:platform="updatePlatform"
            @update:topic="updateTopic"
            @update:sort="updateSort"
            @clear="clearFilters"
            class="w-full sm:w-auto"
          />
        </div>
      </div>
    </header>

    <main class="container mx-auto p-4 sm:p-6 lg:p-8">
      <div v-if="status === 'pending'" class="flex flex-col items-center justify-center py-20">
        <svg class="animate-spin h-10 w-10 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="mt-4 text-lg font-medium text-muted-foreground">Loading your knowledge base...</p>
      </div>
      <div v-else-if="status === 'error'" class="text-center py-20">
        <p class="text-2xl font-semibold text-destructive">Oops! Something went wrong.</p>
        <p class="text-muted-foreground mt-2">We couldn't load your notes. Please check your connection or try again later.</p>
      </div>
      <div v-else-if="filteredNotes.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        <NoteCard
          v-for="note in filteredNotes"
          :key="note.id"
          :note="note"
        />
      </div>
      <div v-else class="text-center py-20">
        <div class="mx-auto bg-secondary rounded-full h-24 w-24 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 10.5a.5.5 0 01.5-.5h3a.5.5 0 010 1h-3a.5.5 0 01-.5-.5z" />
          </svg>
        </div>
        <h2 class="mt-6 text-2xl font-bold tracking-tight">No results found.</h2>
        <p class="mt-2 text-muted-foreground">Try a different search query or adjust your filters.</p>
      </div>
    </main>
  </div>
</template>