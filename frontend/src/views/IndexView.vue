<script setup lang="ts">
import { ref, watch } from "vue";

import ChatHeader from "@/components/chat/ChatHeader.vue";
import WelcomeScreen from "@/components/chat/WelcomeScreen.vue";
import MessageList from "@/components/chat/MessageList.vue";
import ChatInput from "@/components/chat/ChatInput.vue";

import { useTypewriter } from "@/composables/useTypewriter";
import { chatsApi } from "@/api/chats";
interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
}

const locale = ref<"RU" | "RO" | "EN">(
  (localStorage.getItem("locale") as "RU" | "RO" | "EN") || "RU",
);
watch(locale, (newLocale) => {
  localStorage.setItem("locale", newLocale);
});
const messages = ref<Message[]>([]);

const isLoading = ref(false);
const categoryId = ref(null);
const { text: typedText, isTyping, type } = useTypewriter(18);

async function sendMessage(content: string) {
  if (isLoading.value || isTyping.value) {
    return;
  }

  console.log("Selected category ID:", categoryId.value, content);

  // User message
  messages.value.push({
    id: Date.now(),
    role: "user",
    content,
  });

  isLoading.value = true;

  chatsApi
    .create(content, categoryId.value)
    .then(async (response) => {
      const answer = response;

    
      isLoading.value = false;

      console.log(answer);

      window.location.href = `/c/${answer.id}`;
 
    })
    .catch((error) => {
      console.error("Error sending message:", error);
      isLoading.value = false;
    });

  //   // TODO:
  //   // Здесь потом будет настоящий API request
  //   await new Promise((resolve) => setTimeout(resolve, 1000))

  //   const response =
  //     locale.value === "RU"
  //       ? "Чтобы получить муниципальную услугу, необходимо обратиться в соответствующее учреждение и предоставить необходимые документы."
  //       : "Pentru a obține serviciul municipal, trebuie să contactați instituția corespunzătoare și să prezentați documentele necesare."

  //   // Убираем typing indicator
  //   isLoading.value = false

  //   // Печатаем ответ
  //   await type(response)

  //   // После завершения typewriter сохраняем сообщение
  //   messages.value.push({
  //     id: Date.now(),
  //     role: "assistant",
  //     content: typedText.value,
  // sources: [
  //     {
  //         url: 'https://chisinau.md',
  //     }
  // ]
  //   })

  //   typedText.value = ""
}

function usePrompt(prompt: string) {
  sendMessage(prompt);
}
</script>

<template>
  <div class="flex h-screen flex-col bg-background">
    <ChatHeader :locale="locale" @update:locale="locale = $event" />

    <main class="flex min-h-0 flex-1 flex-col">
      <!-- Welcome -->
      <WelcomeScreen
        v-if="messages.length === 0"
        :locale="locale"
        @prompt="usePrompt"
      />

      <!-- Chat -->
      <div v-else class="flex-1 overflow-y-auto">
        <MessageList
          :messages="messages"
          :is-loading="isLoading"
          :typed-text="typedText"
          :is-typing="isTyping"
        />
        <!-- Typewriter -->
        <div v-if="isTyping" class="mx-auto flex w-full max-w-3xl px-4 pb-8">
          <div class="max-w-[80%] rounded-2xl bg-muted px-4 py-3 text-sm">
            {{ typedText }}
            <span class="ml-0.5 animate-pulse">|</span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <ChatInput
        :is-first-message="true"
        :locale="locale"
        :is-loading="isLoading || isTyping"
        @send="sendMessage"
        @update:categoryId="categoryId = $event"
        :active-category="categoryId"
      />
    </main>
  </div>
</template>
