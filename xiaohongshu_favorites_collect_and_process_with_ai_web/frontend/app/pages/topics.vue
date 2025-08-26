<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'

const { data, status, error } = useFetch<{ primary: any[]; subtopics: any[]; intents: any[]; types: any[] }>("/api/topics")

function gotoTopic(topic: string) {
  navigateTo({ path: '/', query: { topic } })
}
</script>

<template>
  <div class="container mx-auto p-4 sm:p-6 lg:p-8">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold tracking-tight">主题中心</h1>
      <NuxtLink to="/">
        <Button variant="ghost">返回首页</Button>
      </NuxtLink>
    </div>

    <div v-if="status === 'pending'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      <div v-for="i in 4" :key="i" class="h-48 bg-muted animate-pulse rounded-xl"></div>
    </div>
    <div v-else-if="status === 'error'" class="text-center py-20">
      <p class="text-2xl font-semibold text-destructive">加载失败</p>
      <p class="text-muted-foreground mt-2">{{ (error as any)?.message || '无法获取主题数据' }}</p>
    </div>

    <div v-else-if="data" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>主主题</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-wrap gap-2">
          <Button v-for="t in data.primary" :key="t.name" size="sm" variant="secondary" @click="gotoTopic(t.name)">
            {{ t.name }}
            <Badge class="ml-2">{{ t.count }}</Badge>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>子主题</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-wrap gap-2">
          <Button v-for="t in data.subtopics" :key="t.name" size="sm" variant="secondary" @click="gotoTopic(t.name)">
            {{ t.name }}
            <Badge class="ml-2">{{ t.count }}</Badge>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>意图</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-wrap gap-2">
          <Button v-for="t in data.intents" :key="t.name" size="sm" variant="secondary" @click="gotoTopic(t.name)">
            {{ t.name }}
            <Badge class="ml-2">{{ t.count }}</Badge>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>内容类型</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-wrap gap-2">
          <Button v-for="t in data.types" :key="t.name" size="sm" variant="secondary" @click="gotoTopic(t.name)">
            {{ t.name }}
            <Badge class="ml-2">{{ t.count }}</Badge>
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>