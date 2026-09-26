<script setup lang="ts">
import { ref, watch } from "vue"

import ChatHeader from "@/components/chat/ChatHeader.vue"
import WelcomeScreen from "@/components/chat/WelcomeScreen.vue"
import MessageList from "@/components/chat/MessageList.vue"
import ChatInput from "@/components/chat/ChatInput.vue"
import NotFoundComponent from "@/components/NotFoundComponent.vue"
import { useTypewriter } from "@/composables/useTypewriter"

interface Message {
  id: number
  role: "user" | "assistant"
  content: string
}

const locale = ref<"RU" | "RO" | "EN">(localStorage.getItem("locale") as "RU" | "RO" | "EN" || "RU")
watch(locale, (newLocale) => {
  localStorage.setItem("locale", newLocale)
})
const messages = ref<Message[]>([])

const isLoading = ref(false)

const {
  text: typedText,
  isTyping,
  type,
} = useTypewriter(18)

async function sendMessage(content: string) {
  if (isLoading.value || isTyping.value) {
    return
  }

  // User message
  messages.value.push({
    id: Date.now(),
    role: "user",
    content,
  })

  isLoading.value = true

  // TODO:
  // Здесь потом будет настоящий API request
  await new Promise((resolve) => setTimeout(resolve, 1000))

  const response =
    locale.value === "RU"
      ? "Чтобы получить муниципальную услугу, необходимо обратиться в соответствующее учреждение и предоставить необходимые документы."
      : "Pentru a obține serviciul municipal, trebuie să contactați instituția corespunzătoare și să prezentați documentele necesare."

  // Убираем typing indicator
  isLoading.value = false

  // Печатаем ответ
  await type(response)

  // После завершения typewriter сохраняем сообщение
  messages.value.push({
    id: Date.now(),
    role: "assistant",
    content: typedText.value,
  })

  typedText.value = ""
}

function usePrompt(prompt: string) {
  sendMessage(prompt)
}
</script>

<template>
  <div class="flex h-screen flex-col bg-background">
    <ChatHeader
      :locale="locale"
      @update:locale="locale = $event"
    />

    <main class="flex min-h-0 flex-1 flex-col">
      <!-- Welcome -->
     <NotFoundComponent :locale="locale">
    </NotFoundComponent>
    </main>
  </div>
</template>