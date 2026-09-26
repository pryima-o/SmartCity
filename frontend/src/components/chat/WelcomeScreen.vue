<script setup lang="ts">
defineProps<{
  locale: "RU" | "RO"
}>()

const emit = defineEmits<{
  prompt: [value: string]
}>()

const prompts = {
  RU: [
    "Как получить муниципальную услугу?",
    "Какие документы мне нужны?",
    "Где находится ближайший муниципальный центр?",
  ],
  RO: [
    "Cum pot obține un serviciu municipal?",
    "De ce documente am nevoie?",
    "Unde este cel mai apropiat centru municipal?",
  ],
}
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center px-4">
   

    <h2 class="text-2xl font-semibold tracking-tight">
      {{
        locale === "RU"
          ? "Привет! Я муниципальный помощник"
          : "Salut! Sunt asistentul tău municipal"
      }}
    </h2>

    <p class="mt-2 max-w-lg text-center text-sm text-muted-foreground">
      {{
        locale === "RU"
          ? "Я помогу найти информацию о муниципальных услугах, документах, правилах и других городских вопросах."
          : "Te pot ajuta să găsești informații despre servicii municipale, documente, reguli și alte întrebări despre oraș."
      }}
    </p>

    <div class="mt-8 grid w-full max-w-2xl gap-2 sm:grid-cols-3">
      <button
        v-for="prompt in prompts[locale]"
        :key="prompt"
        class="rounded-xl border bg-background p-4 text-left text-sm transition hover:bg-muted"
        @click="emit('prompt', prompt)"
      >
        {{ prompt }}
      </button>
    </div>
  </div>
</template>