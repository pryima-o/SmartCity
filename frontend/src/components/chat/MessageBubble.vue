<script setup lang="ts">
import Badge from '@/components/ui/badge/Badge.vue';
defineProps<{
  role: "user" | "assistant"
  content: string,
  sources: []
}>()
</script>

<template>
  <div
    class="flex"
    :class="role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[80%] rounded-2xl px-4 py-3 text-sm"
      :class="
        role === 'user'
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted'
      "
    >
      {{ content }}

      <div class="flex w-full flex-wrap gap-1 mt-2">
        <a
          v-for="(source, index) in sources"
          :key="index"
          :href="source.url"
          target="_blank"
          class="text-xs text-blue-500 hover:underline"
        >
        <Badge variant="outline" class="text-blue-500 bg-white">
                    {{ source.url }}
        </Badge>
        </a>

      </div>
    </div>
  </div>
</template>