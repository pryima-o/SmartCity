<script setup lang="ts">
import { Button } from "@/components/ui/button"

defineProps<{
  locale: "RU" | "RO"
}>()

const emit = defineEmits<{
  "update:locale": [value: "RU" | "RO"]
}>()

function toggleLocale() {
  emit("update:locale", "RU")
}
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b px-6">
    <div>
      <h1 class="font-semibold">Smart City AI</h1>
      <p class="text-xs text-muted-foreground">
        {{ locale === "RU" ? "Муниципальный помощник" : "Asistent municipal" }}
      </p>
    </div>

    <div class="flex items-center gap-2">
      <Button
        variant="ghost"
        size="sm"
        @click="emit('update:locale', locale === 'RU' ? 'RO' : 'RU')"
      >
        {{ locale === "RU" ? "RU" : "RO" }}
      </Button>

      <Button variant="outline" size="sm">
        {{ locale === "RU" ? "Новый чат" : "Chat nou" }}
      </Button>
    </div>
  </header>
</template>