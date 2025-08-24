<template>
  <div class="min-h-dvh bg-background text-foreground">
    <header class="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="container mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="font-semibold">AI Notes</span>
          <span class="text-sm text-muted-foreground hidden sm:inline">收藏与搜索</span>
        </div>
      </div>
    </header>

    <main>
      <slot />
    </main>

    <footer class="border-t mt-12 py-6 text-center text-sm text-muted-foreground">
      © 2025
    </footer>
  </div>
</template>