<script setup lang="ts">
import MessageBubble from "./MessageBubble.vue"
import TypingIndicator from "./TypingIndicator.vue"

interface Message {
  id: number
  role: "user" | "assistant"
  content: string
}

defineProps<{
  messages: Message[]
  isLoading: boolean
}>()
</script>

<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-8">
    <MessageBubble
      v-for="message in messages"
      :key="message.id"
      :role="message.role"
      :content="message.content"
    />

    <TypingIndicator v-if="isLoading" />
  </div>
</template>