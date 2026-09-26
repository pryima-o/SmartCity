<script setup lang="ts">
import { ref } from "vue"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

defineProps<{
  isLoading: boolean
  locale: "RU" | "RO"
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const input = ref("")

function send() {
  const value = input.value.trim()

  if (!value) return

  emit("send", value)
  input.value = ""
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}
</script>

<template>
  <footer class="border-t bg-background p-4">
    <div class="mx-auto max-w-3xl">
      <div class="relative">
        <Textarea
          v-model="input"
          :placeholder="
            locale === 'RU'
              ? 'Напишите свой вопрос...'
              : 'Scrie întrebarea ta...'
          "
          class="min-h-[56px] resize-none pr-20"
          @keydown="handleKeydown"
        />

        <Button
          class="absolute bottom-2 right-2"
          size="sm"
          :disabled="!input.trim() || isLoading"
          @click="send"
        >
          {{ locale === "RU" ? "Отправить" : "Trimite" }}
        </Button>
      </div>

      <p class="mt-2 text-center text-xs text-muted-foreground">
        {{
          locale === "RU"
            ? "AI может допускать ошибки. Проверяйте важную информацию."
            : "AI poate face greșeli. Verifică informațiile importante."
        }}
      </p>
    </div>
  </footer>
</template>