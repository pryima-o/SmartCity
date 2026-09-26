<script setup lang="ts">
import { ref, watch, nextTick } from "vue"

import MessageBubble from "./MessageBubble.vue"
import TypingIndicator from "./TypingIndicator.vue"

interface Message {
  id: number
  role: "user" | "assistant"
  content: string
}

const props = defineProps<{
  messages: Message[]
  isLoading: boolean
  typedText: string
  isTyping: boolean
}>()

const messagesContainer = ref<HTMLElement | null>(null)

async function scrollToBottom() {
  await nextTick()

  if (!messagesContainer.value) return

  messagesContainer.value.scrollTo({
    top: messagesContainer.value.scrollHeight,
    behavior: "smooth",
  })
}

// Новое сообщение
watch(
  () => props.messages.length,
  scrollToBottom
)

// Появился loading
watch(
  () => props.isLoading,
  scrollToBottom
)

// Печатается новый символ
watch(
  () => props.typedText,
  scrollToBottom
)

// Начался / закончился typewriter
watch(
  () => props.isTyping,
  scrollToBottom
)
</script>

<template>
  <div
    ref="messagesContainer"
    class="h-full overflow-y-auto"
  >
    <div
      class="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-8"
    >
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :role="message.role"
        :content="message.content"
        :sources="message.sources"
      />

      <TypingIndicator v-if="isLoading" />

      <!-- Typewriter -->
      <div
        v-if="isTyping"
        class="flex justify-start"
      >
        <div
          class="max-w-[80%] rounded-2xl bg-muted px-4 py-3 text-sm"
        >
          {{ typedText }}<span class="ml-0.5 animate-pulse">|</span>
        </div>
      </div>
    </div>
  </div>
</template>