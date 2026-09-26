<script setup lang="ts">
defineProps<{
  role: "user" | "assistant"
  content: string
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
    </div>
  </div>
</template>