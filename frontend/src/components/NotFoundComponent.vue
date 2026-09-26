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
  <div class="flex flex-1 flex-col items-center justify-center px-4 gap-2">
   

    <h1 class="text-4xl font-semibold tracking-tight">
      404
    </h1>

    <p class="max-w-lg text-center text-sm text-muted-foreground mb-4">
      {{
        locale === "RU"
          ? "Данная страница не найдена."
          : locale === "RO"
            ? "Pagina nu a fost găsită."
            : "Page not found."
      }}
    </p>
    <button>
      <router-link
        to="/"
        class="mt-8 rounded-xl border bg-background p-4 text-left text-sm transition hover:bg-muted"
      >
        {{ locale === "RU" ? "Вернуться в чат" : locale === "RO" ? "Înapoi la chat" : "Back to chat" }}
      </router-link>
    </button>

  
  </div>
</template>