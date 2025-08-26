<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { Input } from '~/components/ui/input'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select'
import { Button } from '~/components/ui/button'

const props = defineProps<{
  topics?: string[]
  valueSearchQuery?: string
  valuePlatform?: string
  valueTopic?: string
  valueSort?: string
}>()

const emit = defineEmits(['update:searchQuery', 'update:platform', 'update:topic', 'update:sort', 'clear'])

const searchQuery = ref('')
const selectedPlatform = ref('all')
const selectedTopic = ref('all')
const selectedSort = ref('date_desc')

// sync from controlled props
watch(() => props.valueSearchQuery, (v) => {
  searchQuery.value = v ?? ''
}, { immediate: true })

watch(() => props.valuePlatform, (v) => {
  selectedPlatform.value = v ?? 'all'
}, { immediate: true })

watch(() => props.valueTopic, (v) => {
  selectedTopic.value = v ?? 'all'
}, { immediate: true })

watch(() => props.valueSort, (v) => {
  selectedSort.value = v ?? 'date_desc'
}, { immediate: true })

const platforms = ['all', 'xiaohongshu', 'bilibili', 'zhihu']

const sortOptions = [
  { value: 'date_desc', label: '按时间(新→旧)' },
  { value: 'date_asc', label: '按时间(旧→新)' },
  { value: 'likes_desc', label: '按点赞(高→低)' },
  { value: 'collects_desc', label: '按收藏(高→低)' },
  { value: 'comments_desc', label: '按评论(高→低)' },
]

const topicOptions = computed(() => {
  const base = props.topics || []
  const uniq = Array.from(new Set(base.filter(Boolean))) as string[]
  return ['all', ...uniq]
})

const emitSearch = useDebounceFn((val: string) => {
  emit('update:searchQuery', val)
}, 250)

watch(searchQuery, (newQuery) => {
  emitSearch(newQuery)
})

watch(selectedPlatform, (newPlatform) => {
  emit('update:platform', newPlatform)
})

watch(selectedTopic, (newTopic) => {
  emit('update:topic', newTopic)
})

watch(selectedSort, (newSort) => {
  emit('update:sort', newSort)
})

function clearAll() {
  searchQuery.value = ''
  selectedPlatform.value = 'all'
  selectedTopic.value = 'all'
  selectedSort.value = 'date_desc'
  emit('clear')
  emit('update:searchQuery', '')
  emit('update:platform', 'all')
  emit('update:topic', 'all')
  emit('update:sort', 'date_desc')
}
</script>

<template>
  <div class="p-4 bg-card border-b">
    <div class="container mx-auto flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
      <div class="relative flex-grow">
        <Input
          v-model="searchQuery"
          placeholder="搜索标题、摘要或标签..."
          class="pl-10 w-full h-10"
        />
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <svg class="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
      </div>
      <Select v-model="selectedPlatform">
        <SelectTrigger class="w-full sm:w-[160px] h-10">
          <SelectValue placeholder="按平台筛选" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="platform in platforms" :key="platform" :value="platform">
              {{ platform === 'all' ? '全部平台' : platform }}
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <Select v-model="selectedTopic">
        <SelectTrigger class="w-full sm:w-[200px] h-10">
          <SelectValue placeholder="按主题筛选" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="topic in topicOptions" :key="topic" :value="topic">
              {{ topic === 'all' ? '全部主题' : topic }}
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <Select v-model="selectedSort">
        <SelectTrigger class="w-full sm:w-[200px] h-10">
          <SelectValue placeholder="排序" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <Button variant="secondary" class="h-10" @click="clearAll">清除筛选</Button>
    </div>
  </div>
</template>