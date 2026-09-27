<script setup lang="ts">
import { ref, watch, onMounted } from "vue";

import ChatHeader from "@/components/chat/ChatHeader.vue";
import WelcomeScreen from "@/components/chat/WelcomeScreen.vue";
import MessageList from "@/components/chat/MessageList.vue";
import ChatInput from "@/components/chat/ChatInput.vue";

import { useTypewriter } from "@/composables/useTypewriter";
import { chatsApi } from "@/api/chats";
import { useRoute } from "vue-router";
const route = useRoute();
interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  silent?: boolean; // Optional property to mark silent messages
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
const chatId = ref<string | null>(null);
  
async function sendMessage(content: string) {
  if (isLoading.value || isTyping.value) {
    return;
  }

  if (!chatId.value) {
    console.error("Chat ID is missing");
    return;
  }

  if (!content.trim()) {
    return;
  }

  console.log("Selected category ID:", categoryId.value, content);

  // Сразу показываем сообщение пользователя
  messages.value.push({
    id: Date.now(),
    role: "user",
    content,
  });

  isLoading.value = true;

  const response = await chatsApi.sendMessage(
    chatId.value,
    content,
  );

  messages.value.push({
    id: response.id,
    role: "assistant",
    content: response.content,
  });

  isLoading.value = false;
  isTyping.value = false;

  if (!response) {
    return;
  }

  console.log("Message response:", response);
}

function useSilentPrompt(prompt: string) {
  console.log("d")
  if (!chatId.value) {
    console.error("Chat ID is missing");
    return;
  }
  isLoading.value = true;
  chatsApi.sendMessage(chatId.value, prompt).then((response) => {
    messages.value.push({
      id: response.id,
      role: "assistant",
      content: response.content,
      silent: true, // Mark this message as silent
    });

    isTyping.value = false;
    isLoading.value = false;
  }).catch((error) => {
    console.error("Error sending silent prompt:", error);
  });
}
onMounted(async () => {
  const id = route.params.id;

  if (!id) {
    return;
  }

  chatId.value = id as string;

  const chat = await chatsApi.get(chatId.value);

  if (!chat) {
    return;
  }

  messages.value = await chatsApi.getMessages(chatId.value);

  if (messages.value.length === 1) {
    useSilentPrompt(messages.value[0].content);
  }
  
  document.title = `Chat - ${chat.title}`;
});
</script>

<template>
  <div class="flex h-screen flex-col bg-background">
    <ChatHeader :locale="locale" @update:locale="locale = $event" :show-new-chat-button="true"/>

    <main class="flex min-h-0 flex-1 flex-col">
      <!-- Welcome -->

      <!-- Chat -->
      <div class="flex-1 overflow-y-auto">
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
        :is-first-message="false"
        :locale="locale"
        :is-loading="isLoading || isTyping"
        @send="sendMessage"
        @update:categoryId="categoryId = $event"
        :active-category="categoryId"
      />
    </main>
  </div>
</template>
