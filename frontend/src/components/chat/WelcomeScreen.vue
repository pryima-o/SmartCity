<script setup lang="ts">
defineProps<{
  locale: "RU" | "RO" | "EN"
}>()

const emit = defineEmits<{
  prompt: [value: string]
}>()

const prompts = {
  RU: [
    "Как решить вопрос с городскими услугами?",
    "Какие документы мне понадобятся?",
    "Где найти нужное место в городе?",
  ],
  RO: [
    "Cum pot rezolva o problemă în oraș?",
    "De ce documente am nevoie?",
    "Unde pot găsi locul de care am nevoie?",
  ],
  EN: [
    "How can I solve a city-related issue?",
    "What documents will I need?",
    "Where can I find the place I need?",
  ],
}
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center px-4">

    <h2 class="text-2xl font-semibold tracking-tight">
      {{
        locale === "RU"
          ? "Привет! Чем могу помочь?"
          : locale === "RO"
            ? "Salut! Cu ce te pot ajuta?"
            : "Hi! How can I help?"
      }}
    </h2>

    <p class="mt-2 max-w-lg text-center text-sm text-muted-foreground">
      {{
        locale === "RU"
          ? "Расскажи, что тебе нужно — помогу разобраться с городскими вопросами, найти нужную информацию или подсказать, куда обратиться."
          : locale === "RO"
            ? "Spune-mi de ce ai nevoie — te ajut să găsești informația potrivită, să rezolvi o problemă sau să afli unde trebuie să mergi."
            : "Tell me what you need — I can help you find the right information, solve a city-related issue, or figure out where to go."
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