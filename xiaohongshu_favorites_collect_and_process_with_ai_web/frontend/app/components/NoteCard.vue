<script setup lang="ts">
import type { NoteDetailsItem } from '~/types/notes'
import { Button } from '~/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '~/components/ui/card'

defineProps<{ note: NoteDetailsItem }>()

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

function getPlatformIcon(platform: string) {
  // This is a placeholder. In a real app, you might have different icons for different platforms.
  if (platform === 'xiaohongshu') return '📕'
  if (platform === 'bilibili') return '📺'
  if (platform === 'zhihu') return '知'
  return '📝'
}
</script>

<template>
  <Card class="flex flex-col h-full transition-all duration-300 ease-in-out transform hover:-translate-y-1 hover:shadow-xl bg-card border rounded-xl overflow-hidden">
    <CardHeader class="p-4">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <CardTitle class="text-lg font-bold tracking-tight">{{ note.title }}</CardTitle>
          <CardDescription class="mt-1 text-sm">{{ note.ai_summary.summary }}</CardDescription>
        </div>
        <div class="text-2xl ml-4" :title="getNotePlatform(note)">{{ getPlatformIcon(getNotePlatform(note)) }}</div>
      </div>
    </CardHeader>
    <CardContent class="p-4 pt-0 flex-grow">
      <div v-if="note.images && note.images.length > 0" class="aspect-video mb-4 rounded-lg overflow-hidden">
        <img :src="note.images[0]" :alt="note.title" class="object-cover w-full h-full">
      </div>
      <div class="flex flex-wrap gap-2">
        <span v-for="tag in note.ai_summary.keywords" :key="tag" class="inline-block bg-muted text-muted-foreground text-xs font-medium px-2.5 py-0.5 rounded-full">
          #{{ tag }}
        </span>
      </div>
    </CardContent>
    <CardFooter class="p-4 flex items-center justify-between text-xs text-muted-foreground border-t">
      <div class="flex items-center space-x-2">
        <img :src="note.author_info.avatar" :alt="note.author_info.username" class="w-6 h-6 rounded-full">
        <span>{{ note.author_info.username }}</span>
      </div>
      <div class="flex items-center space-x-4">
        <span>❤️ {{ note.statistic.like_num }}</span>
        <span>⭐ {{ note.statistic.collect_num }}</span>
        <span>💬 {{ note.statistic.chat_num }}</span>
      </div>
    </CardFooter>
  </Card>
</template>