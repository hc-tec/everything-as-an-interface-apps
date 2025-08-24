<script setup lang="ts">
import { ref, watch } from 'vue'
import { Input } from '~/components/ui/input'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select'

const emit = defineEmits(['update:searchQuery', 'update:platform'])

const searchQuery = ref('')
const selectedPlatform = ref('all')

const platforms = ['all', 'xiaohongshu', 'bilibili', 'zhihu']

watch(searchQuery, (newQuery) => {
  emit('update:searchQuery', newQuery)
})

watch(selectedPlatform, (newPlatform) => {
  emit('update:platform', newPlatform)
})
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
        <SelectTrigger class="w-full sm:w-[180px]">
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
    </div>
  </div>
</template>