<script setup lang="ts">
import { ref, computed } from 'vue'
import type { NoteDetailsItem } from '~/types/notes'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Heart, Star, MessageCircle, ArrowLeft, ExternalLink, Globe2 } from 'lucide-vue-next'

const route = useRoute()
const id = computed(() => route.params.id as string)

const { data, status, error } = useFetch<NoteDetailsItem>(() => `/api/notes/${id.value}`, {
  key: () => `note-${id.value}`
})

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
  <div class="container mx-auto p-4 sm:p-6 lg:p-8">
    <!-- Loading state -->
    <div v-if="status === 'pending'" class="space-y-4">
      <div class="h-8 w-40 bg-muted animate-pulse rounded"></div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <div class="aspect-[16/10] w-full bg-muted animate-pulse rounded-xl"></div>
          <div class="mt-4 space-y-3">
            <div class="h-6 bg-muted animate-pulse rounded"></div>
            <div class="h-4 bg-muted animate-pulse rounded w-3/4"></div>
            <div class="h-4 bg-muted animate-pulse rounded w-2/3"></div>
          </div>
        </div>
        <div class="space-y-3">
          <div class="h-24 bg-muted animate-pulse rounded"></div>
          <div class="h-24 bg-muted animate-pulse rounded"></div>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="status === 'error'" class="text-center py-20">
      <p class="text-2xl font-semibold text-red-500">加载失败</p>
      <p class="mt-2 text-muted-foreground">{{ (error as any)?.statusMessage || (error as any)?.message || '发生未知错误' }}</p>
      <NuxtLink to="/" class="inline-block mt-4">
        <Button variant="outline">返回首页</Button>
      </NuxtLink>
    </div>

    <!-- Data found -->
    <div class="mb-4 flex items-center gap-2">
      <NuxtLink to="/">
        <Button variant="ghost" class="inline-flex items-center gap-2">
          <ArrowLeft class="w-4 h-4" /> 返回
        </Button>
      </NuxtLink>
    </div>

    <div v-if="data" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <Card class="border-none shadow-lg rounded-2xl overflow-hidden">
          <div v-if="data.images && data.images.length" class="relative">
            <img :src="data.images[0]" :alt="data.title" class="w-full object-cover max-h-[420px]" />
            <div class="absolute top-3 right-3 pl-2 pr-2.5 py-1 bg-background/80 text-foreground text-[11px] font-semibold tracking-wide uppercase backdrop-blur-sm rounded-full inline-flex items-center gap-1" :title="getNotePlatform(data)">
              <Globe2 class="w-3.5 h-3.5" />
              <span>{{ getPlatformLabel(getNotePlatform(data)) }}</span>
            </div>
          </div>
          <CardHeader>
            <CardTitle class="text-xl font-bold">{{ data.title || '未命名' }}</CardTitle>
            <CardDescription class="mt-2 whitespace-pre-line">{{ data.ai_summary?.summary || data.desc }}</CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="data.ai_summary?.keywords?.length" class="flex flex-wrap gap-2 mb-3">
              <Badge v-for="k in data.ai_summary.keywords" :key="k" variant="secondary">{{ k }}</Badge>
            </div>
            <div v-if="data.ai_topics" class="flex flex-wrap gap-2 mb-3">
              <Badge v-if="data.ai_topics.primary_topic" variant="outline">{{ data.ai_topics.primary_topic }}</Badge>
              <Badge v-for="(sub, idx) in (data.ai_topics.subtopics || [])" :key="sub + idx" variant="outline">{{ sub }}</Badge>
            </div>
            <div v-if="data.ai_topics && (data.ai_topics.content_intent || data.ai_topics.content_type)" class="flex flex-wrap gap-2">
              <Badge v-if="data.ai_topics.content_intent" class="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">{{ data.ai_topics.content_intent }}</Badge>
              <Badge v-if="data.ai_topics.content_type" class="bg-amber-500/10 text-amber-600 dark:text-amber-400">{{ data.ai_topics.content_type }}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <div class="lg:col-span-1">
        <Card class="border-none shadow-lg rounded-2xl">
          <CardHeader>
            <CardTitle class="text-base">作者 & 互动</CardTitle>
            <CardDescription>来源、作者信息与互动统计</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="flex items-center gap-3 mb-4">
              <img :src="data.author_info.avatar" :alt="data.author_info.username" class="w-10 h-10 rounded-full border" />
              <div class="flex flex-col">
                <div class="flex items-center gap-1">
                  <span class="font-medium">{{ data.author_info.username }}</span>
                  <a v-if="data.author_info.author_link" :href="data.author_info.author_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-primary hover:underline">
                    <ExternalLink class="w-3.5 h-3.5" />
                  </a>
                </div>
                <span v-if="data.ip_zh" class="text-xs text-muted-foreground">IP 属地：{{ data.ip_zh }}</span>
              </div>
            </div>
            <div class="grid grid-cols-3 gap-3 text-sm">
              <div class="flex items-center gap-1"><Heart class="w-4 h-4" /> {{ data.statistic.like_num }}</div>
              <div class="flex items-center gap-1"><Star class="w-4 h-4" /> {{ data.statistic.collect_num }}</div>
              <div class="flex items-center gap-1"><MessageCircle class="w-4 h-4" /> {{ data.statistic.chat_num }}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Not found -->
    <div v-else class="text-center py-20">
      <p class="text-2xl font-semibold text-muted-foreground">未找到该笔记</p>
      <NuxtLink to="/" class="inline-block mt-4">
        <Button>返回首页</Button>
      </NuxtLink>
    </div>
  </div>
</template>