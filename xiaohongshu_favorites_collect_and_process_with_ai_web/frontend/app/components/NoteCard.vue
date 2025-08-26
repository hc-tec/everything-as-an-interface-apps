<script setup lang="ts">
import type { NoteDetailsItem } from '~/types/notes'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '~/components/ui/card'
import { Heart, Star, MessageCircle, Globe2, ExternalLink } from 'lucide-vue-next'

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

function getPlatformLabel(platform: string) {
  if (platform === 'xiaohongshu') return 'XHS'
  if (platform === 'bilibili') return 'Bili'
  if (platform === 'zhihu') return 'Zhihu'
  return 'Other'
}
</script>

<template>
  <Card class="flex flex-col h-full bg-card border-none shadow-lg hover:shadow-2xl transition-all duration-300 ease-in-out transform hover:-translate-y-2 rounded-2xl overflow-hidden group">
    <NuxtLink :to="`/note/${note.id}`" v-if="note.images && note.images.length > 0" class="relative aspect-[16/10] overflow-hidden block">
      <img :src="note.images[0]" :alt="note.title" class="object-cover w-full h-full transition-transform duration-500 group-hover:scale-110" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
      <div class="absolute top-3 right-3 pl-2 pr-2.5 py-1 bg-background/80 text-foreground text-[11px] font-semibold tracking-wide uppercase backdrop-blur-sm rounded-full inline-flex items-center gap-1" :title="getNotePlatform(note)">
        <Globe2 class="w-3.5 h-3.5" />
        <span>{{ getPlatformLabel(getNotePlatform(note)) }}</span>
      </div>
    </NuxtLink>

    <CardHeader class="p-5 flex-grow">
      <NuxtLink :to="`/note/${note.id}`" class="hover:underline">
        <CardTitle class="text-lg font-bold tracking-tight leading-snug">{{ note.title || '未命名' }}</CardTitle>
      </NuxtLink>
      <CardDescription v-if="note.ai_summary && note.ai_summary.summary" class="mt-2 text-sm text-muted-foreground line-clamp-3">
        {{ note.ai_summary.summary }}
      </CardDescription>
      <CardDescription v-else class="mt-2 text-sm text-muted-foreground line-clamp-3">
        {{ note.desc }}
      </CardDescription>
    </CardHeader>

    <CardContent class="p-5 pt-0">
      <div v-if="note.ai_summary && note.ai_summary.keywords && note.ai_summary.keywords.length" class="flex flex-wrap gap-2">
        <span v-for="tag in note.ai_summary.keywords.slice(0, 3)" :key="tag" class="inline-block bg-primary/10 text-primary text-xs font-medium px-3 py-1 rounded-full">
          {{ tag }}
        </span>
      </div>
      <div v-else-if="note.tags && note.tags.length" class="flex flex-wrap gap-2">
        <span v-for="tag in note.tags.slice(0, 3)" :key="tag" class="inline-block bg-muted text-foreground/80 text-xs font-medium px-3 py-1 rounded-full">
          {{ tag }}
        </span>
      </div>
      <!-- AI Topics -->
      <div v-if="note.ai_topics" class="flex flex-wrap gap-2 mt-3">
        <span v-if="note.ai_topics.primary_topic" class="inline-block bg-secondary text-foreground/90 text-xs font-medium px-3 py-1 rounded-full">
          {{ note.ai_topics.primary_topic }}
        </span>
        <span v-for="(sub, idx) in (note.ai_topics.subtopics || []).slice(0, 2)" :key="sub + idx" class="inline-block bg-secondary/70 text-foreground/80 text-xs font-medium px-3 py-1 rounded-full">
          {{ sub }}
        </span>
      </div>
      <!-- AI intent/type badges -->
      <div v-if="note.ai_topics && (note.ai_topics.content_intent || note.ai_topics.content_type)" class="flex flex-wrap gap-2 mt-2">
        <span v-if="note.ai_topics.content_intent" class="inline-block bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[11px] font-medium px-2.5 py-1 rounded-full">
          {{ note.ai_topics.content_intent }}
        </span>
        <span v-if="note.ai_topics.content_type" class="inline-block bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[11px] font-medium px-2.5 py-1 rounded-full">
          {{ note.ai_topics.content_type }}
        </span>
      </div>
    </CardContent>

    <CardFooter class="p-5 flex items-center justify-between text-xs text-muted-foreground bg-muted/50">
      <div class="flex items-center gap-2">
        <img :src="note.author_info.avatar" :alt="note.author_info.username" class="w-7 h-7 rounded-full border-2 border-background">
        <span class="font-medium">{{ note.author_info.username }}</span>
        <a v-if="note.author_info.author_link" :href="note.author_info.author_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-primary hover:underline ml-1">
          <ExternalLink class="w-3.5 h-3.5" />
        </a>
      </div>
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1"><Heart class="w-4 h-4" /> {{ note.statistic.like_num }}</span>
        <span class="flex items-center gap-1"><Star class="w-4 h-4" /> {{ note.statistic.collect_num }}</span>
        <span class="flex items-center gap-1"><MessageCircle class="w-4 h-4" /> {{ note.statistic.chat_num }}</span>
      </div>
    </CardFooter>
  </Card>
</template>